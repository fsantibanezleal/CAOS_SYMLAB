"""Stage 5: scoring, including the equivalence test that separates fitting from discovery.

This is the stage the whole lab is built around. The benchmark literature's most damaging finding is
that a method can score above 0.999 on a coefficient of determination while recovering the correct
STRUCTURE zero percent of the time. That gap is only visible if structure is tested directly, and
testing it is unreliable if you use only one test.

So three independent tests run, and their DISAGREEMENTS are reported rather than resolved:

1. **Symbolic**: simplify the difference between the candidate and the truth and ask whether it is
   zero. Exact when it works, but the simplifier times out or throws on a non-trivial fraction of
   real cases, and the standard practice of scoring those as method failures is wrong: it charges
   the search for a defect in the scoring tool.

2. **Numerical**: evaluate both expressions at many random points across the input box and compare.
   Cheap, robust to the simplifier's limits, and blind to the difference between an expression that
   is genuinely equivalent and one that merely agrees on the sampled region.

3. **Structural**: normalised tree edit distance between the canonical forms. This is the only one
   of the three that gives GRADED credit, so a nearly-right expression is distinguishable from a
   completely wrong one, which a binary test cannot do.

The sympy failure RATE is measured and published. The research identified that as one of the three
contributions a lab of this size can credibly make, precisely because nobody currently reports it.
"""
from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np

from ..model.complexity import description_length
from ..model.expr import KIND_CONST, KIND_VAR, Node, evaluate, is_valid, variables_used, walk
from .infer import VariantInference
from .preprocess import PreparedCase
from .train import TrainedVariant

# The equivalence protocol itself lives in `sreval`, an MIT package extracted from this lab. It is
# imported rather than duplicated: a second copy of a scoring rule is a second place for it to drift,
# and the whole argument of that package is that the scorer must be auditable.
try:  # pragma: no cover - exercised by the pipeline, not by the unit tests
    from sreval import metrics as sreval_metrics
    from sreval.equivalence import structural_distance as sreval_structural_distance

    HAS_SREVAL = True
except ImportError:  # the browser lane never installs it, and never needs it
    sreval_metrics = None
    sreval_structural_distance = None
    HAS_SREVAL = False


#: Points sampled for the numerical equivalence test.
NUMERICAL_PROBE_POINTS = 512

#: Relative tolerance at which two expressions count as numerically equivalent.
NUMERICAL_TOLERANCE = 1e-6

#: The accuracy threshold the benchmark convention uses for an "accuracy solution".
ACCURACY_R2_THRESHOLD = 0.999


@dataclass
class EquivalenceVerdict:
    """The three tests, their verdicts, and whether they agreed."""

    symbolic: bool | None            # None means the simplifier could not decide
    symbolic_error: str
    numerical: bool | None
    numerical_max_rel_error: float | None
    structural_distance: float | None   # 0 identical, 1 completely different
    agreed: bool
    disagreement_note: str = ""

    @property
    def recovered(self) -> bool:
        """The lab's recovery verdict: symbolic if available, otherwise numerical."""
        if self.symbolic is not None:
            return self.symbolic
        return bool(self.numerical)


def _to_sympy(expression: Node, variables: list[str]):
    """Convert to a sympy expression. Imported lazily so the browser lane never needs sympy."""
    import sympy

    symbols = {i: sympy.Symbol(name, real=True) for i, name in enumerate(variables)}
    unary = {
        "neg": lambda a: -a, "square": lambda a: a**2, "sqrt": sympy.sqrt,
        "exp": sympy.exp, "log": sympy.log, "sin": sympy.sin, "cos": sympy.cos,
        "tanh": sympy.tanh, "inv": lambda a: 1 / a, "abs": sympy.Abs,
    }
    binary = {
        "add": lambda a, b: a + b, "sub": lambda a, b: a - b,
        "mul": lambda a, b: a * b, "div": lambda a, b: a / b,
    }

    def convert(node: Node):
        if node.kind == KIND_CONST:
            return sympy.Float(float(node.value))
        if node.kind == KIND_VAR:
            return symbols[int(node.var_index)]
        op = str(node.op)
        children = [convert(c) for c in node.children]
        if op in binary:
            return binary[op](*children)
        if op in unary:
            return unary[op](*children)
        raise ValueError(f"no sympy mapping for operator {op!r}")

    return convert(expression)


