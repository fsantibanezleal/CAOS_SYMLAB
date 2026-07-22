"""Tests for the shared expression core.

These are behaviour tests for the properties the rest of the lab relies on, not coverage padding.
Each one corresponds to a decision recorded in the research dossiers, and a failure here means a
published number would be wrong rather than that a refactor moved a line.
"""
from __future__ import annotations

import math

import numpy as np
import pytest

from symlab.model import complexity as cx
from symlab.model import intervals, latex, scaling, units
from symlab.model.expr import (
    PRIMITIVE_SETS,
    Node,
    canonical_key,
    constants,
    count_operators,
    depth,
    evaluate,
    is_valid,
    n_constants,
    parent_map,
    semantic_key,
    set_constants,
    size,
    to_infix,
    top_level_terms,
    variables_used,
    walk,
)


@pytest.fixture()
def sample_expression() -> Node:
    """2.31 * x0 * sin(x1 + 0.5 * x2) + 0.44"""
    return Node.call(
        "add",
        Node.call(
            "mul",
            Node.const(2.31),
            Node.call(
                "mul",
                Node.var(0),
                Node.call("sin", Node.call("add", Node.var(1), Node.call("mul", Node.const(0.5), Node.var(2)))),
            ),
        ),
        Node.const(0.44),
    )


@pytest.fixture()
def sample_data() -> np.ndarray:
    return np.random.default_rng(20260721).uniform(-2.0, 2.0, size=(256, 3))


# --------------------------------------------------------------------------------------------
# Representation
# --------------------------------------------------------------------------------------------


def test_size_and_depth(sample_expression: Node) -> None:
    assert size(sample_expression) == 12
    assert depth(sample_expression) == 7


def test_node_ids_are_preorder_and_parents_agree(sample_expression: Node) -> None:
    """The shared id space is a contract requirement: the LaTeX annotation, the flat node list and
    the term references must all index the same pre-order walk."""
    nodes = list(walk(sample_expression))
    parents = parent_map(sample_expression)
    assert len(parents) == len(nodes)
    assert parents[0] is None
    for node_id, parent_id in parents.items():
        if parent_id is not None:
            assert parent_id < node_id, "a parent must precede its child in pre-order"


def test_arity_is_enforced() -> None:
    with pytest.raises(ValueError):
        Node.call("add", Node.var(0))


def test_variables_used_reports_only_what_is_read() -> None:
    """The feature-selection finding is only measurable if unused inputs are countable."""
    expression = Node.call("add", Node.var(0), Node.const(1.0))
    assert variables_used(expression) == {0}


# --------------------------------------------------------------------------------------------
# Evaluation and the no-protected-operators decision
# --------------------------------------------------------------------------------------------


def test_evaluate_matches_numpy(sample_expression: Node, sample_data: np.ndarray) -> None:
    expected = 2.31 * sample_data[:, 0] * np.sin(sample_data[:, 1] + 0.5 * sample_data[:, 2]) + 0.44
    np.testing.assert_allclose(evaluate(sample_expression, sample_data), expected, rtol=1e-12)


def test_division_by_zero_is_not_protected() -> None:
    """Protected division would return a finite value here and silently change the function.

    The lab's position, from Keijzer, is that the candidate must be rejected instead.
    """
    expression = Node.call("div", Node.const(1.0), Node.var(0))
    X = np.array([[0.0], [1.0]])
    values = evaluate(expression, X)
    assert not is_valid(values)


def test_log_of_negative_is_not_protected() -> None:
    values = evaluate(Node.call("log", Node.var(0)), np.array([[-1.0]]))
    assert not is_valid(values)


# --------------------------------------------------------------------------------------------
# Constants
# --------------------------------------------------------------------------------------------


def test_constant_round_trip(sample_expression: Node) -> None:
    original = constants(sample_expression)
    assert original == [2.31, 0.5, 0.44]
    rewritten = set_constants(sample_expression, [1.0, 2.0, 3.0])
    assert constants(rewritten) == [1.0, 2.0, 3.0]
    assert constants(sample_expression) == original, "the original tree must be untouched"
    assert n_constants(rewritten) == 3


# --------------------------------------------------------------------------------------------
# Deduplication
# --------------------------------------------------------------------------------------------


def test_canonical_key_is_commutative_where_the_operator_is() -> None:
    assert canonical_key(Node.call("add", Node.var(0), Node.var(1))) == canonical_key(
        Node.call("add", Node.var(1), Node.var(0))
    )
    assert canonical_key(Node.call("mul", Node.var(0), Node.var(1))) == canonical_key(
        Node.call("mul", Node.var(1), Node.var(0))
    )


