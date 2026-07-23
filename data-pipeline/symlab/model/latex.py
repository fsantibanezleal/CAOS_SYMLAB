"""Rendering an expression as readable mathematics, with a stable node identity in the markup.

Three things make this harder than calling a printer and shipping the string, and all three came out
of the persisted visualization research:

1. **The equation must be addressable.** Hovering a term in the rendered equation has to highlight
   the same subtree in the tree view and the same band in the contribution chart. That works only if
   the rendered markup carries the node id, which is what `\\htmlData{nid=N}{...}` does. The ids come
   from the same pre-order walk as the exported flat node list, so the three views cannot drift.

2. **`\\left(` and `\\right)` must be avoided.** They are the reflexive way to size delimiters, and
   they block automatic line breaking in BOTH rendering engines. A long discovered expression then
   overflows its container instead of wrapping. This module emits plain delimiters and provides
   `downgrade_left_right` for any LaTeX arriving from elsewhere.

3. **Colour cannot be baked in.** Writing `\\textcolor{#1f77b4}` in Python produces an equation that
   is unreadable in one of the two themes. Colour is emitted as `\\htmlClass{sym-term-N}` and
   resolved by CSS custom properties in the browser, so it follows the theme. The class index is
   assigned here, in Python, because the same ordering feeds the equation, the tree and the stacked
   area chart, and three independent orderings would eventually disagree.

Constant rounding is treated as a measurement, not a formatting choice: `round_constants` reports
the maximum relative error the rounding introduced across the evaluation rows, so the UI can state
how much precision was traded for readability rather than implying none was.
"""
from __future__ import annotations

import math
import re
from dataclasses import dataclass

import numpy as np

from .expr import (
    KIND_CONST,
    KIND_OP_BINARY,
    KIND_VAR,
    Node,
    constants,
    evaluate,
    is_valid,
    set_constants,
    top_level_terms,
    walk,
)

# Binding power, higher binds tighter. Used to decide when a child needs delimiters.
_PRECEDENCE: dict[str, int] = {
    "add": 1,
    "sub": 1,
    "mul": 2,
    "div": 3,     # rendered as a fraction, so its children never need delimiters
    "neg": 2,
    "square": 4,
    "sqrt": 5,
    "exp": 5,
    "log": 5,
    "sin": 5,
    "cos": 5,
    "tanh": 5,
    "inv": 3,
    "abs": 5,
}

_ATOM = 10


def format_number(value: float, *, sig_digits: int = 4) -> str:
    """Render a constant the way a paper would, not the way a float repr does.

    Integers stay integers, scientific notation is used only when the magnitude demands it, and
    trailing zeros are trimmed. `0.30000000000000004` never reaches the browser.
    """
    if not math.isfinite(value):
        return "\\mathrm{NaN}" if math.isnan(value) else ("\\infty" if value > 0 else "-\\infty")
    if value == 0.0:
        return "0"
    if float(value).is_integer() and abs(value) < 1e6:
        return str(int(value))
    magnitude = abs(value)
    if magnitude >= 1e5 or magnitude < 1e-4:
        mantissa, exponent = f"{value:.{max(0, sig_digits - 1)}e}".split("e")
        mantissa = mantissa.rstrip("0").rstrip(".")
        return f"{mantissa} \\times 10^{{{int(exponent)}}}"
    text = f"{value:.{sig_digits}g}"
    if "e" in text or "E" in text:
        mantissa, exponent = re.split("[eE]", text)
        mantissa = mantissa.rstrip("0").rstrip(".")
        return f"{mantissa} \\times 10^{{{int(exponent)}}}"
    if "." in text:
        text = text.rstrip("0").rstrip(".")
    return text


#: A plain identifier with at most one underscore-subscript. These render correctly as bare LaTeX
#: (`mu`, `T_amb`, `V_1`), so they are left alone; everything else raw is escaped into \mathrm{}.
_SIMPLE_IDENTIFIER = re.compile(r"^[A-Za-z][A-Za-z0-9]*(_[A-Za-z0-9]+)?$")

#: LaTeX specials that must be escaped when a raw name is set as upright text.
_LATEX_ESCAPE = {
    "%": r"\%", "#": r"\#", "&": r"\&", "$": r"\$",
    "_": r"\_", "{": r"\{", "}": r"\}",
    "~": r"\textasciitilde{}", "^": r"\textasciicircum{}",
}


