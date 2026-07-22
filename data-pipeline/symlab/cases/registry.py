"""The case registry: what the lab actually runs, and which ladder rungs each case exercises.

A case is one dataset plus the set of search configurations that will be run against it. The
configurations become the variant chips in the app, and because each one differs from its neighbour
by exactly one mechanism, clicking through them is an ablation rather than a tour.

Categories, used by the registry grouping and by the docs taxonomy:

    P  physics ground truth        the law is published, so recovery is verifiable to the digit
    I  industrial process          real plant and equipment data, real noise
    M  mining and metallurgy       the domain the research found to be the field's clearest gap
    B  biology and ecology         published models with fitted parameters to compare against
    E  environment and energy      physical bounds that a discovered form can violate visibly
    S  synthetic generators        first-principles, exactly scoreable, four with a real twin

Two rules are enforced here rather than left to discipline:

1. **A case declares whether its ground truth is KNOWN.** Only cases with a known truth contribute to
   a solution rate; the rest contribute to error metrics only. Mixing the two would let a lab quote a
   recovery percentage that silently includes problems where recovery cannot be checked.

2. **A case declares its honest variant count.** Where a case genuinely admits no meaningful
   parametric family, it ships one deeply documented variant and says so, rather than being padded
   with fabricated regimes to hit a number.
"""
from __future__ import annotations

from dataclasses import dataclass, field, replace

from ..search.engine import LADDER, SearchConfig
from .generators import GENERATORS, Generator

#: Category codes and their human names.
CATEGORIES: dict[str, str] = {
    "P": "Physics ground truth",
    "I": "Industrial process",
    "M": "Mining and metallurgy",
    "B": "Biology and ecology",
    "E": "Environment and energy",
    "S": "Synthetic generators",
}


@dataclass(frozen=True)
class Variant:
    """One configuration of the search, shown as a chip in the app."""

    id: str
    label_en: str
    label_es: str
    note_en: str
    note_es: str
    config: SearchConfig


@dataclass(frozen=True)
class Case:
    """One case: a dataset, the variants run against it, and what is known about the answer."""

    id: str
    name_en: str
    name_es: str
    category: str
    loader: str                      # a key in io.loaders.LOADERS, or "generator:<id>"
    variants: tuple[Variant, ...]
    ground_truth_known: bool
    real_or_synthetic: str
    summary_en: str
    summary_es: str
    ground_truth_latex: str | None = None
    n_rows: int | None = None
    noise_levels: tuple[float, ...] = (0.0,)
    primitive_set: str = "physics"
    honest_single_variant_reason: str = ""
    caveats: tuple[str, ...] = ()

    @property
    def category_name(self) -> str:
        return CATEGORIES[self.category]

    @property
    def is_generator(self) -> bool:
        return self.loader.startswith("generator:")

    @property
    def generator(self) -> Generator | None:
        return GENERATORS.get(self.loader.split(":", 1)[1]) if self.is_generator else None


# --------------------------------------------------------------------------------------------
# The standard variant ladder
# --------------------------------------------------------------------------------------------