def test_canonical_key_is_not_commutative_where_the_operator_is_not() -> None:
    assert canonical_key(Node.call("sub", Node.var(0), Node.var(1))) != canonical_key(
        Node.call("sub", Node.var(1), Node.var(0))
    )


def test_semantic_key_collapses_all_invalid_candidates(sample_data: np.ndarray) -> None:
    invalid = np.array([np.inf, 1.0, 2.0])
    assert semantic_key(invalid) == "invalid"


# --------------------------------------------------------------------------------------------
# Units
# --------------------------------------------------------------------------------------------


def test_transcendental_of_a_dimensional_quantity_is_rejected() -> None:
    verdict = units.check(Node.call("sin", Node.var(0)), [units.dims(m=1)], units.DIMENSIONLESS)
    assert not verdict.ok
    assert "dimensionless" in verdict.reason


def test_adding_incompatible_dimensions_is_rejected() -> None:
    verdict = units.check(
        Node.call("add", Node.var(0), Node.var(1)),
        [units.dims(m=1), units.dims(s=1)],
        units.dims(m=1),
    )
    assert not verdict.ok


def test_product_and_quotient_compose_dimensions() -> None:
    """velocity = length / time, checked through the operator's own unit rule."""
    verdict = units.check(
        Node.call("div", Node.var(0), Node.var(1)),
        [units.dims(m=1), units.dims(s=1)],
        units.COMMON["velocity"],
    )
    assert verdict.ok


def test_sqrt_of_odd_exponents_is_refused() -> None:
    """There is no integer-exponent representation for the square root of a length, so the
    generator must refuse to build it rather than round the exponent."""
    verdict = units.infer_dims(Node.call("sqrt", Node.var(0)), [units.dims(m=1)], const_dims=units.DIMENSIONLESS)
    assert not verdict.ok


def test_format_dims_reads_as_a_unit_string() -> None:
    """Symbols come out in the fixed contract order (m, kg, s, A, K, mol, cd), so a force reads
    `m.kg.s^-2` rather than the conventional `kg.m.s^-2`. The order is what the exported `dims`
    vector uses, and consistency with the payload matters more than convention here."""
    assert units.format_dims(units.COMMON["force"]) == "m.kg.s^-2"
    assert units.format_dims(units.DIMENSIONLESS) == "1"
    assert units.DIM_SYMBOLS[0] == "m" and units.DIM_SYMBOLS[1] == "kg"


# --------------------------------------------------------------------------------------------
# Interval guards
# --------------------------------------------------------------------------------------------


def test_interval_guard_rejects_a_pole_inside_the_input_box() -> None:
    X = np.linspace(-1.0, 1.0, 50).reshape(-1, 1)
    box = intervals.from_data(X)
    assert not intervals.admissible(Node.call("inv", Node.var(0)), box)


def test_interval_guard_accepts_the_same_expression_away_from_the_pole() -> None:
    X = np.linspace(2.0, 5.0, 50).reshape(-1, 1)
    box = intervals.from_data(X)
    assert intervals.admissible(Node.call("inv", Node.var(0)), box)


def test_interval_guard_rejects_log_of_a_range_reaching_zero() -> None:
    X = np.linspace(0.0, 5.0, 50).reshape(-1, 1)
    assert not intervals.admissible(Node.call("log", Node.var(0)), intervals.from_data(X))


def test_interval_guard_rejects_exp_overflow() -> None:
    X = np.linspace(0.0, 1000.0, 10).reshape(-1, 1)
    assert not intervals.admissible(Node.call("exp", Node.var(0)), intervals.from_data(X))


def test_sin_bounds_are_sound_over_a_wide_interval() -> None:
    result = intervals.propagate(Node.call("sin", Node.var(0)), [intervals.Interval(-10.0, 10.0)])
    assert result.lo == pytest.approx(-1.0)
    assert result.hi == pytest.approx(1.0)


def test_margin_widens_the_box() -> None:
    X = np.linspace(1.0, 2.0, 10).reshape(-1, 1)
    tight = intervals.from_data(X)[0]
    wide = intervals.from_data(X, margin=0.5)[0]
    assert wide.lo < tight.lo and wide.hi > tight.hi


# --------------------------------------------------------------------------------------------
# Linear scaling
# --------------------------------------------------------------------------------------------