#: Significant digits every numeric coefficient is rounded to before the symbolic comparison.
#:
#: The comparison used to be bit-exact, and a coefficient one unit in the last place away from the
#: truth therefore read as a different law. Measured: the sparse arm returned `1 * (mu * Nn)` on
#: feynman-i_12_1 with a least-squares coefficient of 1 plus 2.2e-16, the numerical test agreed to a
#: maximum relative error of 7.6e-16, and the artifact published "structure NOT recovered" next to a
#: printed expression identical to the truth.
#:
#: Twelve digits is far beyond what any search recovers meaningfully and far short of that noise. A
#: genuinely wrong constant differs in the second or third significant digit.
SYMBOLIC_COEFFICIENT_DIGITS = 12


def _round_floats(expression, digits: int = SYMBOLIC_COEFFICIENT_DIGITS):
    """Round every Float atom, so the comparison is about STRUCTURE and not about last-bit noise."""
    import sympy

    replacements = {}
    for atom in expression.atoms(sympy.Float):
        value = float(atom)
        replacements[atom] = sympy.Float(f"{value:.{digits}g}")
    return expression.xreplace(replacements) if replacements else expression


def symbolic_equivalence(
    candidate: Node, truth: Node, variables: list[str], *, timeout_seconds: float = 10.0
) -> tuple[bool | None, str]:
    """Simplify the difference and test for zero. Returns (verdict, error) with verdict None on failure.

    Numeric coefficients are rounded to `SYMBOLIC_COEFFICIENT_DIGITS` in both expressions first; see
    the note there for the measurement that forced it.

    A failure here is a defect of the SCORER, not of the search, and is reported as such. The
    standard practice of counting it against the method is one of the honesty traps the research
    identified.
    """
    try:
        import sympy

        a = _round_floats(_to_sympy(candidate, variables))
        b = _round_floats(_to_sympy(truth, variables))
        difference = sympy.simplify(a - b)
        return bool(difference == 0), ""
    except Exception as error:  # noqa: BLE001 - any simplifier failure is a scorer failure
        return None, f"{type(error).__name__}: {error}"


def numerical_equivalence(
    candidate: Node, truth: Node, box: list[tuple[float, float]], *, seed: int = 0
) -> tuple[bool | None, float | None]:
    """Compare both expressions at random points across the input box."""
    rng = np.random.default_rng(seed)
    probe = np.column_stack([
        rng.uniform(low, high, size=NUMERICAL_PROBE_POINTS) for low, high in box
    ])
    a = evaluate(candidate, probe)
    b = evaluate(truth, probe)
    both_finite = np.isfinite(a) & np.isfinite(b)
    if not both_finite.any():
        return None, None
    denominator = np.maximum(np.abs(b[both_finite]), 1e-12)
    relative = np.abs(a[both_finite] - b[both_finite]) / denominator
    worst = float(np.max(relative))
    return bool(worst <= NUMERICAL_TOLERANCE), worst


def _canonical_labels(node: Node) -> list[str]:
    """A pre-order label sequence, with constants collapsed so numeric drift is not scored as
    structural difference."""
    labels: list[str] = []
    for n in walk(node):
        if n.kind == KIND_CONST:
            labels.append("C")
        elif n.kind == KIND_VAR:
            labels.append(f"v{n.var_index}")
        else:
            labels.append(str(n.op))
    return labels


