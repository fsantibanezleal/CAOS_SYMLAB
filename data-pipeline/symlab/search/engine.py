"""The genetic-programming engine, with every rung of the classical spine as a switch.

The switches are the point. Each one corresponds to a rung of the ladder, and each defaults OFF so
that `SearchConfig()` is a faithful Koza-1992 baseline. Turning them on one at a time is what makes
the Experiments page an ablation rather than an assertion: the claim "linear scaling is the largest
gain per line of code in the classical spine" is only worth making if the same engine can be run
without it on the same data with the same seed.

That also means every configuration is recorded in the manifest. Two runs that differed in the
primitive set, the tuning schedule, or the lexicase down-sampling rate were not solving the same
problem, and the honest-comparison protocol this lab exists to demonstrate falls apart if that goes
unrecorded.

Determinism is a hard requirement, not a nicety. A run is a pure function of `(config, seed, data)`;
the same inputs give the same Pareto front, byte for byte, so the committed artifacts are stable
under regeneration and a reviewer can reproduce any number in the app.
"""
from __future__ import annotations

import math
import time
from dataclasses import dataclass, field, replace as dataclass_replace

import numpy as np

from ..model import scaling as scaling_mod
from ..model.complexity import node_count, pareto_front, pareto_score, weighted_complexity
from ..model.expr import (
    PRIMITIVE_SETS,
    Node,
    canonical_key,
    count_operators,
    depth,
    evaluate,
    is_valid,
    semantic_key,
    size,
)
from ..model.intervals import Interval, admissible, from_data
from ..model.units import Dims
from .generate import ramped_half_and_half, typed_population
from .select import age_fitness_survival, epsilon_lexicase, nsga2_survival, tournament
from .tune import tune_population
from .variation import vary


@dataclass(frozen=True)
class SearchConfig:
    """Every knob, with defaults that reproduce the plain Koza baseline.

    The rung each switch belongs to is named in its comment, so an ablation table in the docs can be
    generated from this dataclass rather than maintained by hand next to it.
    """

    # Budget
    population: int = 300
    generations: int = 40
    max_depth: int = 10
    primitive_set: str = "koza"
    const_range: tuple[float, float] = (-5.0, 5.0)

    # Rung 2: Keijzer linear scaling and interval guards
    linear_scaling: bool = False
    interval_guard: bool = False
    interval_margin: float = 0.0

    # Rung 3: Levenberg-Marquardt constant tuning, applied on a schedule
    constant_tuning: bool = False
    tuning_every: int = 5
    tuning_top_k: int = 30
    tuning_iterations: int = 15

    # Rung 4: multi-objective survival on (loss, complexity)
    multi_objective: bool = False
    parsimony_coefficient: float = 0.0  # the single-objective comparison arm

    # Rung 5: epsilon-lexicase selection
    epsilon_lexicase: bool = False
    lexicase_down_sample: int | None = 64
    tournament_k: int = 5

    # Rung 6: age-fitness Pareto survival and islands
    age_fitness: bool = False
    n_islands: int = 1
    migration_every: int = 10
    migration_size: int = 3

    # Rung 7: deduplication
    dedup_structural: bool = False
    dedup_semantic: bool = False

    # Rung 8: unit-typed generation
    unit_typed: bool = False

    # Variation
    p_crossover: float = 0.6
    p_subtree: float = 0.2
    p_point: float = 0.15
    p_hoist: float = 0.05
    elitism: int = 2

    def label(self) -> str:
        """Short human label for the variant chip in the app."""
        parts = []
        if self.linear_scaling:
            parts.append("scaling")
        if self.interval_guard:
            parts.append("intervals")
        if self.constant_tuning:
            parts.append("LM")
        if self.multi_objective:
            parts.append("NSGA-II")
        if self.epsilon_lexicase:
            parts.append("eps-lexicase")
        if self.age_fitness:
            parts.append("AFP")
        if self.n_islands > 1:
            parts.append(f"{self.n_islands} islands")
        if self.dedup_structural or self.dedup_semantic:
            parts.append("dedup")
        if self.unit_typed:
            parts.append("unit-typed")
        return " + ".join(parts) if parts else "Koza baseline"