def test_linear_scaling_recovers_a_known_affine_relation() -> None:
    rng = np.random.default_rng(7)
    f = rng.uniform(-3.0, 3.0, size=500)
    y = 2.5 * f - 1.25
    fitted = scaling.fit(y, f)
    assert fitted.slope == pytest.approx(2.5, rel=1e-9)
    assert fitted.intercept == pytest.approx(-1.25, rel=1e-9)
    assert not fitted.degenerate


def test_linear_scaling_reports_a_degenerate_candidate() -> None:
    """A constant candidate carries no information; the lab reports that rather than scoring it as
    a fit."""
    f = np.full(100, 3.0)
    y = np.linspace(0.0, 1.0, 100)
    fitted = scaling.fit(y, f)
    assert fitted.degenerate
    assert fitted.intercept == pytest.approx(float(np.mean(y)))


def test_folding_scaling_makes_the_reported_expression_the_scored_one() -> None:
    base = Node.call("mul", Node.var(0), Node.var(1))
    folded = scaling.fold_into_expression(base, scaling.Scaling(2.0, 1.0))
    X = np.array([[3.0, 4.0]])
    assert evaluate(folded, X)[0] == pytest.approx(2.0 * 12.0 + 1.0)


def test_folding_an_identity_scaling_adds_no_complexity() -> None:
    base = Node.call("mul", Node.var(0), Node.var(1))
    assert size(scaling.fold_into_expression(base, scaling.IDENTITY)) == size(base)


# --------------------------------------------------------------------------------------------
# Complexity and model selection
# --------------------------------------------------------------------------------------------


def test_weighted_complexity_separates_what_node_count_cannot() -> None:
    """The benchmark suite's own stated weakness: node count ignores nested nonlinearity."""
    nested = Node.call("sin", Node.call("sin", Node.call("sin", Node.var(0))))
    flat = Node.call("add", Node.call("neg", Node.var(0)), Node.var(1))
    assert cx.node_count(nested) == cx.node_count(flat) == 4
    assert cx.weighted_complexity(nested) > 3 * cx.weighted_complexity(flat)


def test_description_length_decomposes_and_sums() -> None:
    rng = np.random.default_rng(3)
    y = rng.normal(size=200)
    y_pred = y + rng.normal(scale=0.1, size=200)
    expression = Node.call("add", Node.var(0), Node.const(1.0))
    dl = cx.description_length(expression, y, y_pred, n_primitives=8, n_variables=2)
    assert dl.total == pytest.approx(dl.structure + dl.constants + dl.residuals, rel=1e-9)
    assert dl.constants > 0


def test_description_length_prefers_the_simpler_of_two_equal_fits() -> None:
    rng = np.random.default_rng(11)
    y = rng.normal(size=300)
    y_pred = y.copy()
    simple = Node.call("mul", Node.var(0), Node.const(1.0))
    padded = Node.call("add", Node.call("mul", Node.var(0), Node.const(1.0)), Node.const(0.0))
    simple_dl = cx.description_length(simple, y, y_pred, n_primitives=8, n_variables=2).total
    padded_dl = cx.description_length(padded, y, y_pred, n_primitives=8, n_variables=2).total
    assert simple_dl < padded_dl


def test_pareto_front_keeps_only_non_dominated_points() -> None:
    points = [(1.0, 3.0), (0.5, 5.0), (0.6, 7.0), (0.1, 9.0)]
    assert cx.pareto_front(points) == [0, 1, 3]


def test_pareto_front_breaks_ties_at_equal_complexity() -> None:
    points = [(1.0, 5.0), (0.4, 5.0), (0.9, 5.0)]
    front = cx.pareto_front(points)
    assert front == [1]


def test_pareto_score_is_zero_for_the_first_member() -> None:
    scores = cx.pareto_score([(1.0, 3.0), (0.1, 5.0)])
    assert scores[0] == 0.0
    assert scores[1] > 0.0


# --------------------------------------------------------------------------------------------
# LaTeX rendering
# --------------------------------------------------------------------------------------------


def test_rendered_latex_never_uses_left_right(sample_expression: Node) -> None:
    """`\\left(` blocks automatic line breaking in both rendering engines, so a long discovered
    expression would overflow instead of wrapping."""
    rendered = latex.to_latex(sample_expression)
    assert "\\left" not in rendered
    assert "\\right" not in rendered


def test_annotated_latex_carries_the_shared_node_ids(sample_expression: Node) -> None:
    annotated = latex.to_latex(sample_expression, annotate=True)
    for node_id in range(size(sample_expression)):
        assert f"nid={node_id}" in annotated


