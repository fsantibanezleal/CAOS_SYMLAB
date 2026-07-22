"""CONTRACT 2, the pipeline-to-web payload, frozen at `schema_version 1.0.0`.

Every view in the web app is a pure function of what this module emits. That is the point of
freezing it before any UI exists: the renderer never computes anything it could have been given, so
there is exactly one place where a number can be wrong.

Six rules are enforced here rather than left to the caller, because each of them has a known failure
mode behind it:

1. **Every float is rounded before it ships.** `0.30000000000000004` is a rendering bug that starts
   in Python. `_round_floats` walks the whole payload on the way out.
2. **Both `latex_raw` and `latex_pretty` ship.** The reader must be able to see what the engine
   actually produced, not only the prettified form.
3. **Node ids are one integer space.** The `nid` inside the LaTeX, the `id` in the flat node list and
   the `node_id` in `terms` all come from the same pre-order walk. Three views, one identity.
4. **`color_index` is assigned in Python.** The equation, the tree and the stacked contribution chart
   read the same ordering, so their palettes cannot drift apart.
5. **Nothing that Python can compute is left to the browser.** No simplification, no bootstrap, no
   partial dependence, no tree layout arithmetic beyond the layout itself.
6. **Every file carries `schema_version`.** The app refuses to render a payload whose major version
   it does not recognise, visibly, rather than rendering a blank panel.

A seventh rule is specific to this lab's honesty commitments: whenever a payload is downsampled, the
original count ships next to it. Exporting 12 front members out of 16 is fine; not saying so is not.
That pair is real and checkable: `MAX_EXPORTED_MEMBERS` is 12, and `ccpp-derating` has a variant
whose front holds 16, which the artifact reports as `pareto_exported` 12 and `pareto_total` 16.

An earlier version of this paragraph illustrated the rule with "24 lineages out of 184,320
individuals". No budget in this repo produces 184,320 of anything: a case runs 300 by 40 per rung.
An invented example inside a paragraph about not hiding numbers is the wrong place to invent one.
"""
from __future__ import annotations

import math
from typing import Any, Iterable, Sequence

import numpy as np

from ..model import complexity as cx
from ..model import latex as tex
from ..model.expr import (
    KIND_CONST,
    KIND_VAR,
    Node,
    count_operators,
    depth,
    evaluate,
    is_valid,
    parent_map,
    size,
    top_level_terms,
    variables_used,
    walk,
)
from ..model.units import DIMENSIONLESS, Dims, format_dims, infer_dims

#: The frozen contract version. A change to the MAJOR component is a breaking change and requires a
#: matching change in the web app's mirrored TypeScript types.
SCHEMA_VERSION = "1.0.0"

#: How many SIGNIFICANT digits reach the browser, not decimal places.
#:
#: Ten rather than six, because the numbers this lab argues about live where six is not enough. An
#: R-squared of 0.999999998 rounds to exactly 1.0 at six significant digits, and "1.0" beside
#: "structure not recovered" reads as a contradiction instead of as the finding. Six DECIMAL places,
#: which is what this was before, additionally sent a mean squared error of 6.1e-12 to exactly zero.
#:
#: The cost is about four characters per float in the validation arrays. That is a fair price for
#: not publishing a claim of a mathematically exact fit that the search did not achieve.
FLOAT_DIGITS = 10


def _significant(value: float, digits: int) -> float:
    """Round to SIGNIFICANT digits, not decimal places.

    `round(v, 6)` sends everything below 5e-7 to exactly 0.0. That published a mean squared error of
    6.1e-12 as "0.0" and an R-squared of 0.999999998 as "1.0", which are claims of a mathematically
    exact fit. This lab's whole argument is the difference between a very good fit and the right
    answer, and a variant reporting zero error beside "structure not recovered" reads as a
    contradiction rather than as the finding it is.

    Significant digits keep the payload compact without destroying small magnitudes: a loss of
    1e-12 stays 1e-12, and 1234567.891 stays 1234567.891.
    """
    if value == 0.0:
        return 0.0
    return float(f"{value:.{digits}g}")