_LADDER_TEXT: dict[str, tuple[str, str, str, str]] = {
    "r1-koza-baseline": (
        "Koza baseline", "Base Koza",
        "Tree genetic programming as published in 1992: tournament selection, subtree crossover, "
        "no scaling, no guards. Every later chip must beat this by a measured margin.",
        "Programacion genetica de arboles como se publico en 1992: seleccion por torneo, cruce de "
        "subarboles, sin escalado ni salvaguardas. Cada chip posterior debe superarlo por un margen medido.",
    ),
    "r2-linear-scaling": (
        "+ linear scaling", "+ escalado lineal",
        "Adds closed-form optimal slope and intercept per candidate, plus interval arithmetic that "
        "rejects a division by an interval containing zero BEFORE evaluating it. No protected operators.",
        "Anade pendiente e intercepto optimos en forma cerrada por candidato, mas aritmetica de "
        "intervalos que rechaza una division por un intervalo que contiene cero ANTES de evaluarla.",
    ),
    "r3-constant-tuning": (
        "+ constant tuning", "+ ajuste de constantes",
        "Adds Levenberg-Marquardt fitting of every numeric leaf, written back into the tree so the "
        "improvement is inherited rather than rediscovered each generation.",
        "Anade ajuste Levenberg-Marquardt de cada hoja numerica, reescrito en el arbol para que la "
        "mejora se herede en lugar de redescubrirse en cada generacion.",
    ),
    "r4-multi-objective": (
        "+ Pareto survival", "+ supervivencia Pareto",
        "Complexity stops being a penalty and becomes a second objective. The output stops being a "
        "model and becomes a front. This is the chip that changes what the product reports.",
        "La complejidad deja de ser una penalizacion y pasa a ser un segundo objetivo. La salida deja "
        "de ser un modelo y pasa a ser un frente.",
    ),
    "r5-epsilon-lexicase": (
        "+ epsilon-lexicase", "+ epsilon-lexicase",
        "Selection judges one training case at a time instead of on aggregate error, so specialists "
        "survive. Measured cost at this budget: about 22 times the baseline wall-clock.",
        "La seleccion juzga un caso de entrenamiento a la vez en lugar del error agregado, de modo que "
        "los especialistas sobreviven. Costo medido: unas 22 veces el tiempo de la base.",
    ),
    "r6-age-fitness-islands": (
        "+ age-fitness islands", "+ islas edad-aptitud",
        "Age becomes an objective and the population splits into migrating islands, so fresh material "
        "is not immediately outcompeted by an entrenched lineage. The Eureqa recipe.",
        "La edad pasa a ser un objetivo y la poblacion se divide en islas con migracion, de modo que el "
        "material nuevo no es desplazado de inmediato por un linaje establecido.",
    ),
    "r7-deduplication": (
        "+ deduplication", "+ deduplicacion",
        "Structural and semantic hashing skip candidates already evaluated. The count avoided is "
        "reported, because it is a measurement about the search, not an implementation detail.",
        "El hashing estructural y semantico omite candidatos ya evaluados. El conteo evitado se "
        "reporta, porque es una medicion sobre la busqueda, no un detalle de implementacion.",
    ),
    "r8-unit-typed": (
        "+ unit-typed search", "+ busqueda con unidades",
        "Dimensional analysis constrains GENERATION, so an expression that adds a mass to a time is "
        "never built. Only available where the inputs carry declared units.",
        "El analisis dimensional restringe la GENERACION, de modo que nunca se construye una expresion "
        "que sume una masa a un tiempo. Solo disponible cuando las entradas declaran unidades.",
    ),
    "parsimony-arm": (
        "parsimony arm", "brazo de parsimonia",
        "The single-objective comparison: complexity as a penalty term rather than a second "
        "objective. Shipped so the Pareto chip has something real to be compared against.",
        "La comparacion mono-objetivo: complejidad como termino de penalizacion en lugar de segundo "
        "objetivo. Se incluye para que el chip de Pareto tenga con que compararse.",
    ),
}


def ladder_variants(
    keys: tuple[str, ...],
    *,
    population: int = 300,
    generations: int = 40,
    primitive_set: str = "physics",
) -> tuple[Variant, ...]:
    """Build variant chips from ladder keys, at a stated budget.

    The budget is applied uniformly across the chips of one case, because comparing rungs at
    different budgets is the budget-fairness failure the benchmark literature calls out.
    """
    out: list[Variant] = []
    for key in keys:
        base = LADDER[key]
        config = replace(base, population=population, generations=generations,
                         primitive_set=primitive_set)
        label_en, label_es, note_en, note_es = _LADDER_TEXT[key]
        out.append(Variant(id=key, label_en=label_en, label_es=label_es,
                           note_en=note_en, note_es=note_es, config=config))
    return tuple(out)