def structural_distance(candidate: Node, truth: Node) -> float:
    """Normalised edit distance between the two label sequences, in [0, 1].

    A sequence edit distance over the pre-order traversal rather than a full tree edit distance: it
    is O(n*m) instead of O(n^2 m^2), and on expressions of the sizes this lab produces the two agree
    closely enough that the extra cost buys nothing. The choice is stated here because the metric is
    reported, and a reported metric whose definition is implicit is not reproducible.

    DELEGATES to `sreval` when it is installed, which is the whole reason that package was extracted:
    the scorer is a general problem and it should not have a second private implementation living
    here. The local loop below is the browser-lane fallback, because Pyodide never installs sreval,
    and `tests/test_sreval_agrees.py` asserts the two produce identical numbers so the fallback can
    never quietly diverge from the published scorer.

    Until this call existed, `sreval` was imported at the top of this file, pinned in
    `requirements-precompute.txt`, and documented as "used here", while nothing in the module ever
    referenced it.
    """
    a, b = _canonical_labels(candidate), _canonical_labels(truth)
    if not a and not b:
        return 0.0
    if HAS_SREVAL:
        return round(min(1.0, float(sreval_structural_distance(a, b).distance)), 6)
    previous = list(range(len(b) + 1))
    for i, token_a in enumerate(a, start=1):
        current = [i]
        for j, token_b in enumerate(b, start=1):
            current.append(min(
                previous[j] + 1,
                current[j - 1] + 1,
                previous[j - 1] + (0 if token_a == token_b else 1),
            ))
        previous = current
    return round(min(1.0, previous[-1] / max(len(a), len(b))), 6)


def check_equivalence(
    candidate: Node, truth: Node, variables: list[str], box: list[tuple[float, float]], *, seed: int = 0
) -> EquivalenceVerdict:
    """Run all three tests and report whether they agreed."""
    symbolic, symbolic_error = symbolic_equivalence(candidate, truth, variables)
    numerical, worst = numerical_equivalence(candidate, truth, box, seed=seed)
    distance = structural_distance(candidate, truth)

    verdicts = [v for v in (symbolic, numerical) if v is not None]
    agreed = len(set(verdicts)) <= 1
    note = ""
    if not agreed:
        note = (
            f"the symbolic test says {symbolic} and the numerical test says {numerical}. "
            "This usually means the expressions agree on the sampled region but differ elsewhere, "
            "or that the simplifier failed to reduce an equivalent difference to zero."
        )
    elif symbolic is None:
        note = f"the symbolic test could not decide ({symbolic_error}); the numerical verdict is used."

    return EquivalenceVerdict(
        symbolic=symbolic, symbolic_error=symbolic_error,
        numerical=numerical, numerical_max_rel_error=worst,
        structural_distance=distance, agreed=agreed, disagreement_note=note,
    )


@dataclass
class VariantScore:
    """Everything the Benchmark page needs about one variant."""

    variant_id: str
    label: str
    seconds: float
    evaluations: int
    duplicates_avoided: int
    invalid_rejected: int
    front_size: int
    best_train_mse: float | None
    best_test_mse: float | None
    best_test_r2: float | None
    best_extrapolation_mse: float | None
    accuracy_solution: bool
    selected_index: int
    selected_complexity: int
    selected_description_length: float
    n_irrelevant_features: int
    equivalence: EquivalenceVerdict | None = None
    notes: list[str] = field(default_factory=list)


def select_by_description_length(
    trained: TrainedVariant, X: np.ndarray, y: np.ndarray, *, n_primitives: int
) -> int:
    """Pick one point on the front by minimum description length, not by best accuracy.

    Selecting by accuracy reproduces the field's headline failure: the most accurate member of a
    front is routinely the most over-parameterised one, which is how a method scores above 0.999
    while recovering the wrong structure every time.
    """
    best_index, best_value = 0, float("inf")
    for index, individual in enumerate(trained.result.pareto):
        prediction = evaluate(individual.expression, X)
        if not is_valid(prediction):
            continue
        value = description_length(
            individual.expression, y, prediction,
            n_primitives=n_primitives, n_variables=X.shape[1],
        ).total
        if value < best_value:
            best_index, best_value = index, value
    return best_index