def test_colour_is_a_class_not_a_baked_hex(sample_expression: Node) -> None:
    """A hex colour written in Python is unreadable in one of the two themes."""
    terms = latex.term_assignment(sample_expression)
    annotated = latex.to_latex(sample_expression, annotate=True, term_of_node=terms)
    assert "\\htmlClass{sym-term-" in annotated
    assert "\\textcolor" not in annotated


def test_number_formatting_never_leaks_float_noise() -> None:
    assert latex.format_number(0.1 + 0.2) == "0.3"
    assert latex.format_number(3.0) == "3"
    assert latex.format_number(0.0) == "0"
    assert "10^{" in latex.format_number(1.2e-9)


def test_precedence_parenthesises_only_where_needed() -> None:
    expression = Node.call("mul", Node.call("add", Node.var(0), Node.var(1)), Node.var(2))
    rendered = latex.to_latex(expression)
    assert rendered.startswith("(")
    flat = Node.call("add", Node.call("mul", Node.var(0), Node.var(1)), Node.var(2))
    assert "(" not in latex.to_latex(flat)


def test_rounding_reports_the_error_it_introduced(sample_expression: Node, sample_data: np.ndarray) -> None:
    _, report = latex.round_constants(sample_expression, sample_data, sig_digits=4)
    assert report.accepted
    assert report.max_rel_error >= 0.0


def test_rounding_is_refused_when_it_would_change_the_model() -> None:
    """Precision traded for readability must be measured, and refused when it costs too much."""
    expression = Node.call("exp", Node.call("mul", Node.const(12.3456789), Node.var(0)))
    X = np.linspace(1.0, 4.0, 50).reshape(-1, 1)
    _, report = latex.round_constants(expression, X, sig_digits=2, tolerance=1e-9)
    assert not report.accepted


def test_downgrade_left_right_strips_foreign_delimiters() -> None:
    assert latex.downgrade_left_right("\\sin\\left(x\\right)") == "\\sin(x)"


def test_aligned_form_breaks_a_multi_term_sum() -> None:
    expression = Node.call("add", Node.call("add", Node.var(0), Node.var(1)), Node.var(2))
    aligned = latex.aligned_latex(expression)
    assert "\\begin{aligned}" in aligned
    assert "\\\\" in aligned


# --------------------------------------------------------------------------------------------
# Term decomposition
# --------------------------------------------------------------------------------------------


def test_top_level_terms_splits_a_sum(sample_expression: Node) -> None:
    terms = top_level_terms(sample_expression)
    assert len(terms) == 2


def test_subtraction_becomes_a_negated_term() -> None:
    expression = Node.call("sub", Node.var(0), Node.var(1))
    terms = top_level_terms(expression)
    assert len(terms) == 2
    X = np.array([[5.0, 2.0]])
    assert evaluate(terms[1], X)[0] == pytest.approx(-2.0)


def test_operator_counts(sample_expression: Node) -> None:
    counts = count_operators(sample_expression)
    assert counts["mul"] == 3
    assert counts["sin"] == 1


# --------------------------------------------------------------------------------------------
# Primitive sets
# --------------------------------------------------------------------------------------------


def test_primitive_sets_are_named_and_non_empty() -> None:
    """A manifest records which primitives a run was allowed, because two engines given different
    primitive sets were not solving the same problem."""
    for name, ops in PRIMITIVE_SETS.items():
        assert ops, f"primitive set {name} is empty"
        assert len(set(ops)) == len(ops), f"primitive set {name} has duplicates"


def test_infix_is_readable(sample_expression: Node) -> None:
    text = to_infix(sample_expression, ["a", "b", "c"])
    assert "sin" in text and "a" in text
    assert math.isfinite(2.31)


def test_reciprocal_unit_rule_respects_arity() -> None:
    """The `sub` unit rule is shared by the binary quotient and the UNARY reciprocal.

    Indexing the second child unconditionally raised an IndexError on `inv`, which surfaced on the
    pump-affinity case where reciprocals are exactly what the physics calls for. A reciprocal
    negates the exponents.
    """
    verdict = units.infer_dims(Node.call("inv", Node.var(0)), [units.dims(s=1)])
    assert verdict.ok
    assert verdict.dims == units.dims(s=-1)


def test_reciprocal_of_a_frequency_is_a_time() -> None:
    verdict = units.check(
        Node.call("inv", Node.var(0)), [units.COMMON["frequency"]], units.COMMON["time"]
    )
    assert verdict.ok