#: The rungs shown on a case that carries declared units, so rung 8 is meaningful.
FULL_LADDER: tuple[str, ...] = (
    "r1-koza-baseline", "r2-linear-scaling", "r3-constant-tuning", "r4-multi-objective",
    "r5-epsilon-lexicase", "r6-age-fitness-islands", "r7-deduplication", "r8-unit-typed",
)

#: The rungs shown on a case whose inputs are dimensionless or undeclared. Rung 8 is omitted
#: honestly rather than shown as a chip that silently does nothing.
UNITLESS_LADDER: tuple[str, ...] = (
    "r1-koza-baseline", "r2-linear-scaling", "r3-constant-tuning", "r4-multi-objective",
    "r5-epsilon-lexicase", "r6-age-fitness-islands", "r7-deduplication", "parsimony-arm",
)


def _generator_case(
    generator_id: str,
    *,
    category: str,
    name_es: str,
    summary_en: str,
    summary_es: str,
    ladder: tuple[str, ...] = FULL_LADDER,
    n_rows: int = 400,
    noise_levels: tuple[float, ...] = (0.0, 0.01, 0.1),
    population: int = 300,
    generations: int = 40,
) -> Case:
    generator = GENERATORS[generator_id]
    return Case(
        id=generator.id,
        name_en=generator.name,
        name_es=name_es,
        category=category,
        loader=f"generator:{generator_id}",
        variants=ladder_variants(ladder, population=population, generations=generations,
                                 primitive_set=generator.suggested_primitives),
        ground_truth_known=True,
        real_or_synthetic="synthetic",
        summary_en=summary_en,
        summary_es=summary_es,
        ground_truth_latex=generator.truth_latex,
        n_rows=n_rows,
        noise_levels=noise_levels,
        primitive_set=generator.suggested_primitives,
        caveats=generator.caveats,
    )