def run(
    prepared: PreparedCase,
    trained: list[TrainedVariant],
    inferred: list[VariantInference],
    *,
    truth: Node | None = None,
    seed: int = 0,
) -> list[VariantScore]:
    """Score every variant, including equivalence against a known truth where one exists."""
    box = [
        (float(np.min(prepared.X_train[:, j])), float(np.max(prepared.X_train[:, j])))
        for j in range(prepared.X_train.shape[1])
    ]
    variables = list(prepared.dataset.input_keys)
    truth_variables = set(variables_used(truth)) if truth is not None else set()

    scores: list[VariantScore] = []
    for entry, inference in zip(trained, inferred):
        n_primitives = len(entry.result.config.primitive_set)
        selected = select_by_description_length(
            entry, prepared.X_train, prepared.y_train, n_primitives=n_primitives
        )
        selected_individual = entry.result.pareto[selected]
        selected_member = inference.members[selected]

        prediction = evaluate(selected_individual.expression, prepared.X_train)
        dl = description_length(
            selected_individual.expression, prepared.y_train, prediction,
            n_primitives=n_primitives, n_variables=prepared.X_train.shape[1],
        ) if is_valid(prediction) else None

        used = variables_used(selected_individual.expression)
        irrelevant = len(used - truth_variables) if truth is not None else 0

        equivalence = None
        if truth is not None:
            equivalence = check_equivalence(
                selected_individual.expression, truth, variables, box, seed=seed
            )

        test_r2 = selected_member.test.r2
        scores.append(VariantScore(
            variant_id=entry.variant.id,
            label=entry.variant.label_en,
            seconds=entry.seconds,
            evaluations=int(entry.result.counters.get("evaluations", 0)),
            duplicates_avoided=entry.result.duplicates_avoided,
            invalid_rejected=entry.result.invalid_rejected,
            front_size=len(entry.result.pareto),
            best_train_mse=selected_member.train.mse,
            best_test_mse=selected_member.test.mse,
            best_test_r2=test_r2,
            best_extrapolation_mse=(
                selected_member.extrapolation.mse if selected_member.extrapolation else None
            ),
            accuracy_solution=bool(test_r2 is not None and test_r2 >= ACCURACY_R2_THRESHOLD),
            selected_index=selected,
            selected_complexity=selected_individual.complexity,
            selected_description_length=dl.total if dl else float("inf"),
            n_irrelevant_features=irrelevant,
            equivalence=equivalence,
        ))
    return scores


def summarise(scores: list[VariantScore]) -> dict:
    """The headline numbers, computed the way the lab intends to report them.

    `accuracy_solution_rate` and `exact_recovery_rate` are reported SEPARATELY and never merged.
    The gap between them is the single most important number this lab produces.
    """
    total = len(scores)
    if total == 0:
        return {}
    with_truth = [s for s in scores if s.equivalence is not None]
    symbolic_attempted = len(with_truth)
    symbolic_failed = sum(1 for s in with_truth if s.equivalence.symbolic is None)
    return {
        "n_variants": total,
        "accuracy_solutions": sum(1 for s in scores if s.accuracy_solution),
        "accuracy_solution_rate": round(sum(1 for s in scores if s.accuracy_solution) / total, 4),
        "exact_recoveries": sum(1 for s in with_truth if s.equivalence.recovered),
        "exact_recovery_rate": (
            round(sum(1 for s in with_truth if s.equivalence.recovered) / symbolic_attempted, 4)
            if symbolic_attempted else None
        ),
        "mean_structural_distance": (
            round(float(np.mean([s.equivalence.structural_distance for s in with_truth
                                 if s.equivalence.structural_distance is not None])), 4)
            if with_truth else None
        ),
        "symbolic_test_failure_rate": (
            round(symbolic_failed / symbolic_attempted, 4) if symbolic_attempted else None
        ),
        "test_disagreement_count": sum(1 for s in with_truth if not s.equivalence.agreed),
        "total_seconds": round(sum(s.seconds for s in scores), 2),
        "total_evaluations": sum(s.evaluations for s in scores),
        "variants_with_irrelevant_features": sum(1 for s in with_truth if s.n_irrelevant_features > 0),
    }