def latexify_name(name: str) -> str:
    """Make a display name safe and readable inside a LaTeX string.

    Mirrors `frontend/src/lib/latex.ts :: latexSafeName`. A raw data-column name like
    `%_Silica_Concentrate` or `Flotation_Column_03_Air_Flow` is escaped and set upright rather than
    interpreted as a run of subscripts (or, for a leading `%`, a comment that blanks the equation).
    """
    if "\\" in name:
        return name
    if _SIMPLE_IDENTIFIER.match(name):
        return name
    escaped = "".join(_LATEX_ESCAPE.get(char, char) for char in name)
    return f"\\mathrm{{{escaped}}}"


def variable_latex(index: int, display_names: list[str] | None = None) -> str:
    """A variable's rendered symbol. Case definitions supply real symbols (`\\theta`, `T_{in}`);
    real-data loaders supply raw column names, which are made LaTeX-safe here."""
    if display_names and index < len(display_names):
        return latexify_name(display_names[index])
    return f"x_{{{index}}}"


@dataclass
class _Renderer:
    display_names: list[str] | None
    sig_digits: int
    annotate: bool
    term_of_node: dict[int, int]
    counter: int = 0

    def render(self, node: Node, parent_precedence: int = 0) -> str:
        node_id = self.counter
        self.counter += 1
        body = self._body(node, node_id)
        precedence = _ATOM if node.is_leaf else _PRECEDENCE.get(str(node.op), 2)
        if precedence < parent_precedence:
            body = f"({body})"
        if self.annotate:
            term = self.term_of_node.get(node_id)
            if term is not None:
                body = f"\\htmlClass{{sym-term-{term}}}{{{body}}}"
            body = f"\\htmlData{{nid={node_id}}}{{{body}}}"
        return body

    def _body(self, node: Node, node_id: int) -> str:
        if node.kind == KIND_CONST:
            return format_number(float(node.value), sig_digits=self.sig_digits)  # type: ignore[arg-type]
        if node.kind == KIND_VAR:
            return variable_latex(int(node.var_index), self.display_names)  # type: ignore[arg-type]

        op = str(node.op)
        precedence = _PRECEDENCE.get(op, 2)

        if op == "add":
            left = self.render(node.children[0], precedence)
            right = self.render(node.children[1], precedence)
            return f"{left} + {right}"
        if op == "sub":
            left = self.render(node.children[0], precedence)
            right = self.render(node.children[1], precedence + 1)
            return f"{left} - {right}"
        if op == "mul":
            left = self.render(node.children[0], precedence)
            right = self.render(node.children[1], precedence)
            return f"{left} \\cdot {right}"
        if op == "div":
            # A fraction brings its own grouping, so children render at precedence 0.
            numerator = self.render(node.children[0], 0)
            denominator = self.render(node.children[1], 0)
            return f"\\frac{{{numerator}}}{{{denominator}}}"
        if op == "inv":
            return f"\\frac{{1}}{{{self.render(node.children[0], 0)}}}"
        if op == "neg":
            return f"-{self.render(node.children[0], precedence + 1)}"
        if op == "square":
            return f"{self.render(node.children[0], _ATOM)}^{{2}}"
        if op == "sqrt":
            return f"\\sqrt{{{self.render(node.children[0], 0)}}}"
        if op == "abs":
            return f"\\lvert {self.render(node.children[0], 0)} \\rvert"
        if op == "exp":
            return f"e^{{{self.render(node.children[0], 0)}}}"
        if op in ("log", "sin", "cos", "tanh"):
            name = {"log": "\\ln", "sin": "\\sin", "cos": "\\cos", "tanh": "\\tanh"}[op]
            # Plain delimiters on purpose: \left( ... \right) would block line breaking.
            return f"{name}({self.render(node.children[0], 0)})"
        return f"\\mathrm{{{op}}}({', '.join(self.render(c, 0) for c in node.children)})"


def to_latex(
    node: Node,
    *,
    display_names: list[str] | None = None,
    sig_digits: int = 4,
    annotate: bool = False,
    term_of_node: dict[int, int] | None = None,
) -> str:
    """Render the expression.

    `annotate=False` produces the plain string (`latex_raw` in the exported contract).
    `annotate=True` produces the addressable string (`latex_pretty`), carrying node ids and, where
    `term_of_node` supplies them, per-term colour classes.
    """
    renderer = _Renderer(
        display_names=display_names,
        sig_digits=sig_digits,
        annotate=annotate,
        term_of_node=term_of_node or {},
    )
    return renderer.render(node, 0)