CASES: tuple[Case, ...] = (
    # ---------------------------------------------------------------- physics ground truth
    Case(
        id="feynman-suite", category="P",
        name_en="Feynman equations: published physical laws",
        name_es="Ecuaciones de Feynman: leyes fisicas publicadas",
        loader="pmlb:feynman", variants=ladder_variants(UNITLESS_LADDER, population=300, generations=30),
        ground_truth_known=True, real_or_synthetic="synthetic",
        summary_en=(
            "Eighteen published physical laws, each with 100,000 sampled rows and a machine-readable "
            "ground-truth formula. Because the answer is known, this case reports a SOLUTION RATE, "
            "which is a categorically stronger claim than a coefficient of determination."
        ),
        summary_es=(
            "Dieciocho leyes fisicas publicadas, cada una con 100.000 filas muestreadas y una formula "
            "de referencia legible por maquina. Como la respuesta se conoce, este caso reporta una TASA "
            "DE SOLUCION, una afirmacion categoricamente mas fuerte que un coeficiente de determinacion."
        ),
        n_rows=100_000, primitive_set="physics",
        caveats=(
            "This set has been public since 2019 and is inside the pretraining corpus of every large "
            "language model and arguably inside the synthetic distributions of every pretrained "
            "symbolic-regression transformer. Contamination is a live risk for any pretrained method "
            "evaluated here, and results from such methods carry that warning.",
            "Sampling ranges are uniform rather than physically realistic, which is exactly what the "
            "SRSD companion set exists to correct.",
        ),
    ),
    Case(
        id="strogatz-dynamics", category="P",
        name_en="Strogatz systems: two-state ODE right-hand sides",
        name_es="Sistemas de Strogatz: lados derechos de EDO de dos estados",
        loader="pmlb:strogatz", variants=ladder_variants(UNITLESS_LADDER, population=300, generations=30),
        ground_truth_known=True, real_or_synthetic="synthetic",
        summary_en=(
            "Fourteen right-hand sides from seven classical two-state dynamical systems. Recovering a "
            "derivative from a trajectory is a different task from fitting a static function, and this "
            "is where a method that looks strong on static problems often stops working."
        ),
        summary_es=(
            "Catorce lados derechos de siete sistemas dinamicos clasicos de dos estados. Recuperar una "
            "derivada a partir de una trayectoria es una tarea distinta de ajustar una funcion estatica."
        ),
        primitive_set="physics",
    ),
    Case(
        id="nikuradse-friction", category="P",
        name_en="Nikuradse rough-pipe friction: 362 measured points",
        name_es="Friccion en tuberia rugosa de Nikuradse: 362 puntos medidos",
        loader="nikuradse-friction",
        variants=ladder_variants(UNITLESS_LADDER, population=300, generations=40),
        ground_truth_known=False, real_or_synthetic="real",
        summary_en=(
            "Real 1933 laboratory measurements across six roughness ratios. The transitional hump in "
            "these points is genuinely NOT reproduced by the Colebrook correlation that engineering "
            "practice still uses, so this is a case where the accepted answer is visibly incomplete "
            "and a discovered expression has something real to add."
        ),
        summary_es=(
            "Mediciones de laboratorio reales de 1933 en seis razones de rugosidad. La joroba de "
            "transicion en estos puntos genuinamente NO se reproduce con la correlacion de Colebrook "
            "que la practica de ingenieria aun utiliza."
        ),
        n_rows=362,
        ground_truth_latex=r"\text{no closed form; Colebrook is implicit and incomplete here}",
        caveats=(
            "The synthetic friction-factor generator is the calibration twin of this case: fit the "
            "engine where the answer is known, then bring it here where it is not.",
            "The originally cited host returns HTTP 404. These points come from the MIT-licensed "
            "benchmark collection that carries them.",
        ),
    ),
    # ---------------------------------------------------------------- industrial process
    Case(
        id="ccpp-derating", category="I",
        name_en="Combined cycle power plant: ambient derating",
        name_es="Central de ciclo combinado: derrateo ambiental",
        loader="ccpp-derating", variants=ladder_variants(UNITLESS_LADDER, population=300, generations=40),
        ground_truth_known=False, real_or_synthetic="real",
        summary_en=(
            "9,568 hourly records from a real plant at full load. Output falls as ambient temperature "
            "rises and as exhaust vacuum changes; the expected structure carries an air-density term in "
            "pressure over temperature that a search has to assemble from separate inputs."
        ),
        summary_es=(
            "9.568 registros horarios de una central real a plena carga. La potencia cae al subir la "
            "temperatura ambiente; la estructura esperada lleva un termino de densidad del aire."
        ),
        n_rows=9_568,
        caveats=(
            "The archive ships five shuffled folds of the SAME records. Only the first is read; "
            "concatenating them would duplicate every row five times and destroy any held-out split.",
        ),
    ),
    Case(
        id="concrete-abrams", category="I",
        name_en="Concrete compressive strength: the Abrams law",
        name_es="Resistencia a compresion del hormigon: ley de Abrams",
        loader="concrete-abrams", variants=ladder_variants(UNITLESS_LADDER, population=300, generations=40),
        ground_truth_known=False, real_or_synthetic="real",
        summary_en=(
            "1,030 real mixes. The century-old empirical answer is that strength depends on the "
            "water-to-cement RATIO and on the logarithm of age. Neither the ratio nor the logarithm is "
            "an input column, so the search has to construct both."
        ),
        summary_es=(
            "1.030 mezclas reales. La respuesta empirica centenaria es que la resistencia depende de la "
            "RAZON agua-cemento y del logaritmo de la edad. Ninguna de las dos es una columna de entrada."
        ),
        n_rows=1_030,
        ground_truth_latex=r"f_c \approx \frac{A}{B^{w/c}}\ \text{(Abrams)}, \text{ with a } \ln(t) \text{ maturity term}",
    ),
    Case(
        id="wwtp-removal-identity", category="I",
        name_en="Wastewater treatment: an exact identity hiding in real data",
        name_es="Tratamiento de aguas residuales: una identidad exacta en datos reales",
        loader="wwtp-removal-identity",
        variants=ladder_variants(("r1-koza-baseline", "r2-linear-scaling", "r3-constant-tuning",
                                  "r4-multi-objective", "r7-deduplication"),
                                 population=200, generations=25),
        ground_truth_known=True, real_or_synthetic="real",
        summary_en=(
            "The removal-efficiency column is EXACTLY 100 times the inlet minus the outlet over the "
            "inlet, computed from two other columns in the same file. A method that cannot recover an "
            "exact identity present in its own inputs will not recover a physical law from noisy data, "
            "which makes this the cheapest honest sanity check in the whole set."
        ),
        summary_es=(
            "La columna de eficiencia de remocion es EXACTAMENTE 100 por la entrada menos la salida "
            "sobre la entrada. Un metodo que no recupera una identidad exacta presente en sus propias "
            "entradas no va a recuperar una ley fisica a partir de datos ruidosos."
        ),
        n_rows=380,
        ground_truth_latex=r"\mathrm{RD} = 100\,\frac{\mathrm{BOD}_{in} - \mathrm{BOD}_{out}}{\mathrm{BOD}_{in}}",
        honest_single_variant_reason="",
        caveats=(
            "The source landing page states there are no missing values. The file contains 591. Rows "
            "carrying them are dropped rather than imputed, because imputing into an exact identity "
            "would manufacture the very relationship this case exists to recover.",
        ),
    ),
    Case(
        id="gasturbine-nox", category="I",
        name_en="Gas turbine NOx: thermal formation from combustion conditions",
        name_es="NOx de turbina de gas: formacion termica segun condiciones de combustion",
        loader="gasturbine-nox", variants=ladder_variants(UNITLESS_LADDER, population=250, generations=30),
        ground_truth_known=False, real_or_synthetic="real",
        summary_en=(
            "36,733 hourly records over five years. Thermal nitric oxide formation is exponential in "
            "the inverse of flame temperature, so the expected structure needs a division inside an "
            "exponent, which a primitive set without that path simply cannot express."
        ),
        summary_es=(
            "36.733 registros horarios en cinco anos. La formacion termica de oxido nitrico es "
            "exponencial en el inverso de la temperatura de llama."
        ),
        n_rows=36_733,
        caveats=(
            "Carbon monoxide is excluded from the inputs. It is a co-measured emission rather than a "
            "driver, and leaving it in lets a search explain one pollutant with another.",
        ),
    ),
    # ---------------------------------------------------------------- mining
    Case(
        id="flotation-silica", category="M",
        name_en="Froth flotation: silica in the concentrate, a soft sensor with a laboratory delay",
        name_es="Flotacion: silice en el concentrado, sensor virtual con retardo de laboratorio",
        loader="flotation-silica", variants=ladder_variants(UNITLESS_LADDER, population=250, generations=30),
        ground_truth_known=False, real_or_synthetic="real",
        summary_en=(
            "A real concentrator, 21 process inputs against the silica grade of the concentrate. The "
            "target is a laboratory assay measured once an hour, so this is genuinely a soft sensor "
            "problem: predict now what the laboratory will confirm later."
        ),
        summary_es=(
            "Una concentradora real, 21 entradas de proceso contra la ley de silice del concentrado. "
            "El objetivo es un ensayo de laboratorio medido una vez por hora."
        ),
        n_rows=4_097,
        caveats=(
            "The raw file repeats each hourly assay across every 20-second row, about 13.5 times. "
            "Fitting at row level leaks the target. The loader aggregates to the hourly grid and "
            "offers no row-level access at all.",
            "Both concentrate assays are excluded from the inputs: predicting silica from iron is "
            "reading the answer off the other half of the same measurement.",
            "The research dossier's recorded download URL served a completely unrelated dataset. The "
            "corrected source is verified by asserting the flotation schema before use.",
        ),
    ),
    Case(
        id="ore-mineralogy-closure", category="M",
        name_en="Ore mineralogy: the measured line against the stoichiometric one",
        name_es="Mineralogia del mineral: la recta medida frente a la estequiometrica",
        loader="ore-mineralogy-closure",
        variants=ladder_variants(("r1-koza-baseline", "r2-linear-scaling", "r3-constant-tuning",
                                  "r4-multi-objective"), population=200, generations=20),
        ground_truth_known=True, real_or_synthetic="real",
        summary_en=(
            "Iron feed grade against silica feed grade, on real plant data. If the ore were only "
            "hematite and quartz, stoichiometry fixes the line exactly. The measured line differs, and "
            "the size of that difference is a statement about the other minerals present. The lab "
            "reports both lines rather than choosing one."
        ),
        summary_es=(
            "Ley de hierro en la alimentacion frente a ley de silice, con datos reales de planta. Si el "
            "mineral fuera solo hematita y cuarzo, la estequiometria fija la recta exactamente. La recta "
            "medida difiere, y esa diferencia dice algo sobre los demas minerales presentes."
        ),
        n_rows=4_097,
        ground_truth_latex=r"\%\mathrm{Fe} = 69.94 - 0.699\,\%\mathrm{SiO_2}\quad\text{(two-mineral stoichiometry)}",
        caveats=(
            "Measured independently from the raw file during this build: the plant line is "
            "Fe = 67.08 - 0.736 Si with correlation -0.9718, against the stoichiometric 69.94 - 0.699.",
        ),
    ),
    _generator_case(
        "comminution-bond", category="M", name_es="Energia de conminucion: Bond, Kick y Rittinger",
        summary_en=(
            "Three classical comminution laws differ only in one exponent. Shipping them as COMPETING "
            "ground truths turns this into a model SELECTION question rather than a fitting question: "
            "which exponent do the data support, not how small can the residual be. The research found "
            "no published symbolic-regression work on the Bond work index at all."
        ),
        summary_es=(
            "Tres leyes clasicas de conminucion difieren solo en un exponente. Presentarlas como "
            "verdades RIVALES convierte esto en una pregunta de SELECCION de modelo."
        ),
    ),
    _generator_case(
        "flotation-kinetics", category="M", name_es="Cinetica de flotacion: recuperacion de primer orden",
        summary_en=(
            "First-order batch flotation recovery. The interesting question is not the fit but whether "
            "the data justify one rate constant or two: a single floatability component against a fast "
            "and a slow fraction. That is a genuine accuracy-versus-complexity Pareto decision on a "
            "real industrial problem, and it is the calibration twin of the plant soft-sensor case."
        ),
        summary_es=(
            "Recuperacion de flotacion batch de primer orden. La pregunta interesante no es el ajuste "
            "sino si los datos justifican una constante cinetica o dos."
        ),
    ),
    _generator_case(
        "two-product-recovery", category="M", name_es="Balance de dos productos: recuperacion metalurgica",
        summary_en=(
            "The metallurgical accounting identity every concentrator uses daily. The answer is a ratio "
            "of differences, which most search spaces reach only with a competent simplification stage, "
            "so a failure here is informative about the engine rather than about the data."
        ),
        summary_es=(
            "La identidad de balance metalurgico que toda concentradora usa a diario. La respuesta es "
            "una razon de diferencias, dificil de alcanzar sin una etapa de simplificacion competente."
        ),
    ),
    # ---------------------------------------------------------------- synthetic, cross-domain
    _generator_case(
        "friction-factor", category="S", name_es="Factor de friccion en tuberias",
        summary_en=(
            "The explicit turbulent friction correlation, and the calibration twin of the Nikuradse "
            "measured case. Fit the engine here where the answer is known, then take it there where it "
            "is not and the accepted correlation is visibly incomplete."
        ),
        summary_es=(
            "La correlacion explicita de friccion turbulenta, y el gemelo de calibracion del caso medido "
            "de Nikuradse."
        ),
    ),
    _generator_case(
        "heat-exchanger-ntu", category="S", name_es="Efectividad de intercambiador de calor (NTU)",
        summary_en=(
            "Counter-current effectiveness has a REMOVABLE SINGULARITY at equal heat capacity rates. A "
            "fitted expression that blows up there is wrong in a way a plain error metric hides "
            "completely, and only the extrapolation view exposes it."
        ),
        summary_es=(
            "La efectividad en contracorriente tiene una SINGULARIDAD EVITABLE cuando las capacidades "
            "termicas se igualan. Una expresion ajustada que diverge alli es incorrecta de un modo que "
            "una metrica de error simple oculta por completo."
        ),
    ),
    _generator_case(
        "nusselt-gnielinski", category="S", name_es="Transferencia de calor: Gnielinski",
        summary_en=(
            "Deliberately UNRECOVERABLE by the obvious hypothesis. A pure power law cannot fit data "
            "generated by this correlation at low Reynolds number. Reporting a good power-law fit here "
            "and stopping is exactly the failure this lab exists to demonstrate."
        ),
        summary_es=(
            "Deliberadamente IRRECUPERABLE con la hipotesis obvia. Una ley de potencias pura no puede "
            "ajustar datos generados por esta correlacion a bajo numero de Reynolds."
        ),
    ),
    _generator_case(
        "pump-affinity-power", category="S", name_es="Leyes de afinidad de bombas: potencia al eje",
        summary_en=(
            "The cleanest dimensional-analysis case in the set. With units enforced the exponents are "
            "forced by the physics; without units they must be found by search. Running the same case "
            "with rung 8 on and off is the whole argument for unit-typed generation."
        ),
        summary_es=(
            "El caso de analisis dimensional mas limpio del conjunto. Con unidades impuestas los "
            "exponentes quedan forzados por la fisica; sin unidades hay que encontrarlos por busqueda."
        ),
    ),
    _generator_case(
        "stokes-settling", category="S", name_es="Velocidad terminal de Stokes",
        summary_en=(
            "The target depends on a DIFFERENCE of densities. A fit that latches onto particle density "
            "alone looks excellent on a sample where fluid density barely varies, and is wrong. This is "
            "the clearest small example of a correct-looking fit that is the wrong law."
        ),
        summary_es=(
            "El objetivo depende de una DIFERENCIA de densidades. Un ajuste que se apoya solo en la "
            "densidad de la particula parece excelente y es incorrecto."
        ),
    ),
    _generator_case(
        "arrhenius-rate", category="S", name_es="Dependencia de Arrhenius con la temperatura",
        summary_en=(
            "A DIAGNOSTIC case. It does not test how good a search is, it tests whether the primitive "
            "set can express the answer at all: without a division inside an exponent, recovery is "
            "impossible and reporting that as a search failure would be a category error."
        ),
        summary_es=(
            "Un caso DIAGNOSTICO. No mide que tan buena es la busqueda, mide si el conjunto de "
            "primitivas puede siquiera expresar la respuesta."
        ),
    ),
    _generator_case(
        "monod-saturation", category="B", name_es="Saturacion de Michaelis-Menten y Monod",
        summary_en=(
            "The saturating hyperbola that is Michaelis-Menten in enzyme kinetics and Monod in "
            "fermentation, which is what makes it the bridge between the biology and industrial tracks."
        ),
        summary_es=(
            "La hiperbola de saturacion que es Michaelis-Menten en cinetica enzimatica y Monod en "
            "fermentacion, lo que la convierte en el puente entre biologia y proceso industrial."
        ),
        noise_levels=(0.0, 0.01, 0.05, 0.1),
    ),
    _generator_case(
        "theta-logistic-growth", category="B", name_es="Crecimiento poblacional theta-logistico",
        summary_en=(
            "Density-dependent population growth with a shape exponent. The real-data companion ships "
            "thousands of series WITH published fitted exponents, so a recovered value can be compared "
            "against a published one rather than only against a residual."
        ),
        summary_es=(
            "Crecimiento poblacional dependiente de la densidad con un exponente de forma, comparable "
            "contra exponentes publicados."
        ),
    ),
    _generator_case(
        "lotka-volterra-rhs", category="B", name_es="Lotka-Volterra: lado derecho de la presa",
        summary_en=(
            "The bilinear predator-prey interaction. Recovering the derivative and recovering the "
            "system's conserved quantity are DIFFERENT tasks on the same data, and the second is harder."
        ),
        summary_es=(
            "La interaccion bilineal depredador-presa. Recuperar la derivada y recuperar la cantidad "
            "conservada del sistema son tareas DISTINTAS sobre los mismos datos."
        ),
    ),
    _generator_case(
        "asm1-aerobic-growth", category="E", name_es="Crecimiento aerobio ASM1: producto de saturaciones",
        summary_en=(
            "A PRODUCT of two saturation functions, which has no additive decomposition. This is the "
            "case that separates engines doing a real multiplicative search from those that only "
            "assemble sums of terms."
        ),
        summary_es=(
            "Un PRODUCTO de dos funciones de saturacion, sin descomposicion aditiva. Este caso separa "
            "los motores con busqueda multiplicativa real de los que solo ensamblan sumas."
        ),
    ),
    _generator_case(
        "wind-power-curve", category="E", name_es="Curva de potencia de aerogenerador",
        summary_en=(
            "Piecewise by construction: zero below cut-in, cubic in wind speed, a rated plateau, then "
            "zero above cut-out. No single smooth expression represents it, so this case tests whether "
            "the search reports an honest partial fit or an overconfident smooth one."
        ),
        summary_es=(
            "Definida por tramos: cero bajo la velocidad de arranque, cubica, meseta nominal y cero "
            "sobre la de corte. Ninguna expresion suave unica la representa."
        ),
    ),
    _generator_case(
        "antoine-vapour-pressure", category="I", name_es="Presion de vapor de Antoine",
        summary_en=(
            "A reciprocal-shifted temperature form. The two-window variant asks the search to detect "
            "that a single constant set cannot cover the whole liquid range, which is a change-point "
            "question dressed as a fitting question."
        ),
        summary_es=(
            "Una forma reciproca desplazada en temperatura. La variante de dos ventanas pide detectar "
            "que un solo juego de constantes no cubre todo el rango liquido."
        ),
    ),
    _generator_case(
        "cstr-conversion", category="I", name_es="Conversion en reactor CSTR no isotermico",
        summary_en=(
            "Conversion saturates in the Damkohler number, and the Damkohler number itself hides an "
            "Arrhenius exponential. Two nested structures the search has to find together."
        ),
        summary_es=(
            "La conversion satura en el numero de Damkohler, y ese numero esconde a su vez una "
            "exponencial de Arrhenius. Dos estructuras anidadas que hay que hallar juntas."
        ),
    ),
)