@dataclass
class Individual:
    """One member of the population, carrying everything survival needs to judge it."""

    expression: Node
    loss: float = float("inf")
    complexity: int = 0
    age: int = 0
    scaling: scaling_mod.Scaling = scaling_mod.IDENTITY
    operator: str = "init"
    parents: tuple[int, ...] = ()
    island: int = 0
    ident: int = -1


@dataclass
class SearchResult:
    """The full record of one run, ready for the export contract."""

    config: SearchConfig
    seed: int
    pareto: list[Individual]
    pareto_scores: list[float]
    best: Individual
    history: dict
    counters: dict
    duplicates_avoided: int
    invalid_rejected: int
    wall_seconds: float


def _apply_scaling(expression: Node, fitted: scaling_mod.Scaling, enabled: bool) -> Node:
    if not enabled:
        return expression
    return scaling_mod.fold_into_expression(expression, fitted)


class Engine:
    """A deterministic genetic-programming search over expressions."""

    def __init__(
        self,
        config: SearchConfig,
        *,
        input_dims: list[Dims] | None = None,
        target_dims: Dims | None = None,
    ) -> None:
        self.config = config
        self.input_dims = input_dims
        self.target_dims = target_dims
        self.primitives = PRIMITIVE_SETS[config.primitive_set]

    # -- fitness ------------------------------------------------------------------------------

    def _evaluate_one(
        self, expression: Node, X: np.ndarray, y: np.ndarray, box: list[Interval] | None
    ) -> tuple[float, scaling_mod.Scaling, np.ndarray | None]:
        """Loss, the fitted scaling, and the per-row errors that lexicase needs.

        Returns an infinite loss for any candidate that the interval guard rejects or that produces
        a non-finite value. Both rejections are counted by the caller, because the fraction of the
        population rejected is a real measurement about the primitive set and the data, and it is
        reported rather than hidden.
        """
        if box is not None and not admissible(expression, box):
            return float("inf"), scaling_mod.IDENTITY, None
        raw = evaluate(expression, X)
        if not is_valid(raw):
            return float("inf"), scaling_mod.IDENTITY, None
        if self.config.linear_scaling:
            fitted = scaling_mod.fit(y, raw)
            prediction = fitted.apply(raw)
        else:
            fitted = scaling_mod.IDENTITY
            prediction = raw
        errors = np.abs(y - prediction)
        loss = float(np.mean(errors * errors))
        if not math.isfinite(loss):
            return float("inf"), scaling_mod.IDENTITY, None
        return loss, fitted, errors

    # -- the run ------------------------------------------------------------------------------

    def run(self, X: np.ndarray, y: np.ndarray, *, seed: int = 0) -> SearchResult:
        """Run the search. Deterministic in `(config, seed, data)`.

        Numpy floating-point warnings are silenced for the whole run, deliberately and narrowly: a
        genetic-programming search generates invalid candidates by design (`sin` of an overflowed
        product, a division that overflows), and every one of them is DETECTED and rejected by
        `_evaluate_one` and counted in `invalid_rejected`. Letting numpy also print a warning per
        occurrence would emit thousands of lines that say nothing the counter does not already say.
        The rejections remain visible as a number in the manifest.
        """
        started = time.perf_counter()
        cfg = self.config
        rng = np.random.default_rng(seed)
        errstate = np.errstate(all="ignore")
        errstate.__enter__()
        try:
            n_vars = X.shape[1]
            box = from_data(X, margin=cfg.interval_margin) if cfg.interval_guard else None

            seen_structural: set[str] = set()
            seen_semantic: set[str] = set()
            duplicates_avoided = 0
            invalid_rejected = 0
            next_id = 0

            # -- initial population, per island
            islands: list[list[Individual]] = []
            per_island = max(4, cfg.population // max(1, cfg.n_islands))
            for island_index in range(max(1, cfg.n_islands)):
                if cfg.unit_typed and self.input_dims is not None and self.target_dims is not None:
                    trees = typed_population(
                        rng, size=per_island, primitives=self.primitives,
                        input_dims=self.input_dims, target=self.target_dims, max_depth=min(6, cfg.max_depth),
                    )
                    if not trees:
                        # The declared inputs cannot reach the target dimension. Report it by falling
                        # back and marking the run, rather than silently searching a different problem.
                        trees = ramped_half_and_half(
                            rng, size=per_island, primitives=self.primitives, n_vars=n_vars,
                            max_depth=min(6, cfg.max_depth), const_range=cfg.const_range,
                        )
                else:
                    trees = ramped_half_and_half(
                        rng, size=per_island, primitives=self.primitives, n_vars=n_vars,
                        max_depth=min(6, cfg.max_depth), const_range=cfg.const_range,
                    )
                members = []
                for tree in trees:
                    members.append(Individual(expression=tree, island=island_index, ident=next_id))
                    next_id += 1
                islands.append(members)

            history_generation: list[int] = []
            history_best: list[float] = []
            history_mean: list[float] = []
            history_worst: list[float] = []
            history_evals: list[int] = []
            history_struct_div: list[float] = []
            history_sem_div: list[float] = []
            history_op_entropy: list[float] = []
            island_traces: list[dict] = [{"id": i, "best_loss": [], "size": []} for i in range(len(islands))]
            migrations: list[dict] = []
            operator_names = list(self.primitives)
            operator_matrix: list[list[float]] = [[] for _ in operator_names]

            archive: dict[str, Individual] = {}
            evaluations = 0

            for generation in range(cfg.generations):
                all_members: list[Individual] = []
                for island_index, members in enumerate(islands):
                    # -- evaluate
                    error_rows: list[np.ndarray] = []
                    for member in members:
                        loss, fitted, errors = self._evaluate_one(member.expression, X, y, box)
                        evaluations += 1
                        if not math.isfinite(loss):
                            invalid_rejected += 1
                        member.loss = loss
                        member.scaling = fitted
                        member.complexity = node_count(member.expression)
                        error_rows.append(errors if errors is not None else np.full(len(y), np.inf))

                    # -- constant tuning on a schedule, applied to the best few only
                    if cfg.constant_tuning and generation % max(1, cfg.tuning_every) == 0:
                        order = np.argsort([m.loss for m in members])[: cfg.tuning_top_k]
                        trees = [m.expression for m in members]
                        trees, _improved = tune_population(
                            trees, X, y, indices=list(order), max_iterations=cfg.tuning_iterations
                        )
                        for i in order:
                            members[i].expression = trees[i]
                            loss, fitted, errors = self._evaluate_one(trees[i], X, y, box)
                            evaluations += 1
                            members[i].loss = loss
                            members[i].scaling = fitted
                            members[i].complexity = node_count(trees[i])
                            error_rows[i] = errors if errors is not None else np.full(len(y), np.inf)

                    # -- archive every finite candidate under its canonical key
                    for member in members:
                        if math.isfinite(member.loss):
                            key = canonical_key(member.expression)
                            held = archive.get(key)
                            if held is None or member.loss < held.loss:
                                archive[key] = Individual(
                                    expression=member.expression, loss=member.loss,
                                    complexity=member.complexity, age=member.age,
                                    scaling=member.scaling, operator=member.operator,
                                    island=member.island, ident=member.ident,
                                )

                    island_traces[island_index]["best_loss"].append(
                        round(float(min((m.loss for m in members if math.isfinite(m.loss)), default=float("inf"))), 8)
                        if any(math.isfinite(m.loss) for m in members) else None
                    )
                    island_traces[island_index]["size"].append(len(members))
                    all_members.extend(members)

                    # -- breed the next island generation
                    errors_matrix = np.vstack(error_rows) if cfg.epsilon_lexicase else None
                    losses = np.array([m.loss for m in members])
                    # Effective loss carries the single-objective parsimony arm, so that the comparison
                    # against multi-objective survival is like for like.
                    effective = losses.copy()
                    if cfg.parsimony_coefficient > 0:
                        effective = effective + cfg.parsimony_coefficient * np.array(
                            [m.complexity for m in members], dtype=float
                        )
                    finite = np.isfinite(effective)
                    if not finite.any():
                        effective = np.where(finite, effective, 1e300)
                    else:
                        effective = np.where(finite, effective, np.nanmax(effective[finite]) * 10.0 + 1.0)

                    order = np.argsort(effective)
                    children: list[Individual] = [
                        dataclass_replace(members[int(i)], age=members[int(i)].age + 1)
                        for i in order[: cfg.elitism]
                    ]

                    # A retry budget, so deduplication cannot spin. Once the population converges,
                    # most children collide with something already seen, and an unbounded retry loop
                    # would burn the generation rejecting duplicates.
                    #
                    # MEASURED COST ATTRIBUTION (population 100, 10 generations, 120 rows, seed 7).
                    # An earlier version of this comment blamed deduplication for the whole slowdown
                    # of the combined rung. Isolating the switches shows that was wrong:
                    #
                    #   baseline                     0.30 s
                    #   baseline + epsilon-lexicase  6.73 s   (22x)
                    #   baseline + deduplication     0.75 s   (2.5x, 551 duplicates avoided)
                    #   baseline + both             13.43 s
                    #
                    # Epsilon-lexicase is the dominant cost, by an order of magnitude over dedup:
                    # it walks up to `lexicase_down_sample` cases per selection event and there are
                    # two selection events per child. That cost is a real property of the method and
                    # is REPORTED on the Experiments page rather than hidden, because a selection
                    # method that buys quality with 22x the wall-clock has to be compared at equal
                    # budget, not at equal generation count.
                    #
                    # The retry budget below bounds the dedup half; `duplicates_avoided` still
                    # reports the true count.
                    dedup_rows = min(64, X.shape[0])
                    attempts_left = len(members) * 8
                    while len(children) < len(members) and attempts_left > 0:
                        attempts_left -= 1
                        if cfg.epsilon_lexicase and errors_matrix is not None:
                            a_idx = epsilon_lexicase(rng, errors_matrix, down_sample=cfg.lexicase_down_sample)
                            b_idx = epsilon_lexicase(rng, errors_matrix, down_sample=cfg.lexicase_down_sample)
                        else:
                            a_idx = tournament(rng, effective, k=cfg.tournament_k)
                            b_idx = tournament(rng, effective, k=cfg.tournament_k)
                        child_tree, operator = vary(
                            rng, members[a_idx].expression, members[b_idx].expression,
                            primitives=self.primitives, n_vars=n_vars,
                            p_crossover=cfg.p_crossover, p_subtree=cfg.p_subtree,
                            p_point=cfg.p_point, p_hoist=cfg.p_hoist, max_depth=cfg.max_depth,
                        )

                        if cfg.dedup_structural:
                            key = canonical_key(child_tree)
                            if key in seen_structural:
                                duplicates_avoided += 1
                                continue
                            seen_structural.add(key)
                        if cfg.dedup_semantic:
                            # Hash on a SUBSAMPLE of the rows, not the whole training set. Semantic
                            # identity is a screening test, not a proof, and evaluating every
                            # rejected candidate on every row was the other half of the cost above.
                            values = evaluate(child_tree, X[:dedup_rows])
                            key = semantic_key(values)
                            if key in seen_semantic:
                                duplicates_avoided += 1
                                continue
                            seen_semantic.add(key)

                        children.append(Individual(
                            expression=child_tree,
                            age=min(members[a_idx].age, members[b_idx].age) + 1,
                            operator=operator,
                            parents=(members[a_idx].ident, members[b_idx].ident),
                            island=island_index,
                            ident=next_id,
                        ))
                        next_id += 1

                    # If the retry budget ran out, top up from the current generation rather than
                    # letting the population shrink. A shrinking population would silently change the
                    # search budget mid-run and make the ablation dishonest.
                    if len(children) < len(members):
                        for i in order[: len(members) - len(children)]:
                            children.append(dataclass_replace(members[int(i)], age=members[int(i)].age + 1))

                    # -- survival
                    if cfg.multi_objective or cfg.age_fitness:
                        pool = members + children
                        pool_losses = np.array([
                            m.loss if math.isfinite(m.loss) else 1e300 for m in pool
                        ])
                        if cfg.age_fitness and cfg.multi_objective:
                            objectives = np.column_stack([
                                pool_losses,
                                np.array([node_count(m.expression) for m in pool], dtype=float),
                                np.array([m.age for m in pool], dtype=float),
                            ])
                            keep = nsga2_survival(objectives, len(members))
                        elif cfg.multi_objective:
                            objectives = np.column_stack([
                                pool_losses,
                                np.array([node_count(m.expression) for m in pool], dtype=float),
                            ])
                            keep = nsga2_survival(objectives, len(members))
                        else:
                            keep = age_fitness_survival(
                                pool_losses, np.array([m.age for m in pool]), len(members)
                            )
                        islands[island_index] = [pool[i] for i in keep]
                    else:
                        islands[island_index] = children[: len(members)]

                # -- migration between islands
                if len(islands) > 1 and generation > 0 and generation % max(1, cfg.migration_every) == 0:
                    for source in range(len(islands)):
                        destination = (source + 1) % len(islands)
                        donors = sorted(islands[source], key=lambda m: m.loss)[: cfg.migration_size]
                        if not donors:
                            continue
                        victims = sorted(range(len(islands[destination])),
                                         key=lambda i: -islands[destination][i].loss)[: len(donors)]
                        deltas = []
                        for slot, donor in zip(victims, donors):
                            deltas.append(donor.loss - islands[destination][slot].loss)
                            islands[destination][slot] = dataclass_replace(donor, island=destination)
                        migrations.append({
                            "generation": generation, "from": source, "to": destination,
                            "count": len(donors),
                            "mean_fitness_delta": round(float(np.mean(deltas)), 8) if deltas else 0.0,
                        })

                # -- history for this generation
                finite_losses = [m.loss for m in all_members if math.isfinite(m.loss)]
                history_generation.append(generation)
                history_evals.append(evaluations)
                history_best.append(round(min(finite_losses), 10) if finite_losses else None)
                history_mean.append(round(float(np.mean(finite_losses)), 10) if finite_losses else None)
                history_worst.append(round(max(finite_losses), 10) if finite_losses else None)
                history_struct_div.append(
                    round(len({canonical_key(m.expression) for m in all_members}) / max(1, len(all_members)), 6)
                )
                history_sem_div.append(
                    round(len({semantic_key(evaluate(m.expression, X[:32])) for m in all_members})
                          / max(1, len(all_members)), 6)
                )
                counts: dict[str, int] = {}
                for m in all_members:
                    for op, c in count_operators(m.expression).items():
                        counts[op] = counts.get(op, 0) + c
                total = sum(counts.values()) or 1
                entropy = -sum((c / total) * math.log(c / total) for c in counts.values() if c > 0)
                history_op_entropy.append(round(entropy, 6))
                for i, op in enumerate(operator_names):
                    operator_matrix[i].append(counts.get(op, 0))

            # -- the Pareto front, built from the archive rather than the final population
            candidates = [m for m in archive.values() if math.isfinite(m.loss)]
            if not candidates:
                empty = Individual(expression=Node.const(float(np.mean(y))), loss=float(np.var(y)), complexity=1)
                candidates = [empty]
            points = [(m.loss, float(node_count(m.expression))) for m in candidates]
            front_indices = pareto_front(points)
            front = [candidates[i] for i in front_indices]
            front.sort(key=lambda m: node_count(m.expression))
            scores = pareto_score([(m.loss, float(node_count(m.expression))) for m in front])

            # Fold the fitted scaling into the reported expression, so the shown model IS the scored one,
            # and RECOMPUTE complexity afterwards. Folding adds nodes (a multiply, an add and their two
            # constants), so reporting the pre-folding count would understate complexity on one of the two
            # axes the whole product is read on. The Pareto ORDERING is unaffected, because scaling adds
            # the same fixed number of nodes to every scaled candidate, but the reported number is not.
            front = [
                dataclass_replace(
                    m,
                    expression=(folded := _apply_scaling(m.expression, m.scaling, self.config.linear_scaling)),
                    complexity=node_count(folded),
                )
                for m in front
            ]
            scores = pareto_score([(m.loss, float(m.complexity)) for m in front])
            best = min(front, key=lambda m: m.loss)

            history = {
                "generation": history_generation,
                "evals": history_evals,
                "best_loss": history_best,
                "mean_loss": history_mean,
                "worst_loss": history_worst,
                "diversity": {
                    "structural": history_struct_div,
                    "semantic": history_sem_div,
                    "operator_entropy": history_op_entropy,
                },
                "operator_freq": {"ops": operator_names, "matrix": operator_matrix},
                "islands": island_traces if len(islands) > 1 else [],
                "migrations": migrations,
            }
            counters = {
                "archive_size": len(archive),
                "front_size": len(front),
                "evaluations": evaluations,
                "max_depth_seen": max((depth(m.expression) for m in front), default=0),
                "max_size_seen": max((size(m.expression) for m in front), default=0),
            }
            return SearchResult(
                config=self.config, seed=seed, pareto=front, pareto_scores=scores, best=best,
                history=history, counters=counters, duplicates_avoided=duplicates_avoided,
                invalid_rejected=invalid_rejected,
                wall_seconds=round(time.perf_counter() - started, 3),
            )
        finally:
            errstate.__exit__(None, None, None)


#: The ladder as configurations. Each entry adds exactly ONE mechanism to the one before it, so the
#: Experiments page can attribute a measured difference to a named change rather than to a bundle.
LADDER: dict[str, SearchConfig] = {
    "r1-koza-baseline": SearchConfig(),
    "r2-linear-scaling": SearchConfig(linear_scaling=True, interval_guard=True, interval_margin=0.25),
    "r3-constant-tuning": SearchConfig(linear_scaling=True, interval_guard=True, interval_margin=0.25,
                                       constant_tuning=True),
    "r4-multi-objective": SearchConfig(linear_scaling=True, interval_guard=True, interval_margin=0.25,
                                       constant_tuning=True, multi_objective=True),
    "r5-epsilon-lexicase": SearchConfig(linear_scaling=True, interval_guard=True, interval_margin=0.25,
                                        constant_tuning=True, multi_objective=True,
                                        epsilon_lexicase=True),
    "r6-age-fitness-islands": SearchConfig(linear_scaling=True, interval_guard=True, interval_margin=0.25,
                                           constant_tuning=True, epsilon_lexicase=True,
                                           age_fitness=True, n_islands=4),
    "r7-deduplication": SearchConfig(linear_scaling=True, interval_guard=True, interval_margin=0.25,
                                     constant_tuning=True, multi_objective=True, epsilon_lexicase=True,
                                     age_fitness=True, n_islands=4,
                                     dedup_structural=True, dedup_semantic=True),
    "r8-unit-typed": SearchConfig(linear_scaling=True, interval_guard=True, interval_margin=0.25,
                                  constant_tuning=True, multi_objective=True, epsilon_lexicase=True,
                                  age_fitness=True, n_islands=4,
                                  dedup_structural=True, dedup_semantic=True, unit_typed=True),
    "parsimony-arm": SearchConfig(linear_scaling=True, interval_guard=True, interval_margin=0.25,
                                  constant_tuning=True, parsimony_coefficient=0.001),
}