def term_assignment(root: Node) -> dict[int, int]:
    """Map every node id to the index of the top-level additive term it belongs to.

    Nodes above the term split (the `+` spine itself) map to nothing, which is why the returned dict
    is partial rather than covering the whole id space.
    """
    ids_in_preorder = list(range(sum(1 for _ in walk(root))))
    del ids_in_preorder  # the walk below assigns ids directly

    out: dict[int, int] = {}
    counter = 0
    terms = top_level_terms(root)
    term_roots = {id(t): i for i, t in enumerate(terms)}

    def visit(node: Node, current_term: int | None) -> None:
        nonlocal counter
        my_id = counter
        counter += 1
        term = term_roots.get(id(node), current_term)
        if term is not None:
            out[my_id] = term
        for child in node.children:
            visit(child, term)

    visit(root, None)
    return out


def downgrade_left_right(latex: str) -> str:
    """Strip `\\left` and `\\right` so long expressions can wrap.

    Applied to any LaTeX produced outside this module, for example by a third-party engine's own
    printer, before it is shown.
    """
    return re.sub(r"\\left(?=[([|.])", "", re.sub(r"\\right(?=[)\]|.])", "", latex))


@dataclass(frozen=True)
class RoundingReport:
    """What rounding the constants actually cost, measured rather than assumed."""

    sig_digits: int
    max_rel_error: float
    accepted: bool


def round_constants(
    node: Node,
    X: np.ndarray,
    *,
    sig_digits: int = 4,
    tolerance: float = 1e-3,
) -> tuple[Node, RoundingReport]:
    """Round every constant to `sig_digits`, then measure the damage on the actual rows.

    The rounded expression is accepted only when the maximum relative deviation stays within
    `tolerance`. Otherwise the original constants are kept and the report says so, so the UI can
    show full precision instead of a prettier expression that is quietly a different model.
    """
    original_values = evaluate(node, X)
    if not is_valid(original_values):
        return node, RoundingReport(sig_digits, float("nan"), False)

    def _round(value: float) -> float:
        if value == 0.0 or not math.isfinite(value):
            return value
        exponent = math.floor(math.log10(abs(value)))
        factor = 10 ** (sig_digits - 1 - exponent)
        return round(value * factor) / factor

    rounded_node = set_constants(node, [_round(c) for c in constants(node)])
    rounded_values = evaluate(rounded_node, X)
    if not is_valid(rounded_values):
        return node, RoundingReport(sig_digits, float("inf"), False)

    denominator = np.maximum(np.abs(original_values), 1e-12)
    max_rel_error = float(np.max(np.abs(rounded_values - original_values) / denominator))
    if max_rel_error <= tolerance:
        return rounded_node, RoundingReport(sig_digits, round(max_rel_error, 12), True)
    return node, RoundingReport(sig_digits, round(max_rel_error, 12), False)


def aligned_latex(root: Node, *, display_names: list[str] | None = None, target: str = "y",
                  sig_digits: int = 4, max_terms_per_line: int = 1) -> str:
    """An `aligned` environment that breaks a long sum across lines at its top-level terms.

    This is the readable form for an expression with many additive terms. It is emitted in addition
    to, never instead of, the single-line form.
    """
    terms = top_level_terms(root)
    if len(terms) <= 1:
        return f"{target} = {to_latex(root, display_names=display_names, sig_digits=sig_digits)}"
    rendered = [to_latex(t, display_names=display_names, sig_digits=sig_digits) for t in terms]
    lines = [f"{target} &= {rendered[0]}"]
    for i in range(1, len(rendered), max_terms_per_line):
        chunk = rendered[i : i + max_terms_per_line]
        joined = " + ".join(chunk)
        lines.append(f"&\\quad + {joined}")
    body = " \\\\ ".join(lines)
    return f"\\begin{{aligned}} {body} \\end{{aligned}}"


def node_kind_label(node: Node, display_names: list[str] | None = None) -> str:
    """The short label the tree view prints inside a node."""
    if node.kind == KIND_CONST:
        return format_number(float(node.value), sig_digits=3)  # type: ignore[arg-type]
    if node.kind == KIND_VAR:
        index = int(node.var_index)  # type: ignore[arg-type]
        if display_names and index < len(display_names):
            return display_names[index]
        return f"x{index}"
    symbols = {
        "add": "+", "sub": "-", "mul": "*", "div": "/", "neg": "-", "square": "^2",
        "sqrt": "sqrt", "exp": "exp", "log": "ln", "sin": "sin", "cos": "cos",
        "tanh": "tanh", "inv": "1/x", "abs": "abs",
    }
    return symbols.get(str(node.op), str(node.op))


def is_binary(node: Node) -> bool:
    return node.kind == KIND_OP_BINARY