_BY_ID: dict[str, Case] = {c.id: c for c in CASES}


def list_cases() -> list[Case]:
    return list(CASES)


def get_case(case_id: str) -> Case:
    if case_id not in _BY_ID:
        raise KeyError(f"unknown case: {case_id!r}. known: {sorted(_BY_ID)}")
    return _BY_ID[case_id]


def list_categories() -> dict[str, list[str]]:
    out: dict[str, list[str]] = {}
    for case in CASES:
        out.setdefault(case.category, []).append(case.id)
    return out


def coverage_summary() -> dict:
    """The coverage matrix the Experiments page reports, computed rather than typed."""
    by_category = list_categories()
    return {
        "n_cases": len(CASES),
        "n_categories": len(by_category),
        "categories": {CATEGORIES[k]: len(v) for k, v in sorted(by_category.items())},
        "ground_truth_known": sum(1 for c in CASES if c.ground_truth_known),
        "real": sum(1 for c in CASES if c.real_or_synthetic == "real"),
        "synthetic": sum(1 for c in CASES if c.real_or_synthetic == "synthetic"),
        "total_variants": sum(len(c.variants) for c in CASES),
        "min_variants": min(len(c.variants) for c in CASES),
        "max_variants": max(len(c.variants) for c in CASES),
    }