def _round_floats(obj: Any, digits: int = FLOAT_DIGITS) -> Any:
    """Recursively round every float in a payload. Rule 1, applied once, at the boundary."""
    if isinstance(obj, float):
        if not math.isfinite(obj):
            return None
        return _significant(obj, digits)
    if isinstance(obj, (np.floating,)):
        value = float(obj)
        return None if not math.isfinite(value) else _significant(value, digits)
    if isinstance(obj, (np.integer,)):
        return int(obj)
    if isinstance(obj, np.ndarray):
        return _round_floats(obj.tolist(), digits)
    if isinstance(obj, dict):
        return {k: _round_floats(v, digits) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [_round_floats(v, digits) for v in obj]
    return obj


# --------------------------------------------------------------------------------------------
# Influence: the one definition, used everywhere
# --------------------------------------------------------------------------------------------


def subtree_influence(root: Node, X: np.ndarray, y: np.ndarray) -> dict[int, float]:
    """Influence of every subtree, defined once and reused by every view that encodes importance.

    The definition: replace the subtree by its own mean over the training rows, re-evaluate the whole
    expression, and measure how much the coefficient of determination drops. Normalised so the root
    is 1.0.

    This single number drives node radius in the tree, the ordering of terms in the equation, and the
    band ordering in the contribution chart. Defining it in three places would guarantee that the
    three eventually disagree, which is why it lives here and is exported rather than recomputed.

    A subtree whose replacement leaves the fit unchanged scores zero. That is informative rather than
    a defect: it means the subtree is inert, and inert subtrees are exactly what the complexity axis
    is supposed to penalise.
    """
    base_pred = evaluate(root, X)
    if not is_valid(base_pred):
        return {i: 0.0 for i, _ in enumerate(walk(root))}
    y_var = float(np.var(y))
    if y_var <= 0.0:
        return {i: 0.0 for i, _ in enumerate(walk(root))}
    base_r2 = 1.0 - float(np.mean((y - base_pred) ** 2)) / y_var

    nodes = list(walk(root))
    out: dict[int, float] = {}
    raw: dict[int, float] = {}

    for node_id, node in enumerate(nodes):
        if node_id == 0:
            raw[node_id] = max(base_r2, 0.0)
            continue
        subtree_values = evaluate(node, X)
        if not is_valid(subtree_values):
            raw[node_id] = 0.0
            continue
        replacement = float(np.mean(subtree_values))
        ablated = _replace_subtree_by_id(root, node_id, Node.const(replacement))
        ablated_pred = evaluate(ablated, X)
        if not is_valid(ablated_pred):
            raw[node_id] = max(base_r2, 0.0)
            continue
        ablated_r2 = 1.0 - float(np.mean((y - ablated_pred) ** 2)) / y_var
        raw[node_id] = max(base_r2 - ablated_r2, 0.0)

    scale = max(raw.values()) if raw else 0.0
    for node_id, value in raw.items():
        out[node_id] = round(value / scale, 6) if scale > 0 else 0.0
    out[0] = 1.0
    return out


def _replace_subtree_by_id(root: Node, target_id: int, replacement: Node) -> Node:
    """Rebuild the tree with the subtree at `target_id` (pre-order) swapped out."""
    counter = 0

    def rebuild(node: Node) -> Node:
        nonlocal counter
        my_id = counter
        counter += 1
        if my_id == target_id:
            # skip the rest of this subtree in the id walk
            counter += size(node) - 1
            return replacement
        if node.is_leaf:
            return node
        return Node(kind=node.kind, op=node.op, children=tuple(rebuild(c) for c in node.children))

    return rebuild(root)


# --------------------------------------------------------------------------------------------
# 6.3 the flat tree node list
# --------------------------------------------------------------------------------------------


def tree_payload(
    root: Node,
    X: np.ndarray,
    y: np.ndarray,
    *,
    input_dims: Sequence[Dims] | None = None,
    display_names: list[str] | None = None,
) -> dict:
    """The flat node list. Flat rather than nested: it serialises smaller, diffs cleanly, and the
    browser rebuilds the hierarchy from `parent` in one call."""
    parents = parent_map(root)
    influence = subtree_influence(root, X, y)
    terms = tex.term_assignment(root)
    dims_ok: dict[int, tuple[bool, Dims | None]] = {}
    if input_dims is not None:
        for node_id, node in enumerate(walk(root)):
            check = infer_dims(node, list(input_dims))
            dims_ok[node_id] = (check.ok, check.dims)

    nodes: list[dict] = []
    for node_id, node in enumerate(walk(root)):
        values = evaluate(node, X)
        finite = is_valid(values)
        entry: dict[str, Any] = {
            "id": node_id,
            "parent": parents[node_id],
            "kind": node.kind,
            "label": tex.node_kind_label(node, display_names),
            "arity": node.arity,
            "depth": _depth_of(root, node_id),
            "subtree_size": size(node),
            "influence": influence.get(node_id, 0.0),
            "mean_value": float(np.mean(values)) if finite else None,
            "abs_value_p95": float(np.percentile(np.abs(values), 95)) if finite else None,
            "term_id": terms.get(node_id),
        }
        if node.kind == KIND_CONST:
            entry["value"] = float(node.value)  # type: ignore[arg-type]
        if node.kind == KIND_VAR:
            entry["var_index"] = int(node.var_index)  # type: ignore[arg-type]
        if node_id in dims_ok:
            ok, d = dims_ok[node_id]
            entry["unit_ok"] = ok
            entry["unit_dims"] = list(d) if d is not None else None
            entry["unit_label"] = format_dims(d) if d is not None else None
        nodes.append(entry)

    return {"nodes": nodes, "max_depth": depth(root), "n_nodes": size(root)}


def _depth_of(root: Node, target_id: int) -> int:
    counter = 0
    found = -1

    def visit(node: Node, d: int) -> None:
        nonlocal counter, found
        my_id = counter
        counter += 1
        if my_id == target_id:
            found = d
        for child in node.children:
            visit(child, d + 1)

    visit(root, 0)
    return found


# --------------------------------------------------------------------------------------------
# 6.2 a Pareto member
# --------------------------------------------------------------------------------------------


def pareto_member_payload(
    root: Node,
    X_train: np.ndarray,
    y_train: np.ndarray,
    *,
    index: int,
    X_test: np.ndarray | None = None,
    y_test: np.ndarray | None = None,
    display_names: list[str] | None = None,
    input_dims: Sequence[Dims] | None = None,
    target_dims: Dims | None = None,
    n_primitives: int = 8,
    on_front: bool = True,
    score: float = 0.0,
    sig_digits: int = 4,
    rounding_tolerance: float = 1e-3,
) -> dict:
    """One candidate expression, with everything the App needs to render and to judge it."""
    rounded, rounding = tex.round_constants(
        root, X_train, sig_digits=sig_digits, tolerance=rounding_tolerance
    )
    shown = rounded if rounding.accepted else root

    y_pred_train = evaluate(shown, X_train)
    loss_train = _mse(y_train, y_pred_train)
    loss_test = None
    if X_test is not None and y_test is not None:
        loss_test = _mse(y_test, evaluate(shown, X_test))

    terms_map = tex.term_assignment(shown)
    term_entries = _term_entries(shown, X_train, display_names=display_names, sig_digits=sig_digits)

    units_ok = None
    units_reason = ""
    if input_dims is not None and target_dims is not None:
        from ..model.units import check as unit_check

        verdict = unit_check(shown, list(input_dims), target_dims)
        units_ok = verdict.ok
        units_reason = verdict.reason

    dl = cx.description_length(
        shown, y_train, y_pred_train,
        n_primitives=n_primitives,
        n_variables=X_train.shape[1],
    )

    return {
        "index": index,
        "complexity": cx.node_count(shown),
        "complexity_weighted": cx.weighted_complexity(shown),
        "description_length": {
            "total": dl.total, "structure": dl.structure,
            "constants": dl.constants, "residuals": dl.residuals,
        },
        "bic": cx.bic(shown, y_train, y_pred_train),
        "loss_train": loss_train,
        "loss_test": loss_test,
        "r2_train": _r2(y_train, y_pred_train),
        "r2_test": _r2(y_test, evaluate(shown, X_test)) if (X_test is not None and y_test is not None) else None,
        "score": score,
        "on_front": on_front,
        "raw_string": _infix(shown, display_names),
        "latex_raw": tex.to_latex(shown, display_names=display_names, sig_digits=sig_digits),
        "latex_pretty": tex.to_latex(
            shown, display_names=display_names, sig_digits=sig_digits,
            annotate=True, term_of_node=terms_map,
        ),
        "latex_aligned": tex.aligned_latex(shown, display_names=display_names, sig_digits=sig_digits),
        "rounding": {
            "sig_digits": rounding.sig_digits,
            "tolerance": rounding_tolerance,
            "max_rel_error": rounding.max_rel_error,
            "accepted": rounding.accepted,
        },
        "tree": tree_payload(shown, X_train, y_train, input_dims=input_dims, display_names=display_names),
        "terms": term_entries,
        "variables_used": sorted(variables_used(shown)),
        "n_variables_available": int(X_train.shape[1]),
        "operator_counts": count_operators(shown),
        "units_ok": units_ok,
        "units_reason": units_reason,
    }


def _infix(node: Node, display_names: list[str] | None) -> str:
    from ..model.expr import to_infix

    return to_infix(node, display_names)


def _term_entries(
    root: Node, X: np.ndarray, *, display_names: list[str] | None, sig_digits: int
) -> list[dict]:
    """Top-level additive terms, ordered by contribution, with the colour index assigned HERE.

    Rule 4: one ordering, three consumers. The equation's `\\htmlClass`, the tree's `term_id` and the
    stacked area chart all read this list, so the palettes cannot drift.
    """
    terms = top_level_terms(root)
    entries: list[dict] = []
    node_ids = _term_root_ids(root)
    for term_id, term in enumerate(terms):
        values = evaluate(term, X)
        finite = is_valid(values)
        entries.append({
            "term_id": term_id,
            "node_id": node_ids[term_id] if term_id < len(node_ids) else None,
            "latex": tex.to_latex(term, display_names=display_names, sig_digits=sig_digits),
            "mean_abs_contrib": float(np.mean(np.abs(values))) if finite else 0.0,
            "var_share": 0.0,
            "complexity": cx.node_count(term),
        })
    total_variance = sum(
        float(np.var(evaluate(t, X))) if is_valid(evaluate(t, X)) else 0.0 for t in terms
    )
    if total_variance > 0:
        for entry, term in zip(entries, terms):
            values = evaluate(term, X)
            entry["var_share"] = round(
                (float(np.var(values)) if is_valid(values) else 0.0) / total_variance, 6
            )
    order = sorted(range(len(entries)), key=lambda i: -entries[i]["mean_abs_contrib"])
    for colour, i in enumerate(order):
        entries[i]["color_index"] = colour
    return entries


def _term_root_ids(root: Node) -> list[int]:
    """Pre-order ids of the top-level term roots, in term order."""
    terms = top_level_terms(root)
    wanted = {id(t): i for i, t in enumerate(terms)}
    out: dict[int, int] = {}
    counter = 0

    def visit(node: Node) -> None:
        nonlocal counter
        my_id = counter
        counter += 1
        if id(node) in wanted and wanted[id(node)] not in out:
            out[wanted[id(node)]] = my_id
        for child in node.children:
            visit(child)

    visit(root)
    return [out.get(i, 0) for i in range(len(terms))]


# --------------------------------------------------------------------------------------------
# 6.4 generation history, columnar
# --------------------------------------------------------------------------------------------


def history_payload(
    *,
    generation: Sequence[int],
    best_loss: Sequence[float],
    mean_loss: Sequence[float],
    worst_loss: Sequence[float],
    evaluations: Sequence[int],
    diversity_structural: Sequence[float] | None = None,
    diversity_semantic: Sequence[float] | None = None,
    operator_entropy: Sequence[float] | None = None,
    operator_names: Sequence[str] | None = None,
    operator_matrix: Sequence[Sequence[float]] | None = None,
    islands: Iterable[dict] | None = None,
    migrations: Iterable[dict] | None = None,
) -> dict:
    """Columnar arrays, not arrays of objects.

    The chart library consumes columns directly and the payload is several times smaller. This is
    the one place in the contract where the shape is chosen for the renderer rather than for
    readability, and it is a deliberate trade.
    """
    return {
        "generation": list(generation),
        "evals": list(evaluations),
        "best_loss": list(best_loss),
        "mean_loss": list(mean_loss),
        "worst_loss": list(worst_loss),
        "diversity": {
            "structural": list(diversity_structural or []),
            "semantic": list(diversity_semantic or []),
            "operator_entropy": list(operator_entropy or []),
        },
        "operator_freq": {
            "ops": list(operator_names or []),
            "matrix": [list(row) for row in (operator_matrix or [])],
        },
        "islands": list(islands or []),
        "migrations": list(migrations or []),
    }


# --------------------------------------------------------------------------------------------
# 6.6 model-validation arrays
# --------------------------------------------------------------------------------------------


def parity_stride(n_rows: int, max_points: int) -> int:
    """The one definition of the parity stride.

    It has to be one definition because two blocks are exported separately and then read side by
    side: the per-variant parity arrays, and the per-case input columns below. If those two ever
    used different strides the app would plot a residual against the wrong row's input and nothing
    would look wrong on screen.
    """
    return max(1, n_rows // max_points)


def parity_input_columns(
    X_train: np.ndarray,
    *,
    X_test: np.ndarray | None = None,
    input_keys: Sequence[str] | None = None,
    max_parity_points: int = 2000,
) -> dict:
    """The input columns behind the parity arrays, exported ONCE per case.

    A column of the data is a property of the case, not of the expression being scored, so storing
    it inside each variant multiplied it by the number of rungs for no information. Row order and
    stride match `validation_payload` exactly, by construction: both call `parity_stride`, and both
    stack train before test.
    """
    keys = list(input_keys or [f"x{i}" for i in range(X_train.shape[1])])
    X_all = np.vstack([X_train, X_test]) if X_test is not None else X_train
    stride = parity_stride(len(X_all), max_parity_points)
    return {
        "stride": stride,
        "n_shown": int(len(X_all[::stride])),
        "n_total": int(len(X_all)),
        "columns": {key: X_all[::stride, j].tolist() for j, key in enumerate(keys)},
    }


def validation_payload(
    root: Node,
    X_train: np.ndarray,
    y_train: np.ndarray,
    *,
    X_test: np.ndarray | None = None,
    y_test: np.ndarray | None = None,
    input_keys: Sequence[str] | None = None,
    max_parity_points: int = 2000,
    pdp_grid: int = 40,
    extrapolation_factor: float = 2.0,
) -> dict:
    """Parity, residuals, partial dependence, partial effects and extrapolation behaviour.

    Partial EFFECTS are the piece worth naming: for a symbolic model the derivative with respect to
    an input is itself a closed-form expression, so the sensitivity can be reported exactly rather
    than approximated by sampling. That is the one interpretability move a black-box model cannot
    make, and it is why this lab shows it next to partial dependence rather than instead of it.
    """
    keys = list(input_keys or [f"x{i}" for i in range(X_train.shape[1])])

    if X_test is not None and y_test is not None:
        X_all = np.vstack([X_train, X_test])
        y_all = np.concatenate([y_train, y_test])
        split = np.concatenate([np.zeros(len(y_train), dtype=int), np.ones(len(y_test), dtype=int)])
    else:
        X_all, y_all, split = X_train, y_train, np.zeros(len(y_train), dtype=int)

    y_pred = evaluate(root, X_all)
    stride = parity_stride(len(y_all), max_parity_points)
    parity = {
        "y_true": y_all[::stride].tolist(),
        "y_pred": (y_pred[::stride] if is_valid(y_pred) else np.full_like(y_all[::stride], np.nan)).tolist(),
        "split": split[::stride].tolist(),
        "n_shown": int(len(y_all[::stride])),
        "n_total": int(len(y_all)),
    }

    # NOTE: the residual-against-each-input series is NOT stored here, and that is a size decision
    # with a measured cause. It used to be, as {input: {x, residual}} for all inputs of all variants,
    # and both halves were redundant: `residual` is exactly `y_true - y_pred` from the parity block
    # two lines up, byte for byte, repeated once per input, and `x` is a column of the data, which
    # does not depend on which expression is being scored and so was repeated once per variant too.
    # On the flotation case, 21 inputs by 3400 rows by 8 variants came to 12.1 MB of the 12.6 MB
    # artifact. The reader downloaded all of it to see a residual plot that the app can subtract for
    # itself. The x columns are now exported ONCE per case by `parity_input_columns` below, on the
    # same stride, and the residual is subtracted in the browser.

    pdp: list[dict] = []
    extrapolation: list[dict] = []
    for j, key in enumerate(keys):
        lo, hi = float(np.min(X_train[:, j])), float(np.max(X_train[:, j]))
        grid = np.linspace(lo, hi, pdp_grid)
        base = np.tile(np.mean(X_train, axis=0), (pdp_grid, 1))
        base[:, j] = grid
        curve = evaluate(root, base)
        pdp.append({
            "var": key,
            "grid": grid.tolist(),
            "mean": curve.tolist() if is_valid(curve) else [None] * pdp_grid,
            "support": [lo, hi],
        })

        width = hi - lo
        wide = np.linspace(lo - extrapolation_factor * width, hi + extrapolation_factor * width, pdp_grid * 2)
        wide_base = np.tile(np.mean(X_train, axis=0), (len(wide), 1))
        wide_base[:, j] = wide
        wide_curve = evaluate(root, wide_base)
        finite_mask = np.isfinite(wide_curve)
        extrapolation.append({
            "var": key,
            "grid": wide.tolist(),
            "support": [lo, hi],
            "y": np.where(finite_mask, wide_curve, np.nan).tolist(),
            "n_nonfinite": int(np.sum(~finite_mask)),
        })

    term_contributions = _term_contribution_series(root, X_all, max_points=max_parity_points)

    return {
        "parity": parity,
        "pdp": pdp,
        "extrapolation": extrapolation,
        "term_contributions": term_contributions,
    }


def _term_contribution_series(root: Node, X: np.ndarray, *, max_points: int) -> dict:
    terms = top_level_terms(root)
    prediction = evaluate(root, X)
    if not is_valid(prediction):
        return {"sort_key": "y_pred", "order": [], "terms": []}
    order = np.argsort(prediction)
    stride = max(1, len(order) // max_points)
    order = order[::stride]
    series = []
    for term_id, term in enumerate(terms):
        values = evaluate(term, X)
        series.append({
            "term_id": term_id,
            "values": (values[order] if is_valid(values) else np.zeros(len(order))).tolist(),
        })
    return {"sort_key": "y_pred", "order": order.tolist(), "terms": series}


# --------------------------------------------------------------------------------------------
# 6.1 the run document
# --------------------------------------------------------------------------------------------


def run_payload(
    *,
    run_id: str,
    dataset: dict,
    engine: dict,
    pareto: list[dict],
    selected_index: int,
    history: dict | None = None,
    validation: dict | None = None,
    notes: dict | None = None,
) -> dict:
    """Assemble one run document and round every float on the way out."""
    payload = {
        "schema_version": SCHEMA_VERSION,
        "run_id": run_id,
        "dataset": dataset,
        "engine": engine,
        "pareto": pareto,
        "selected_index": selected_index,
        "history": history or {},
        "validation": validation or {},
        "notes": notes or {},
    }
    return _round_floats(payload)


def dataset_descriptor(
    X: np.ndarray,
    y: np.ndarray,
    *,
    name: str,
    input_keys: Sequence[str],
    input_display: Sequence[str] | None = None,
    input_units: Sequence[str] | None = None,
    input_dims: Sequence[Dims] | None = None,
    target_key: str = "y",
    target_display: str = "y",
    target_unit: str = "1",
    target_dims: Dims = DIMENSIONLESS,
    real_or_synthetic: str = "synthetic",
    source: str | None = None,
    license_note: str | None = None,
) -> dict:
    """The dataset block of the run document, including provenance.

    `source` and `license_note` are not optional in practice: every case in this lab either names a
    fetchable source with its licence, or is a generator whose governing equation is published in the
    docs. A dataset block with neither is a defect the case review is meant to catch.
    """
    inputs = []
    for j, key in enumerate(input_keys):
        column = X[:, j]
        inputs.append({
            "key": key,
            "display": (input_display[j] if input_display else key),
            "unit": (input_units[j] if input_units else "1"),
            "dims": list(input_dims[j]) if input_dims else list(DIMENSIONLESS),
            "min": float(np.min(column)),
            "max": float(np.max(column)),
            "mean": float(np.mean(column)),
            "std": float(np.std(column)),
        })
    return {
        "name": name,
        "n_rows": int(X.shape[0]),
        "n_inputs": int(X.shape[1]),
        "real_or_synthetic": real_or_synthetic,
        "source": source,
        "license": license_note,
        "inputs": inputs,
        "target": {
            "key": target_key,
            "display": target_display,
            "unit": target_unit,
            "dims": list(target_dims),
            "min": float(np.min(y)),
            "max": float(np.max(y)),
            "mean": float(np.mean(y)),
            "std": float(np.std(y)),
        },
    }


# --------------------------------------------------------------------------------------------
# small shared statistics
# --------------------------------------------------------------------------------------------


def _mse(y: np.ndarray, y_pred: np.ndarray) -> float:
    if not is_valid(y_pred):
        return float("inf")
    return float(np.mean((y - y_pred) ** 2))


def _r2(y: np.ndarray, y_pred: np.ndarray) -> float:
    if not is_valid(y_pred):
        return float("-inf")
    variance = float(np.var(y))
    if variance <= 0:
        return float("nan")
    return float(1.0 - np.mean((y - y_pred) ** 2) / variance)
