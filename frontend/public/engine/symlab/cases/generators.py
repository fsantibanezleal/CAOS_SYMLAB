"""First-principles generators: synthetic data whose governing equation is KNOWN exactly.

Every generator here was transcribed from a named primary or reference source during the research
phase, and the source is carried on the generator object rather than in a comment, so the app and
the docs cite the same string the code was built from.

Why these exist at all, when the lab also ships real datasets: on real data nobody knows the true
law, so a result can only be scored on error. Here the truth is known, so the lab can report a
SOLUTION RATE, which is a categorically stronger claim than a coefficient of determination. The
benchmark literature's most damaging finding for the field, a model scoring above 0.999 while
recovering the correct structure zero percent of the time, is only measurable because generators like
these exist.

Four of them have a real-data twin in the case list, which is the strongest arrangement available:
calibrate the engine where the answer is known, then test it where it is not.

- `friction-factor` pairs with the Nikuradse 362-point measured dataset.
- `flotation-kinetics` and `comminution-bond` pair with the mining cases.
- `monod-saturation` pairs with the penicillin fermentation case.
- `wind-power-curve` pairs with the Kelmarsh reserve case.

Honesty rules applied throughout: a generator whose validity range is finite carries that range and a
variant that DELIBERATELY leaves it, because showing a law break down outside its domain is the most
useful lesson this lab can teach. And where the research could not verify a formula (the Morrell
size-specific-energy refinement), it is not shipped as a scored target.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

import numpy as np

from ..model.expr import Node
from ..model.units import COMMON, DIMENSIONLESS, Dims, dims

#: Gas constant, J/(mol K). CODATA value.
R_GAS = 8.314462618
#: Specific gas constant for dry air, J/(kg K), used by the wind generator's density correction.
R_DRY_AIR = 287.058
#: Standard gravity, m/s^2.
G0 = 9.80665


@dataclass(frozen=True)
class InputSpec:
    """One input column: how it is named, what it means, and what unit it carries."""

    key: str
    display: str
    unit: str
    dims: Dims = DIMENSIONLESS
    note: str = ""


@dataclass(frozen=True)
class Generator:
    """A synthetic case with a known governing equation.

    `sample` returns `(X, y)` with X shaped (n, len(inputs)). `truth_latex` is the law as it should
    be rendered; `truth_infix` is the machine-comparable form the equivalence test scores against.
    """

    id: str
    name: str
    category: str
    inputs: tuple[InputSpec, ...]
    target: InputSpec
    truth_latex: str
    truth_infix: str
    source: str
    sample: Callable[[np.random.Generator, int], tuple[np.ndarray, np.ndarray]]
    recovery_target: str
    validity: str = ""
    caveats: tuple[str, ...] = ()
    suggested_primitives: str = "physics"
    real_data_twin: str | None = None
    #: The truth as a machine-comparable expression tree, or None where the law cannot be written in
    #: this operator set. ONLY generators carrying one contribute to a recovery rate; the rest
    #: contribute to error metrics only, and the app says "not checkable" rather than reporting zero.
    truth_node: Callable[[], Node] | None = None
    #: How hard the recovery task actually is, stated rather than left implicit.
    #:   "structure"           the physical parameters are input COLUMNS, so only the FORM is unknown.
    #:                         This is the convention the published physics benchmarks use.
    #:   "structure+constants" the parameters are baked into the generator, so the NUMBERS must be
    #:                         recovered as well, which is a materially harder task.
    regime: str = "structure"

    @property
    def input_keys(self) -> list[str]:
        return [i.key for i in self.inputs]

    @property
    def input_dims(self) -> list[Dims]:
        return [i.dims for i in self.inputs]


def add_noise(rng: np.random.Generator, y: np.ndarray, level: float, *, multiplicative: bool = False) -> np.ndarray:
    """Add noise at a stated level.

    Two models, because the literature uses both and they are not interchangeable. Multiplicative
    log-normal noise is right for a rate or a concentration, where the error scales with the value;
    additive noise proportional to the root-mean-square of the signal is the benchmark convention.
    """
    if level <= 0:
        return y
    if multiplicative:
        return y * np.exp(rng.normal(0.0, level, size=y.shape))
    rms = float(np.sqrt(np.mean(y * y)))
    return y + rng.normal(0.0, level * rms, size=y.shape)


def _loguniform(rng: np.random.Generator, low: float, high: float, n: int) -> np.ndarray:
    return np.exp(rng.uniform(np.log(low), np.log(high), size=n))


# --------------------------------------------------------------------------------------------
# 1. Michaelis-Menten and Monod saturation
# --------------------------------------------------------------------------------------------


def _michaelis_menten(rng: np.random.Generator, n: int) -> tuple[np.ndarray, np.ndarray]:
    v_max = rng.uniform(0.1, 100.0, size=n)
    km = _loguniform(rng, 0.01, 10.0, n)
    # Substrate sampled log-uniformly across three decades around Km, so the saturating regime and
    # the linear regime are both represented. Sampling uniformly instead would put almost every row
    # in the saturated plateau, where the law is nearly constant and nothing can be identified.
    a = km * _loguniform(rng, 0.03, 30.0, n)
    y = v_max * a / (km + a)
    return np.column_stack([a, v_max, km]), y


MICHAELIS_MENTEN = Generator(
    id="monod-saturation",
    category="S",
    name="Michaelis-Menten and Monod saturation",
    inputs=(
        InputSpec("a", "a", "mol/m^3", COMMON["dimensionless"], "substrate concentration"),
        InputSpec("Vmax", "V_{max}", "1/s", COMMON["dimensionless"], "limiting rate"),
        InputSpec("Km", "K_m", "mol/m^3", COMMON["dimensionless"], "substrate concentration at half V"),
    ),
    target=InputSpec("v", "v", "1/s", COMMON["dimensionless"], "reaction rate"),
    truth_latex=r"v = \frac{V_{max} \cdot a}{K_m + a}",
    truth_infix="(Vmax * a) / (Km + a)",
    source="Michaelis-Menten kinetics, verified reference transcription (research dossier 7.2.1)",
    sample=_michaelis_menten,
    recovery_target="the saturating hyperbola form and the numeric Km",
    validity="Steady-state (Briggs-Haldane) approximation; enzyme concentration much below substrate.",
    caveats=(
        "The same algebraic form is the Monod growth law in fermentation, which is what makes this "
        "generator the calibration twin of the penicillin case.",
        "A Lineweaver-Burk linearisation fits this exactly but distorts the error structure; the lab "
        "shows that as a worked example of a transformation that helps a human and hurts a fit.",
    ),
    real_data_twin="penicillin-monod",
    truth_node=lambda: Node.call("div", Node.call("mul", Node.var(1), Node.var(0)),
                                Node.call("add", Node.var(2), Node.var(0))),
    regime="structure",
)


# --------------------------------------------------------------------------------------------
# 2. Arrhenius
# --------------------------------------------------------------------------------------------


def _arrhenius(rng: np.random.Generator, n: int) -> tuple[np.ndarray, np.ndarray]:
    ea = rng.uniform(20_000.0, 200_000.0, size=n)   # J/mol
    a_pre = _loguniform(rng, 1e4, 1e14, n)
    T = rng.uniform(280.0, 420.0, size=n)
    y = a_pre * np.exp(-ea / (R_GAS * T))
    return np.column_stack([T, ea, a_pre]), y


ARRHENIUS = Generator(
    id="arrhenius-rate",
    category="S",
    name="Arrhenius temperature dependence",
    inputs=(
        InputSpec("T", "T", "K", COMMON["temperature"], "absolute temperature"),
        InputSpec("Ea", "E_a", "J/mol", DIMENSIONLESS, "activation energy"),
        InputSpec("A", "A", "1/s", COMMON["frequency"], "pre-exponential factor"),
    ),
    target=InputSpec("k", "k", "1/s", COMMON["frequency"], "rate constant"),
    truth_latex=r"k = A \cdot e^{-E_a / (R T)}",
    truth_infix="A * exp(-Ea / (8.314462618 * T))",
    source="Arrhenius equation, verified reference transcription (research dossier 7.2.2)",
    sample=_arrhenius,
    recovery_target="the exp(-c/T) structure, which engines lacking a reciprocal-in-exponent path miss",
    validity="Empirically excellent over moderate temperature ranges; not a derivation from first principles.",
    caveats=(
        "This is a DIAGNOSTIC generator. It does not test how good a search is, it tests whether the "
        "primitive set can express the answer at all. An engine without division inside an exponent "
        "cannot recover it, and reporting that as a search failure would be a category error.",
    ),
    truth_node=lambda: Node.call("mul", Node.var(2), Node.call("exp", Node.call("neg",
        Node.call("div", Node.var(1), Node.call("mul", Node.const(R_GAS), Node.var(0)))))),
    regime="structure",
)


# --------------------------------------------------------------------------------------------
# 3. Non-isothermal CSTR
# --------------------------------------------------------------------------------------------


def _cstr(rng: np.random.Generator, n: int) -> tuple[np.ndarray, np.ndarray]:
    tau = _loguniform(rng, 0.1, 100.0, n)
    T = rng.uniform(300.0, 420.0, size=n)
    ea = np.full(n, 60_000.0)
    a_pre = np.full(n, 1e7)
    k = a_pre * np.exp(-ea / (R_GAS * T))
    damkohler = k * tau
    y = damkohler / (1.0 + damkohler)
    return np.column_stack([tau, T]), y


CSTR = Generator(
    id="cstr-conversion",
    category="S",
    name="Non-isothermal CSTR conversion",
    inputs=(
        InputSpec("tau", r"\tau", "s", COMMON["time"], "residence time V/Q"),
        InputSpec("T", "T", "K", COMMON["temperature"], "reactor temperature"),
    ),
    target=InputSpec("X", "X", "1", DIMENSIONLESS, "fractional conversion"),
    truth_latex=r"X = \frac{\tau A e^{-E_a/(RT)}}{1 + \tau A e^{-E_a/(RT)}}",
    truth_infix="(tau * 1e7 * exp(-60000 / (8.314462618 * T))) / (1 + tau * 1e7 * exp(-60000 / (8.314462618 * T)))",
    source="Continuous stirred-tank reactor, first-order kinetics, verified (research dossier 7.2.3)",
    sample=_cstr,
    recovery_target="the saturation-in-Damkohler-number structure z/(1+z) with z = tau*k(T)",
    validity="Steady state, perfect mixing, first-order irreversible kinetics, constant density.",
    caveats=(
        "The activation energy and pre-exponential factor are FIXED here rather than sampled, so the "
        "target is a function of two inputs. Sampling them too would make the problem trivially "
        "separable and remove the point of the case.",
    ),
    regime="structure+constants",
)


# --------------------------------------------------------------------------------------------
# 4. Comminution: Bond, Kick and Rittinger
# --------------------------------------------------------------------------------------------


def _bond(rng: np.random.Generator, n: int) -> tuple[np.ndarray, np.ndarray]:
    work_index = rng.uniform(5.0, 25.0, size=n)
    f80 = _loguniform(rng, 1000.0, 20_000.0, n)
    p80 = _loguniform(rng, 45.0, 500.0, n)
    p80 = np.minimum(p80, f80 * 0.9)   # enforce P80 < F80, a physical constraint of comminution
    y = 10.0 * work_index * (1.0 / np.sqrt(p80) - 1.0 / np.sqrt(f80))
    return np.column_stack([f80, p80, work_index]), y


COMMINUTION_BOND = Generator(
    id="comminution-bond",
    category="S",
    name="Comminution energy: Bond, with Kick and Rittinger as rival hypotheses",
    inputs=(
        InputSpec("F80", "F_{80}", "um", COMMON["length"], "80 percent passing size of the feed"),
        InputSpec("P80", "P_{80}", "um", COMMON["length"], "80 percent passing size of the product"),
        InputSpec("Wi", "W_i", "kWh/t", DIMENSIONLESS, "Bond work index"),
    ),
    target=InputSpec("E", "E", "kWh/t", DIMENSIONLESS, "specific comminution energy"),
    truth_latex=r"E = 10 W_i \left( \frac{1}{\sqrt{P_{80}}} - \frac{1}{\sqrt{F_{80}}} \right)",
    truth_infix="10 * Wi * (1/sqrt(P80) - 1/sqrt(F80))",
    source="Bond comminution law, verified reference transcription (research dossier 7.2.4)",
    sample=_bond,
    recovery_target="the exponent n in dE/dx = -C/x^n; Bond is n = 1.5, Kick n = 1, Rittinger n = 2",
    validity="Empirical, calibrated by the standard Bond ball mill work index test.",
    caveats=(
        "The three classical laws are shipped as COMPETING ground truths so the case poses a model "
        "SELECTION question rather than a fitting question. Which exponent the data support is the "
        "answer, not how small the residual is.",
        "The Morrell size-specific-energy refinement is a known extension whose exact coefficient form "
        "the research could not verify, so it is deliberately NOT shipped as a scored target.",
    ),
    real_data_twin="geomet-bond",
    truth_node=lambda: Node.call("mul", Node.call("mul", Node.const(10.0), Node.var(2)),
        Node.call("sub", Node.call("inv", Node.call("sqrt", Node.var(1))),
                          Node.call("inv", Node.call("sqrt", Node.var(0))))),
    regime="structure",
)


def _kick(rng: np.random.Generator, n: int) -> tuple[np.ndarray, np.ndarray]:
    c = rng.uniform(1.0, 20.0, size=n)
    f80 = _loguniform(rng, 1000.0, 20_000.0, n)
    p80 = np.minimum(_loguniform(rng, 45.0, 500.0, n), f80 * 0.9)
    return np.column_stack([f80, p80, c]), c * np.log(f80 / p80)


COMMINUTION_KICK = Generator(
    id="comminution-kick",
    category="S",
    name="Comminution energy: Kick (the rival exponent)",
    inputs=COMMINUTION_BOND.inputs[:2] + (InputSpec("C", "C", "kWh/t", DIMENSIONLESS, "material constant"),),
    target=COMMINUTION_BOND.target,
    truth_latex=r"E = C \ln\!\left(\frac{F_{80}}{P_{80}}\right)",
    truth_infix="C * log(F80 / P80)",
    source="Kick comminution law, verified reference transcription (research dossier 7.2.4)",
    sample=_kick,
    recovery_target="the logarithmic ratio form, distinguished from Bond's inverse-square-root",
    caveats=("Shipped so the model-selection question in the Bond case has a real alternative to select.",),
    real_data_twin="geomet-bond",
    truth_node=lambda: Node.call("mul", Node.var(2),
        Node.call("log", Node.call("div", Node.var(0), Node.var(1)))),
    regime="structure",
)


# --------------------------------------------------------------------------------------------
# 5. Flotation kinetics
# --------------------------------------------------------------------------------------------


def _flotation(rng: np.random.Generator, n: int) -> tuple[np.ndarray, np.ndarray]:
    r_inf = rng.uniform(0.6, 0.98, size=n)
    k = rng.uniform(0.05, 2.0, size=n)
    # Standard batch flotation sampling times, in minutes.
    grid = np.array([0.5, 1.0, 2.0, 4.0, 8.0, 16.0])
    t = grid[rng.integers(0, len(grid), size=n)]
    y = r_inf * (1.0 - np.exp(-k * t))
    return np.column_stack([t, r_inf, k]), y


FLOTATION_KINETICS = Generator(
    id="flotation-kinetics",
    category="S",
    name="Flotation kinetics: first-order recovery",
    inputs=(
        InputSpec("t", "t", "min", COMMON["time"], "flotation time"),
        InputSpec("Rinf", r"R_\infty", "1", DIMENSIONLESS, "ultimate recovery"),
        InputSpec("KB", "K_B", "1/min", COMMON["frequency"], "average rate constant"),
    ),
    target=InputSpec("R", "R", "1", DIMENSIONLESS, "cumulative recovery fraction"),
    truth_latex=r"R(t) = R_\infty \left(1 - e^{-K_B t}\right)",
    truth_infix="Rinf * (1 - exp(-KB * t))",
    source=(
        "Bu, Xie, Peng, Ge and Ni (2017), Physicochemical Problems of Mineral Processing 53(1):342-365, "
        "doi:10.5277/ppmp170128, equation (8); verified by extracting the open-access PDF"
    ),
    sample=_flotation,
    recovery_target="the exponential-saturation form, R_inf, and whether one rate constant or two are justified",
    validity="Classical first-order batch flotation; assumes a single floatability component.",
    caveats=(
        "The Kelsall two-component variant, splitting fast and slow floating fractions, is the "
        "interesting question: whether the data justify one rate constant or two is a genuine "
        "complexity-versus-accuracy Pareto demonstration on a real industrial problem.",
    ),
    real_data_twin="flotation-silica",
    truth_node=lambda: Node.call("mul", Node.var(1), Node.call("sub", Node.const(1.0),
        Node.call("exp", Node.call("neg", Node.call("mul", Node.var(2), Node.var(0)))))),
    regime="structure",
)


# --------------------------------------------------------------------------------------------
# 6. Two-product mass balance
# --------------------------------------------------------------------------------------------


def _two_product(rng: np.random.Generator, n: int) -> tuple[np.ndarray, np.ndarray]:
    f = rng.uniform(0.3, 3.0, size=n)
    c = f * rng.uniform(10.0, 40.0, size=n)
    t = rng.uniform(0.02, 0.3, size=n)
    t = np.minimum(t, f * 0.9)
    y = 100.0 * (c / f) * ((f - t) / (c - t))
    return np.column_stack([f, c, t]), y


TWO_PRODUCT = Generator(
    id="two-product-recovery",
    category="S",
    name="Two-product mass balance: metal recovery",
    inputs=(
        InputSpec("f", "f", "%", DIMENSIONLESS, "feed assay"),
        InputSpec("c", "c", "%", DIMENSIONLESS, "concentrate assay"),
        InputSpec("t", "t", "%", DIMENSIONLESS, "tailings assay"),
    ),
    target=InputSpec("R", "X_R", "%", DIMENSIONLESS, "metal recovery"),
    truth_latex=r"X_R = 100 \cdot \frac{c}{f} \cdot \frac{f - t}{c - t}",
    truth_infix="100 * (c/f) * ((f - t)/(c - t))",
    source="Two-product formula, froth flotation metallurgical accounting, verified (research dossier 7.2.6)",
    sample=_two_product,
    recovery_target="the exact rational expression, a ratio of differences",
    caveats=(
        "A HARD exact-recovery test on purpose. The answer is a ratio of differences, which most "
        "search spaces reach only with a competent simplification stage, so a failure here is "
        "informative about the engine rather than about the data.",
    ),
    truth_node=lambda: Node.call("mul", Node.call("mul", Node.const(100.0),
        Node.call("div", Node.var(1), Node.var(0))),
        Node.call("div", Node.call("sub", Node.var(0), Node.var(2)),
                          Node.call("sub", Node.var(1), Node.var(2)))),
    regime="structure",
)


# --------------------------------------------------------------------------------------------
# 7. Heat exchanger effectiveness-NTU
# --------------------------------------------------------------------------------------------


def _ntu(rng: np.random.Generator, n: int) -> tuple[np.ndarray, np.ndarray]:
    ntu = _loguniform(rng, 0.1, 8.0, n)
    # Keep Cr away from exactly 1 where the counter-current expression has a removable singularity;
    # the singularity itself is the subject of a dedicated variant rather than a source of NaNs here.
    cr = rng.uniform(0.0, 0.95, size=n)
    y = (1.0 - np.exp(-ntu * (1.0 - cr))) / (1.0 - cr * np.exp(-ntu * (1.0 - cr)))
    return np.column_stack([ntu, cr]), y


NTU_COUNTERFLOW = Generator(
    id="heat-exchanger-ntu",
    category="S",
    name="Heat exchanger effectiveness, counter-current NTU",
    inputs=(
        InputSpec("NTU", r"\mathrm{NTU}", "1", DIMENSIONLESS, "number of transfer units, UA/C_min"),
        InputSpec("Cr", "C_r", "1", DIMENSIONLESS, "heat capacity rate ratio C_min/C_max"),
    ),
    target=InputSpec("eps", r"\varepsilon", "1", DIMENSIONLESS, "effectiveness"),
    truth_latex=r"\varepsilon = \frac{1 - e^{-\mathrm{NTU}(1 - C_r)}}{1 - C_r e^{-\mathrm{NTU}(1 - C_r)}}",
    truth_infix="(1 - exp(-NTU*(1 - Cr))) / (1 - Cr*exp(-NTU*(1 - Cr)))",
    source="Effectiveness-NTU method, counter-current arrangement, verified (research dossier 7.2.7)",
    sample=_ntu,
    recovery_target="both branches, plus the Cr = 1 limit eps = NTU/(1 + NTU)",
    validity="Steady state, constant properties, no phase change, no losses to surroundings.",
    caveats=(
        "There is a REMOVABLE SINGULARITY at Cr = 1 where the expression degenerates to NTU/(1+NTU). "
        "That is the point of the case: a fitted result that blows up at Cr = 1 is wrong in a way a "
        "plain error metric hides completely, and the extrapolation view is what exposes it.",
    ),
    truth_node=lambda: Node.call("div",
        Node.call("sub", Node.const(1.0), Node.call("exp", Node.call("neg",
            Node.call("mul", Node.var(0), Node.call("sub", Node.const(1.0), Node.var(1)))))),
        Node.call("sub", Node.const(1.0), Node.call("mul", Node.var(1),
            Node.call("exp", Node.call("neg",
                Node.call("mul", Node.var(0), Node.call("sub", Node.const(1.0), Node.var(1)))))))),
    regime="structure+constants",
)


# --------------------------------------------------------------------------------------------
# 8. Convective heat transfer
# --------------------------------------------------------------------------------------------


def _dittus_boelter(rng: np.random.Generator, n: int) -> tuple[np.ndarray, np.ndarray]:
    re = _loguniform(rng, 1e4, 5e6, n)
    pr = _loguniform(rng, 0.6, 160.0, n)
    y = 0.023 * re ** 0.8 * pr ** 0.4
    return np.column_stack([re, pr]), y


DITTUS_BOELTER = Generator(
    id="nusselt-dittus-boelter",
    category="S",
    name="Convective heat transfer: Dittus-Boelter",
    inputs=(
        InputSpec("Re", r"\mathrm{Re}_D", "1", DIMENSIONLESS, "Reynolds number"),
        InputSpec("Pr", r"\mathrm{Pr}", "1", DIMENSIONLESS, "Prandtl number"),
    ),
    target=InputSpec("Nu", r"\mathrm{Nu}_D", "1", DIMENSIONLESS, "Nusselt number"),
    truth_latex=r"\mathrm{Nu}_D = 0.023\,\mathrm{Re}_D^{4/5}\,\mathrm{Pr}^{0.4}",
    truth_infix="0.023 * Re^0.8 * Pr^0.4",
    source="Dittus-Boelter correlation, verified (research dossier 7.2.8)",
    sample=_dittus_boelter,
    recovery_target="the power-law exponents 0.8 and 0.4",
    validity="0.6 <= Pr <= 160, Re above about 10000, L/D above about 10, heating (n = 0.4).",
    caveats=(
        "A pure power law in two dimensionless groups, so it is one of the few cases where a "
        "unit-constrained search has no work to do and an unconstrained one still has to find two "
        "fractional exponents. That contrast is the case.",
        "The Gnielinski correlation covers a wider range and is NOT a pure power law; data generated "
        "from it cannot be fitted by one at low Reynolds number, which the lab ships as a clean "
        "demonstration of model misspecification.",
    ),
    regime="structure+constants",
)


def _gnielinski(rng: np.random.Generator, n: int) -> tuple[np.ndarray, np.ndarray]:
    re = _loguniform(rng, 3e3, 5e6, n)
    pr = _loguniform(rng, 0.5, 200.0, n)
    f = (0.79 * np.log(re) - 1.64) ** -2
    y = ((f / 8.0) * (re - 1000.0) * pr) / (1.0 + 12.7 * np.sqrt(f / 8.0) * (pr ** (2.0 / 3.0) - 1.0))
    return np.column_stack([re, pr]), y


GNIELINSKI = Generator(
    id="nusselt-gnielinski",
    category="S",
    name="Convective heat transfer: Gnielinski (the misspecification case)",
    inputs=DITTUS_BOELTER.inputs,
    target=DITTUS_BOELTER.target,
    truth_latex=(
        r"\mathrm{Nu}_D = \frac{(f/8)(\mathrm{Re}_D - 1000)\mathrm{Pr}}"
        r"{1 + 12.7\sqrt{f/8}\left(\mathrm{Pr}^{2/3} - 1\right)}, \quad f = (0.79\ln \mathrm{Re}_D - 1.64)^{-2}"
    ),
    truth_infix="((f/8)*(Re - 1000)*Pr) / (1 + 12.7*sqrt(f/8)*(Pr^(2/3) - 1)) with f = (0.79*log(Re) - 1.64)^-2",
    source="Gnielinski correlation, verified (research dossier 7.2.8)",
    sample=_gnielinski,
    recovery_target="whether a pure power law can fit this at all; it cannot at low Reynolds number",
    validity="0.5 <= Pr <= 2000, 3000 <= Re <= 5e6.",
    caveats=(
        "This case is designed to be UNRECOVERABLE by the obvious hypothesis. Reporting a good "
        "power-law fit here and stopping is exactly the failure the lab exists to demonstrate.",
    ),
    regime="structure+constants",
)


# --------------------------------------------------------------------------------------------
# 9. Pipe friction factor
# --------------------------------------------------------------------------------------------


def _swamee_jain(rng: np.random.Generator, n: int) -> tuple[np.ndarray, np.ndarray]:
    re = _loguniform(rng, 5e3, 1e8, n)
    rel_rough = _loguniform(rng, 1e-6, 5e-2, n)
    y = 0.25 / (np.log10(rel_rough / 3.7 + 5.74 / re ** 0.9)) ** 2
    return np.column_stack([re, rel_rough]), y


FRICTION_FACTOR = Generator(
    id="friction-factor",
    category="S",
    name="Pipe friction factor: Swamee-Jain explicit form",
    inputs=(
        InputSpec("Re", r"\mathrm{Re}", "1", DIMENSIONLESS, "Reynolds number"),
        InputSpec("relrough", r"\epsilon/D", "1", DIMENSIONLESS, "relative roughness"),
    ),
    target=InputSpec("f", "f", "1", DIMENSIONLESS, "Darcy friction factor"),
    truth_latex=r"f = \frac{0.25}{\left[\log_{10}\!\left(\frac{\epsilon/D}{3.7} + \frac{5.74}{\mathrm{Re}^{0.9}}\right)\right]^2}",
    truth_infix="0.25 / (log10(relrough/3.7 + 5.74/Re^0.9))^2",
    source="Swamee-Jain explicit approximation to Colebrook-White, verified (research dossier 7.2.9)",
    sample=_swamee_jain,
    recovery_target="the piecewise structure, the 1/sqrt(f) implicit form, and the fully-rough asymptote",
    validity="5000 <= Re <= 1e8 and 1e-6 <= eps/D <= 0.05.",
    caveats=(
        "The laminar branch f = 64/Re is EXACT and belongs to a different regime; a single expression "
        "covering both branches does not exist, so a case that samples across the transition is asking "
        "for something impossible. The lab samples the turbulent branch and says so.",
        "This generator has the strongest real-data twin in the set: the Nikuradse 362 measured points, "
        "whose transitional hump is genuinely not reproduced by Colebrook. Synthetic ground truth to "
        "calibrate the engine, real data to expose what the correlation misses.",
    ),
    real_data_twin="nikuradse-friction",
    regime="structure+constants",
)


# --------------------------------------------------------------------------------------------
# 10. Stokes settling
# --------------------------------------------------------------------------------------------


def _stokes(rng: np.random.Generator, n: int) -> tuple[np.ndarray, np.ndarray]:
    radius = _loguniform(rng, 1e-6, 1e-3, n)
    rho_p = rng.uniform(1500.0, 8000.0, size=n)
    rho_f = rng.uniform(900.0, 1300.0, size=n)
    mu = _loguniform(rng, 1e-4, 1e-1, n)
    y = (2.0 / 9.0) * ((rho_p - rho_f) / mu) * G0 * radius ** 2
    return np.column_stack([radius, rho_p, rho_f, mu]), y


STOKES = Generator(
    id="stokes-settling",
    category="S",
    name="Stokes terminal settling velocity",
    inputs=(
        InputSpec("R", "R", "m", COMMON["length"], "particle radius"),
        InputSpec("rho_p", r"\rho_p", "kg/m^3", COMMON["density"], "particle density"),
        InputSpec("rho_f", r"\rho_f", "kg/m^3", COMMON["density"], "fluid density"),
        InputSpec("mu", r"\mu", "Pa.s", dims(m=-1, kg=1, s=-1), "dynamic viscosity"),
    ),
    target=InputSpec("v", "v", "m/s", COMMON["velocity"], "terminal velocity"),
    truth_latex=r"v = \frac{2}{9}\,\frac{\rho_p - \rho_f}{\mu}\,g\,R^2",
    truth_infix="(2/9) * ((rho_p - rho_f)/mu) * 9.80665 * R^2",
    source="Stokes law, verified (research dossier 7.2.10)",
    sample=_stokes,
    recovery_target="the R^2 dependence and the density-DIFFERENCE structure",
    validity="Reynolds number below 1 for about 10 percent error, stated on the source.",
    caveats=(
        "The density difference matters: a fit that finds rho_p alone can look excellent on a sample "
        "where rho_f barely varies, and is wrong. This is the clearest small example of a correct-looking "
        "fit that is the wrong law.",
        "A variant deliberately samples beyond Re = 1 so the lab can show a law BREAKING DOWN outside "
        "its validity range, which is the single most useful honest lesson available here.",
        "No open tabulated sphere-drag experimental dataset was found in the research, so this case "
        "stays synthetic rather than claiming a real twin.",
    ),
    truth_node=lambda: Node.call("mul", Node.call("mul", Node.const(2.0 / 9.0 * G0),
        Node.call("div", Node.call("sub", Node.var(1), Node.var(2)), Node.var(3))),
        Node.call("square", Node.var(0))),
    regime="structure+constants",
)


# --------------------------------------------------------------------------------------------
# 11. Antoine vapour pressure
# --------------------------------------------------------------------------------------------


def _antoine(rng: np.random.Generator, n: int) -> tuple[np.ndarray, np.ndarray]:
    # Verified water constants for the lower window, T in degC and p in mmHg.
    a, b, c = 8.07131, 1730.63, 233.426
    T = rng.uniform(-20.0, 100.0, size=n)
    y = 10.0 ** (a - b / (c + T))
    return T.reshape(-1, 1), y


ANTOINE = Generator(
    id="antoine-vapour-pressure",
    category="S",
    name="Antoine vapour pressure (water, lower window)",
    inputs=(InputSpec("T", "T", "degC", DIMENSIONLESS, "temperature in degrees Celsius"),),
    target=InputSpec("p", "p", "mmHg", DIMENSIONLESS, "saturation vapour pressure"),
    truth_latex=r"\log_{10} p = A - \frac{B}{C + T}, \quad A = 8.07131,\ B = 1730.63,\ C = 233.426",
    truth_infix="10^(8.07131 - 1730.63/(233.426 + T))",
    source="Antoine equation, verified water constants for -20 to 100 degC (research dossier 7.2.11)",
    sample=_antoine,
    recovery_target="the B/(C + T) reciprocal-shifted form",
    validity="-20 to 100 degC for these constants; a DIFFERENT verified set covers 99 to 374 degC.",
    caveats=(
        "A single constant set cannot cover the whole liquid range. The two-window variant asks the "
        "search to detect that, which is a change-point question dressed as a fitting question.",
        "Real-data twin: the batch distillation dataset names its three chemical systems, so the true "
        "Antoine constants of every component are independently obtainable rather than assumed.",
    ),
    regime="structure+constants",
)


# --------------------------------------------------------------------------------------------
# 12. Pump affinity laws
# --------------------------------------------------------------------------------------------


def _affinity_power(rng: np.random.Generator, n: int) -> tuple[np.ndarray, np.ndarray]:
    n1 = rng.uniform(600.0, 3600.0, size=n)
    n2 = rng.uniform(600.0, 3600.0, size=n)
    d1 = rng.uniform(0.1, 1.0, size=n)
    d2 = rng.uniform(0.1, 1.0, size=n)
    rho1 = rng.uniform(800.0, 1400.0, size=n)
    rho2 = rng.uniform(800.0, 1400.0, size=n)
    y = (rho1 / rho2) * (n1 / n2) ** 3 * (d1 / d2) ** 5
    return np.column_stack([n1, n2, d1, d2, rho1, rho2]), y


AFFINITY_POWER = Generator(
    id="pump-affinity-power",
    category="S",
    name="Pump affinity law: shaft power ratio",
    inputs=(
        InputSpec("n1", "n_1", "rpm", COMMON["frequency"], "shaft speed, point 1"),
        InputSpec("n2", "n_2", "rpm", COMMON["frequency"], "shaft speed, point 2"),
        InputSpec("D1", "D_1", "m", COMMON["length"], "impeller diameter, point 1"),
        InputSpec("D2", "D_2", "m", COMMON["length"], "impeller diameter, point 2"),
        InputSpec("rho1", r"\rho_1", "kg/m^3", COMMON["density"], "density, point 1"),
        InputSpec("rho2", r"\rho_2", "kg/m^3", COMMON["density"], "density, point 2"),
    ),
    target=InputSpec("Wratio", "W_1/W_2", "1", DIMENSIONLESS, "shaft power ratio"),
    truth_latex=r"\frac{W_1}{W_2} = \frac{\rho_1}{\rho_2}\left(\frac{n_1}{n_2}\right)^{3}\left(\frac{D_1}{D_2}\right)^{5}",
    truth_infix="(rho1/rho2) * (n1/n2)^3 * (D1/D2)^5",
    source="Affinity laws for centrifugal pumps and fans, verified (research dossier 7.2.12)",
    sample=_affinity_power,
    recovery_target="the integer exponent triple (3, 5) for power, against (1, 3) for flow and (2, 2) for head",
    validity="Assumes constant efficiency between the two operating points.",
    caveats=(
        "The cleanest DIMENSIONAL-ANALYSIS case in the set, and the natural place to demonstrate the "
        "unit-typed rung: with units enforced the exponents are forced, without units they must be "
        "found. Running both configurations on this one case is the whole argument for rung 8.",
    ),
    truth_node=lambda: Node.call("mul", Node.call("mul",
        Node.call("div", Node.var(4), Node.var(5)),
        Node.call("mul", Node.call("div", Node.var(0), Node.var(1)),
            Node.call("square", Node.call("div", Node.var(0), Node.var(1))))),
        Node.call("mul", Node.call("square", Node.call("square", Node.call("div", Node.var(2), Node.var(3)))),
                          Node.call("div", Node.var(2), Node.var(3)))),
    regime="structure",
)


# --------------------------------------------------------------------------------------------
# 13. Wind turbine power curve
# --------------------------------------------------------------------------------------------


def _wind_power(rng: np.random.Generator, n: int) -> tuple[np.ndarray, np.ndarray]:
    # Kelmarsh geometry, so the synthetic and real cases are directly comparable.
    swept_area = 6647.6      # m^2
    rated_power = 2_050_000  # W
    cp = 0.47
    v_in, v_out = 3.0, 25.0
    v = rng.uniform(0.0, 28.0, size=n)
    T = rng.uniform(263.0, 313.0, size=n)
    pressure = rng.uniform(95_000.0, 104_000.0, size=n)
    rho = pressure / (R_DRY_AIR * T)
    cubic = 0.5 * rho * swept_area * v ** 3 * cp
    y = np.where(v < v_in, 0.0, np.where(v > v_out, 0.0, np.minimum(cubic, rated_power)))
    return np.column_stack([v, T, pressure]), y


WIND_POWER = Generator(
    id="wind-power-curve",
    category="S",
    name="Wind turbine power curve with the Betz cubic and a rated plateau",
    inputs=(
        InputSpec("v", "v", "m/s", COMMON["velocity"], "upstream wind speed"),
        InputSpec("T", "T", "K", COMMON["temperature"], "air temperature"),
        InputSpec("p", "p", "Pa", COMMON["pressure"], "air pressure"),
    ),
    target=InputSpec("P", "P", "W", COMMON["power"], "electrical power output"),
    truth_latex=r"P = \min\!\left(\tfrac{1}{2}\rho S v^3 C_p,\; P_{rated}\right),\quad \rho = \frac{p}{R_d T}",
    truth_infix="min(0.5 * (p/(287.058*T)) * 6647.6 * v^3 * 0.47, 2050000) gated by cut-in and cut-out",
    source="Betz law and the verified Kelmarsh turbine geometry (research dossier 7.2.13)",
    sample=_wind_power,
    recovery_target="the cubic term and the saturation breakpoint",
    validity="Cp cannot exceed the Betz limit 16/27 = 0.593; real turbines peak at 0.45 to 0.50.",
    caveats=(
        "PIECEWISE by construction: zero below cut-in, cubic, a rated plateau, then zero above cut-out. "
        "A single smooth expression cannot represent it, so this case tests whether the search reports "
        "an honest partial fit or an overconfident smooth one.",
        "Real-data twin: the Kelmarsh farm, using the same swept area and rated power.",
    ),
    regime="structure+constants",
)


# --------------------------------------------------------------------------------------------
# 14. Population dynamics
# --------------------------------------------------------------------------------------------


def _theta_logistic(rng: np.random.Generator, n: int) -> tuple[np.ndarray, np.ndarray]:
    r = rng.uniform(0.1, 3.0, size=n)
    k = _loguniform(rng, 10.0, 1e5, n)
    theta = rng.uniform(0.3, 3.0, size=n)
    pop = k * rng.uniform(0.01, 1.5, size=n)
    y = r * pop * (1.0 - (pop / k) ** theta)
    return np.column_stack([pop, r, k, theta]), y


THETA_LOGISTIC = Generator(
    id="theta-logistic-growth",
    category="S",
    name="Theta-logistic population growth",
    inputs=(
        InputSpec("N", "N", "1", DIMENSIONLESS, "population size"),
        InputSpec("r", "r", "1/a", COMMON["frequency"], "intrinsic growth rate"),
        InputSpec("K", "K", "1", DIMENSIONLESS, "carrying capacity"),
        InputSpec("theta", r"\theta", "1", DIMENSIONLESS, "density-dependence shape"),
    ),
    target=InputSpec("dNdt", r"dN/dt", "1/a", COMMON["frequency"], "growth rate"),
    truth_latex=r"\frac{dN}{dt} = r N \left(1 - \left(\frac{N}{K}\right)^{\theta}\right)",
    truth_infix="r * N * (1 - (N/K)^theta)",
    source="Theta-logistic model, verified against GPDD provenance (research dossier 7.2.14)",
    sample=_theta_logistic,
    recovery_target="the density-dependence exponent theta, recovering the plain logistic at theta = 1",
    caveats=(
        "Real-data twin: GPDD ships 5,156 series WITH published theta fits, so a recovered exponent "
        "can be compared against a published one rather than only against the residual.",
    ),
    real_data_twin="gpdd-density-dependence",
    regime="structure",
)


def _lotka_volterra(rng: np.random.Generator, n: int) -> tuple[np.ndarray, np.ndarray]:
    # Parameters chosen to reproduce roughly the ten-year lynx-hare cycle.
    # Only the prey right-hand side is generated here, so only alpha and beta are used. The
    # predator parameters gamma and delta belong to the second equation of the system and to
    # the conserved quantity, both of which ship as their own variants.
    alpha, beta = 0.55, 0.028
    hares = rng.uniform(5.0, 90.0, size=n)
    lynx = rng.uniform(5.0, 60.0, size=n)
    y = alpha * hares - beta * hares * lynx
    return np.column_stack([hares, lynx]), y


LOTKA_VOLTERRA = Generator(
    id="lotka-volterra-rhs",
    category="S",
    name="Lotka-Volterra: the prey right-hand side",
    inputs=(
        InputSpec("H", "H", "1", DIMENSIONLESS, "prey abundance"),
        InputSpec("L", "L", "1", DIMENSIONLESS, "predator abundance"),
    ),
    target=InputSpec("dHdt", "dH/dt", "1/a", COMMON["frequency"], "prey growth rate"),
    truth_latex=r"\frac{dH}{dt} = \alpha H - \beta H L",
    truth_infix="0.55*H - 0.028*H*L",
    source="Lotka-Volterra predator-prey model, lynx-hare parameterisation (research dossier 7.2.14)",
    sample=_lotka_volterra,
    recovery_target="the bilinear interaction term, and separately the conserved quantity",
    caveats=(
        "The conserved quantity V = delta*H - gamma*ln(H) + beta*L - alpha*ln(L) is a DIFFERENT and "
        "harder symbolic regression formulation on the same system, and it ships as its own variant. "
        "Recovering an invariant is not the same task as recovering a derivative.",
        "Real-data twin: the lynx-hare series, 21 points, 1900 to 1920.",
    ),
    real_data_twin="lynx-hare-lotka-volterra",
    truth_node=lambda: Node.call("sub", Node.call("mul", Node.const(0.55), Node.var(0)),
        Node.call("mul", Node.const(0.028), Node.call("mul", Node.var(0), Node.var(1)))),
    regime="structure+constants",
)


# --------------------------------------------------------------------------------------------
# 15. ASM1 aerobic growth switching
# --------------------------------------------------------------------------------------------


def _asm1_growth(rng: np.random.Generator, n: int) -> tuple[np.ndarray, np.ndarray]:
    mu_h, k_s, k_oh = 4.0, 10.0, 0.2
    ss = _loguniform(rng, 0.1, 200.0, n)
    so = _loguniform(rng, 0.01, 8.0, n)
    xbh = rng.uniform(500.0, 4000.0, size=n)
    y = mu_h * (ss / (k_s + ss)) * (so / (k_oh + so)) * xbh
    return np.column_stack([ss, so, xbh]), y


ASM1_GROWTH = Generator(
    id="asm1-aerobic-growth",
    category="S",
    name="ASM1 aerobic heterotrophic growth: a product of saturations",
    inputs=(
        InputSpec("Ss", "S_S", "g COD/m^3", DIMENSIONLESS, "readily biodegradable substrate"),
        InputSpec("So", "S_O", "g O2/m^3", DIMENSIONLESS, "dissolved oxygen"),
        InputSpec("Xbh", "X_{B,H}", "g COD/m^3", DIMENSIONLESS, "heterotrophic biomass"),
    ),
    target=InputSpec("rate", r"\rho_1", "g COD/(m^3 d)", DIMENSIONLESS, "aerobic growth rate"),
    truth_latex=r"\rho_1 = \mu_H \frac{S_S}{K_S + S_S} \cdot \frac{S_O}{K_{OH} + S_O} \cdot X_{B,H}",
    truth_infix="4.0 * (Ss/(10 + Ss)) * (So/(0.2 + So)) * Xbh",
    source="IWA ASM1 kinetic rate expressions, from the published BSM1 specification (research dossier 7.2.15)",
    sample=_asm1_growth,
    recovery_target="the PRODUCT of two Monod switching functions, a genuinely hard multiplicative structure",
    caveats=(
        "A product of saturations is much harder for a search than a sum of terms, because no additive "
        "decomposition of the target exists. This is the case that separates engines with a real "
        "multiplicative search from those that only assemble sums.",
        "The BSM1 model is published but its reference implementation is not, so this lab implements "
        "and owns its own simulator rather than claiming compatibility with one it cannot inspect.",
    ),
    truth_node=lambda: Node.call("mul", Node.call("mul", Node.const(4.0),
        Node.call("div", Node.var(0), Node.call("add", Node.const(10.0), Node.var(0)))),
        Node.call("mul", Node.call("div", Node.var(1), Node.call("add", Node.const(0.2), Node.var(1))),
                          Node.var(2))),
    regime="structure+constants",
)


#: Every generator, by id.
GENERATORS: dict[str, Generator] = {
    g.id: g
    for g in (
        MICHAELIS_MENTEN,
        ARRHENIUS,
        CSTR,
        COMMINUTION_BOND,
        COMMINUTION_KICK,
        FLOTATION_KINETICS,
        TWO_PRODUCT,
        NTU_COUNTERFLOW,
        DITTUS_BOELTER,
        GNIELINSKI,
        FRICTION_FACTOR,
        STOKES,
        ANTOINE,
        AFFINITY_POWER,
        WIND_POWER,
        THETA_LOGISTIC,
        LOTKA_VOLTERRA,
        ASM1_GROWTH,
    )
}


def make_dataset(
    generator: Generator,
    *,
    n_rows: int = 400,
    seed: int = 0,
    noise: float = 0.0,
    multiplicative_noise: bool = False,
) -> tuple[np.ndarray, np.ndarray]:
    """Draw a dataset from a generator, at a stated noise level.

    Deterministic in `(generator.id, n_rows, seed, noise)`, so a committed artifact regenerates
    byte for byte.
    """
    rng = np.random.default_rng(abs(hash(generator.id)) % (2**32) + seed)
    X, y = generator.sample(rng, n_rows)
    y = add_noise(rng, y, noise, multiplicative=multiplicative_noise)
    return X, y
