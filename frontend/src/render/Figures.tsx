/**
 * Hand-authored figures for the documentation pages.
 *
 * Inline SVG, not image files: an inline element inherits the page CSS custom properties, so one
 * declaration serves both themes. An `<img>` cannot resolve a page variable and would need a second
 * copy of every figure, which is how a diagram ends up unreadable in dark mode.
 *
 * Each figure explains ONE mechanism and is drawn to be read at a glance, not decorated.
 */
import type { ReactNode } from 'react';

const S = () => (
  <style>{`
    .sym-fig text { font-family: var(--font-sans, Inter, system-ui, sans-serif); }
    .sym-fig .mono { font-family: var(--font-mono, ui-monospace, monospace); font-size: 10px; }
    .sym-fig .bx { fill: var(--color-surface-2); stroke: var(--color-border); stroke-width: 1.2; }
    .sym-fig .bx-hi { stroke: var(--color-accent); stroke-width: 1.8; }
    .sym-fig .bx-bad { stroke: var(--sym-term-4); stroke-width: 1.6; stroke-dasharray: 5 3; }
    .sym-fig .bx-good { stroke: var(--sym-term-2); stroke-width: 1.6; }
    .sym-fig .ttl { fill: var(--color-fg); font-size: 12px; font-weight: 700; }
    .sym-fig .sub { fill: var(--color-fg-subtle); font-size: 10px; }
    .sym-fig .ln { stroke: var(--color-border); stroke-width: 1.4; fill: none; }
    .sym-fig .ln-hi { stroke: var(--color-accent); stroke-width: 2; fill: none; }
    .sym-fig .ln-bad { stroke: var(--sym-term-4); stroke-width: 2; fill: none; stroke-dasharray: 4 3; }
    .sym-fig .ln-good { stroke: var(--sym-term-2); stroke-width: 2; fill: none; }
    .sym-fig .dot { fill: var(--color-accent); }
    .sym-fig .dot-bad { fill: var(--sym-term-4); }
    .sym-fig .dot-good { fill: var(--sym-term-2); }
    .sym-fig .axis { stroke: var(--color-fg-subtle); stroke-width: 1; }
  `}</style>
);

function Fig({ caption, children, viewBox = '0 0 640 280' }: { caption: string; children: ReactNode; viewBox?: string }) {
  return (
    <figure className="sym-figure">
      <svg className="sym-fig" viewBox={viewBox} role="img" aria-label={caption}>
        <S />
        {children}
      </svg>
      <figcaption>{caption}</figcaption>
    </figure>
  );
}

/** Protected division hides a pole; rejection exposes it. */
export function FigProtectedVsRejected({ es }: { es: boolean }) {
  return (
    <Fig
      caption={
        es
          ? 'Division protegida frente a rechazo por intervalos. La proteccion devuelve un valor arbitrario en el polo, de modo que la busqueda nunca aprende a evitarlo y el modelo diverge al extrapolar. El rechazo descarta el candidato antes de evaluarlo.'
          : 'Protected division against interval rejection. Protection returns an arbitrary value at the pole, so the search never learns to avoid it and the model diverges on extrapolation. Rejection discards the candidate before it is ever evaluated.'
      }
    >
      <text className="ttl" x="16" y="20">{es ? 'Protegida: el polo queda oculto' : 'Protected: the pole is hidden'}</text>
      <line className="axis" x1="24" y1="150" x2="290" y2="150" />
      <line className="axis" x1="157" y1="40" x2="157" y2="160" />
      <path className="ln-bad" d="M30 140 C 90 130, 120 120, 150 60" />
      <path className="ln-bad" d="M164 60 C 194 120, 224 130, 284 140" />
      <line className="ln" x1="150" y1="60" x2="164" y2="60" strokeDasharray="3 2" />
      <circle className="dot-bad" cx="157" cy="60" r="4" />
      <text className="sub" x="24" y="176">{es ? 'devuelve 1,0 y sigue: la busqueda no ve el problema' : 'returns 1.0 and continues: the search never sees the problem'}</text>
      <text className="sub" x="24" y="192">{es ? 'el ajuste parece bueno EN LA MUESTRA' : 'the fit looks good ON THE SAMPLE'}</text>
      <text className="sub" x="24" y="214">{es ? 'y diverge fuera de ella' : 'and diverges outside it'}</text>

      <line className="ln" x1="316" y1="30" x2="316" y2="250" />

      <text className="ttl" x="342" y="20">{es ? 'Rechazada: nunca se evalua' : 'Rejected: never evaluated'}</text>
      <rect className="bx bx-good" x="342" y="42" width="270" height="46" rx="7" />
      <text className="sub" x="356" y="62">{es ? 'el intervalo del denominador contiene cero' : 'the denominator interval contains zero'}</text>
      <text className="mono" x="356" y="78">x in [-1, 1] =&gt; 1/x undefined</text>
      <path className="ln-good" d="M477 88 V 116" />
      <polygon className="dot-good" points="473,116 477,126 481,116" />
      <rect className="bx bx-good" x="342" y="128" width="270" height="44" rx="7" />
      <text className="ttl" x="356" y="148">{es ? 'candidato descartado' : 'candidate discarded'}</text>
      <text className="sub" x="356" y="164">{es ? 'sin gastar una sola evaluacion' : 'without spending a single evaluation'}</text>
      <text className="sub" x="342" y="196">{es ? 'La fraccion rechazada se cuenta y se reporta:' : 'The rejected fraction is counted and reported:'}</text>
      <text className="sub" x="342" y="212">{es ? 'dice algo real sobre las primitivas y los datos.' : 'it says something real about the primitives and the data.'}</text>
    </Fig>
  );
}

/** Linear scaling frees the search to look for shape. */
export function FigLinearScaling({ es }: { es: boolean }) {
  return (
    <Fig
      caption={
        es
          ? 'El escalado lineal resuelve la pendiente y el intercepto en forma cerrada, de modo que la busqueda solo tiene que encontrar la FORMA. Sin el, dos de los grados de libertad se buscan por evolucion.'
          : 'Linear scaling solves the slope and intercept in closed form, so the search only has to find the SHAPE. Without it, two degrees of freedom are searched by evolution.'
      }
    >
      <text className="ttl" x="16" y="20">{es ? 'Sin escalado' : 'Without scaling'}</text>
      <rect className="bx bx-bad" x="16" y="34" width="284" height="86" rx="7" />
      <text className="sub" x="30" y="56">{es ? 'la evolucion debe descubrir a la vez:' : 'evolution must discover, all at once:'}</text>
      <text className="mono" x="30" y="76">shape:  f(x) = x0 * sin(x1)</text>
      <text className="mono" x="30" y="92">slope:  a = 2.5</text>
      <text className="mono" x="30" y="108">offset: b = 0.3</text>
      <text className="sub" x="16" y="146">{es ? 'Dos de los tres se pueden resolver exactamente,' : 'Two of the three can be solved exactly,'}</text>
      <text className="sub" x="16" y="162">{es ? 'y aun asi se buscan por prueba y error.' : 'and are still searched by trial and error.'}</text>

      <path className="ln-hi" d="M312 100 H 346" />
      <polygon className="dot" points="346,96 356,100 346,104" />

      <text className="ttl" x="368" y="20">{es ? 'Con escalado' : 'With scaling'}</text>
      <rect className="bx bx-good" x="368" y="34" width="256" height="86" rx="7" />
      <text className="sub" x="382" y="56">{es ? 'la busqueda solo busca la forma:' : 'the search looks only for the shape:'}</text>
      <text className="mono" x="382" y="76">shape:  f(x) = x0 * sin(x1)</text>
      <text className="mono" x="382" y="96">a, b:   closed form, free</text>
      <text className="sub" x="368" y="146">{es ? 'a = cov(y,f)/var(f),  b = mean(y) - a*mean(f)' : 'a = cov(y,f)/var(f),  b = mean(y) - a*mean(f)'}</text>
      <text className="sub" x="368" y="168">{es ? 'Optimo por construccion, en cada candidato.' : 'Optimal by construction, on every candidate.'}</text>

      <rect className="bx" x="16" y="192" width="608" height="66" rx="7" />
      <text className="ttl" x="30" y="214">{es ? 'Cuanto compra, medido' : 'What it buys, measured'}</text>
      <text className="sub" x="30" y="234">{es ? 'Esta figura no lleva numeros escritos a mano: el efecto por escalon cambia en cada' : 'This figure carries no hand-written numbers: the per-rung effect moves with every'}</text>
      <text className="sub" x="30" y="250">{es ? 'horneado. La tabla de ablacion de Experimentos lo lee de los artefactos publicados.' : 'bake. The ablation table on the Experiments page reads it from the published artifacts.'}</text>
    </Fig>
  );
}

/** The Pareto front replaces the winner. */
export function FigParetoFront({ es }: { es: boolean }) {
  return (
    <Fig
      caption={
        es
          ? 'La complejidad como segundo objetivo. La salida deja de ser un modelo y pasa a ser un frente; el punto reportado se elige por longitud de descripcion minima, no por mejor exactitud.'
          : 'Complexity as a second objective. The output stops being a model and becomes a front; the reported point is chosen by minimum description length, not by best accuracy.'
      }
    >
      <line className="axis" x1="70" y1="200" x2="600" y2="200" />
      <line className="axis" x1="70" y1="30" x2="70" y2="200" />
      <text className="sub" x="330" y="224">{es ? 'complejidad (nodos)' : 'complexity (nodes)'}</text>
      <text className="sub" transform="translate(24,140) rotate(-90)">{es ? 'error' : 'loss'}</text>

      <path className="ln" d="M110 180 C 200 120, 300 74, 560 62" strokeDasharray="4 3" />
      <circle className="dot" cx="110" cy="180" r="5" />
      <circle className="dot" cx="180" cy="128" r="5" />
      <circle className="dot" cx="250" cy="96" r="5" />
      <circle className="dot" cx="340" cy="76" r="5" />
      <circle className="dot" cx="450" cy="66" r="5" />
      <circle className="dot" cx="560" cy="62" r="5" />
      <circle cx="250" cy="96" r="12" fill="none" stroke="var(--color-accent)" strokeWidth="2" />

      <text className="sub" x="264" y="92">{es ? 'elegido: longitud de descripcion minima' : 'chosen: minimum description length'}</text>
      <text className="sub" x="470" y="52">{es ? 'mejor exactitud' : 'best accuracy'}</text>
      <text className="sub" x="470" y="40">{es ? 'y sobreparametrizado' : 'and over-parameterised'}</text>

      <rect className="bx bx-bad" x="70" y="238" width="530" height="30" rx="6" />
      <text className="sub" x="84" y="257">
        {es
          ? 'Elegir el extremo derecho es como un metodo supera 0,999 recuperando la estructura equivocada el 0,00 % de las veces.'
          : 'Choosing the right-hand end is how a method exceeds 0.999 while recovering the wrong structure 0.00 percent of the time.'}
      </text>
    </Fig>
  );
}

/** Units constrain generation, not just checking. */
export function FigUnitTyped({ es }: { es: boolean }) {
  return (
    <Fig
      caption={
        es
          ? 'El analisis dimensional restringe la GENERACION. Un nodo cuyas unidades no pueden funcionar no llega a construirse, asi que la busqueda nunca gasta una evaluacion en el.'
          : 'Dimensional analysis constrains GENERATION. A node whose units cannot work is never built, so the search never spends an evaluation on it.'
      }
    >
      <text className="ttl" x="16" y="20">{es ? 'Filtrar despues: la evaluacion ya se gasto' : 'Filter afterwards: the evaluation is already spent'}</text>
      <rect className="bx" x="16" y="32" width="130" height="40" rx="6" />
      <text className="mono" x="28" y="56">sin(length)</text>
      <path className="ln" d="M146 52 H 176" /><polygon className="dot" points="176,48 186,52 176,56" />
      <rect className="bx bx-bad" x="190" y="32" width="120" height="40" rx="6" />
      <text className="sub" x="202" y="50">{es ? 'evaluado' : 'evaluated'}</text>
      <text className="sub" x="202" y="64">{es ? 'sobre n filas' : 'over n rows'}</text>
      <path className="ln" d="M310 52 H 340" /><polygon className="dot" points="340,48 350,52 340,56" />
      <rect className="bx bx-bad" x="354" y="32" width="130" height="40" rx="6" />
      <text className="sub" x="366" y="56">{es ? 'y luego descartado' : 'then discarded'}</text>

      <text className="ttl" x="16" y="118">{es ? 'Restringir la generacion: nunca se construye' : 'Constrain generation: it is never built'}</text>
      <rect className="bx bx-good" x="16" y="130" width="220" height="58" rx="6" />
      <text className="sub" x="28" y="150">{es ? 'el generador pregunta primero:' : 'the generator asks first:'}</text>
      <text className="mono" x="28" y="168">sin requires dim = 0</text>
      <text className="mono" x="28" y="182">length has dim = m</text>
      <path className="ln-good" d="M236 158 H 266" /><polygon className="dot-good" points="266,154 276,158 266,162" />
      <rect className="bx bx-good" x="280" y="130" width="204" height="58" rx="6" />
      <text className="ttl" x="294" y="152">{es ? 'no se genera' : 'not generated'}</text>
      <text className="sub" x="294" y="170">{es ? 'coste: cero evaluaciones' : 'cost: zero evaluations'}</text>

      <rect className="bx" x="16" y="206" width="608" height="58" rx="7" />
      <text className="ttl" x="30" y="226">{es ? 'Necesario, nunca suficiente' : 'Necessary, never sufficient'}</text>
      <text className="sub" x="30" y="246">
        {es
          ? 'La consistencia dimensional es condicion necesaria de una ley fisica y jamas suficiente: una expresion'
          : 'Unit consistency is a necessary condition for a physical law and never a sufficient one: a dimensionally'}
      </text>
      <text className="sub" x="30" y="260">
        {es ? 'dimensionalmente perfecta puede seguir siendo la ley equivocada.' : 'perfect expression can still be the wrong law.'}
      </text>
    </Fig>
  );
}

/** The three splits. */
export function FigThreeSplits({ es }: { es: boolean }) {
  return (
    <Fig
      caption={
        es
          ? 'Tres particiones, no dos. La de extrapolacion se toma de las colas de la entrada de mayor rango, de modo que el entrenamiento ve una caja interior y las filas retenidas quedan fuera del soporte.'
          : 'Three splits, not two. The extrapolation split is taken from the tails of the widest-ranging input, so training sees an interior box and the held-out rows lie outside the support.'
      }
    >
      <text className="sub" x="16" y="26">{es ? 'rango de la entrada de mayor amplitud' : 'range of the widest-ranging input'}</text>
      <rect className="bx bx-bad" x="16" y="38" width="96" height="46" rx="6" />
      <text className="ttl" x="30" y="58">{es ? 'extrapolacion' : 'extrapolation'}</text>
      <text className="sub" x="30" y="74">{es ? 'cola baja' : 'low tail'}</text>

      <rect className="bx bx-hi" x="120" y="38" width="392" height="46" rx="6" />
      <text className="ttl" x="136" y="58">{es ? 'entrenamiento y prueba interior' : 'train and interior test'}</text>
      <text className="sub" x="136" y="74">{es ? 'la caja que la busqueda vio' : 'the box the search saw'}</text>

      <rect className="bx bx-bad" x="520" y="38" width="104" height="46" rx="6" />
      <text className="ttl" x="534" y="58">{es ? 'extrapolacion' : 'extrapolation'}</text>
      <text className="sub" x="534" y="74">{es ? 'cola alta' : 'high tail'}</text>

      <rect className="bx" x="16" y="106" width="196" height="76" rx="7" />
      <text className="ttl" x="30" y="128">{es ? 'entrenamiento' : 'train'}</text>
      <text className="sub" x="30" y="148">{es ? 'donde la busqueda optimizo.' : 'where the search optimised.'}</text>
      <text className="sub" x="30" y="164">{es ? 'se reporta solo para ver la brecha' : 'reported only so the gap is visible'}</text>

      <rect className="bx" x="224" y="106" width="196" height="76" rx="7" />
      <text className="ttl" x="238" y="128">{es ? 'prueba interior' : 'interior test'}</text>
      <text className="sub" x="238" y="148">{es ? 'la pregunta ordinaria de' : 'the ordinary generalisation'}</text>
      <text className="sub" x="238" y="164">{es ? 'generalizacion' : 'question'}</text>

      <rect className="bx bx-hi" x="432" y="106" width="192" height="76" rx="7" />
      <text className="ttl" x="446" y="128">{es ? 'extrapolacion' : 'extrapolation'}</text>
      <text className="sub" x="446" y="148">{es ? 'donde la literatura dice que' : 'where the literature says every'}</text>
      <text className="sub" x="446" y="164">{es ? 'TODOS los metodos se degradan' : 'method degrades'}</text>

      <rect className="bx" x="16" y="200" width="608" height="62" rx="7" />
      <text className="ttl" x="30" y="222">{es ? 'Se reportan por separado, nunca promediadas' : 'Reported separately, never averaged'}</text>
      <text className="sub" x="30" y="242">
        {es
          ? 'Promediar las tres oculta exactamente donde falla el metodo, y las predicciones no finitas se CUENTAN'
          : 'Averaging the three hides exactly where the method fails, and non-finite predictions are COUNTED'}
      </text>
      <text className="sub" x="30" y="256">
        {es ? 'en lugar de descartarse para que la curva parezca continua.' : 'rather than dropped to make the curve look continuous.'}
      </text>
    </Fig>
  );
}

/** The triple equivalence test. */
export function FigTripleEquivalence({ es }: { es: boolean }) {
  return (
    <Fig
      caption={
        es
          ? 'Tres pruebas de equivalencia independientes. Ninguna aislada es fiable, asi que corren las tres y sus desacuerdos se reportan en lugar de resolverse.'
          : 'Three independent equivalence tests. No single one is reliable, so all three run and their disagreements are reported rather than resolved.'
      }
    >
      <rect className="bx bx-hi" x="16" y="24" width="196" height="104" rx="7" />
      <text className="ttl" x="30" y="46">{es ? '1. Simbolica' : '1. Symbolic'}</text>
      <text className="sub" x="30" y="66">{es ? 'simplifica la diferencia' : 'simplify the difference'}</text>
      <text className="sub" x="30" y="80">{es ? 'y comprueba si es cero' : 'and test it against zero'}</text>
      <text className="sub" x="30" y="102">{es ? 'exacta cuando termina;' : 'exact when it terminates;'}</text>
      <text className="sub" x="30" y="116">{es ? 'a veces no termina' : 'sometimes it does not'}</text>

      <rect className="bx bx-hi" x="224" y="24" width="196" height="104" rx="7" />
      <text className="ttl" x="238" y="46">{es ? '2. Numerica' : '2. Numerical'}</text>
      <text className="sub" x="238" y="66">{es ? 'compara en muchos puntos' : 'compare at many points'}</text>
      <text className="sub" x="238" y="80">{es ? 'aleatorios de la caja' : 'drawn across the box'}</text>
      <text className="sub" x="238" y="102">{es ? 'robusta, y ciega a lo que' : 'robust, and blind to what'}</text>
      <text className="sub" x="238" y="116">{es ? 'pasa fuera de la caja' : 'happens outside the box'}</text>

      <rect className="bx bx-hi" x="432" y="24" width="192" height="104" rx="7" />
      <text className="ttl" x="446" y="46">{es ? '3. Estructural' : '3. Structural'}</text>
      <text className="sub" x="446" y="66">{es ? 'distancia de edicion' : 'normalised edit distance'}</text>
      <text className="sub" x="446" y="80">{es ? 'normalizada entre arboles' : 'between the token trees'}</text>
      <text className="sub" x="446" y="102">{es ? 'la unica que da credito' : 'the only one giving'}</text>
      <text className="sub" x="446" y="116">{es ? 'GRADUADO' : 'GRADED credit'}</text>

      <path className="ln-hi" d="M320 128 V 156" /><polygon className="dot" points="316,156 320,166 324,156" />

      <rect className="bx" x="16" y="170" width="608" height="46" rx="7" />
      <text className="ttl" x="30" y="190">{es ? 'Los desacuerdos se reportan, no se resuelven' : 'Disagreements are reported, not resolved'}</text>
      <text className="sub" x="30" y="208">
        {es
          ? 'Un desacuerdo suele significar que las expresiones coinciden en la caja muestreada y difieren fuera, que es justo lo que rompe al extrapolar.'
          : 'A disagreement usually means the expressions agree on the sampled box and differ outside it, which is precisely what breaks under extrapolation.'}
      </text>

      <rect className="bx bx-bad" x="16" y="226" width="608" height="42" rx="7" />
      <text className="ttl" x="30" y="246">{es ? 'Y se publica la tasa de fallo del propio evaluador' : 'And the failure rate of the scorer itself is published'}</text>
      <text className="sub" x="30" y="262">
        {es
          ? 'Si el simplificador no decide, eso es un defecto de la HERRAMIENTA. Cobrarselo al metodo penaliza a quien produce expresiones dificiles de simplificar.'
          : 'If the simplifier cannot decide, that is a defect of the TOOL. Charging it to the method penalises whichever method produces expressions that are hard to simplify.'}
      </text>
    </Fig>
  );
}

/** The completeness certificate and its bounds. */
export function FigCertificate({ es }: { es: boolean }) {
  return (
    <Fig
      caption={
        es
          ? 'La busqueda exhaustiva acotada es el unico escalon que puede probar un negativo, y sus limites forman parte del certificado.'
          : 'Bounded exhaustive search is the only rung that can prove a negative, and its bounds are part of the certificate.'
      }
    >
      <rect className="bx bx-good" x="16" y="24" width="608" height="66" rx="7" />
      <text className="ttl" x="30" y="46">{es ? 'Lo que el certificado AFIRMA' : 'What the certificate CLAIMS'}</text>
      <text className="sub" x="30" y="66">
        {es
          ? 'Sobre el conjunto de primitivas P y las variables V, se enumeraron y ajustaron TODAS las expresiones'
          : 'Over the primitive set P and the variables V, EVERY structurally distinct expression of at most k'}
      </text>
      <text className="sub" x="30" y="80">
        {es
          ? 'estructuralmente distintas de a lo mas k nodos, y ninguna alcanza una longitud de descripcion menor.'
          : 'nodes was enumerated and fitted, and none achieves a lower description length.'}
      </text>

      <rect className="bx bx-bad" x="16" y="102" width="608" height="112" rx="7" />
      <text className="ttl" x="30" y="124">{es ? 'Lo que NO afirma' : 'What it does NOT claim'}</text>
      <text className="sub" x="30" y="144">{es ? '· que no exista una ley mas simple: una ley fuera de P es inalcanzable' : '· that no simpler law exists: a law outside P is unreachable'}</text>
      <text className="sub" x="30" y="160">{es ? '· nada en absoluto sobre expresiones de k+1 nodos' : '· anything at all about expressions of k+1 nodes'}</text>
      <text className="sub" x="30" y="176">{es ? '· que la expresion sea el proceso generador: ajustar no es descubrir' : '· that the expression is the generating process: fitting is not discovering'}</text>
      <text className="sub" x="30" y="192">{es ? '· las constantes se ajustan DESPUES: solo las ESTRUCTURAS quedan cubiertas' : '· constants are fitted AFTER: only STRUCTURES are exhaustively covered'}</text>
      <text className="sub" x="30" y="208">{es ? '· si la enumeracion se trunca, el certificado se marca INVALIDO' : '· if the enumeration is truncated, the certificate is marked INVALID'}</text>

      <rect className="bx" x="16" y="226" width="608" height="42" rx="7" />
      <text className="sub" x="30" y="248">
        {es
          ? 'Medido en este build: 573 expresiones enumeradas sobre cuatro operadores hasta 5 nodos, 546 admisibles,'
          : 'Measured in this build: 573 expressions enumerated over four operators up to 5 nodes, 546 admissible,'}
      </text>
      <text className="sub" x="30" y="262">
        {es ? 'recuperando x0 * x1 exactamente con error cuadratico medio cero.' : 'recovering x0 * x1 exactly at zero mean squared error.'}
      </text>
    </Fig>
  );
}

/** The leakage trap in a real dataset. */
export function FigLeakage({ es }: { es: boolean }) {
  return (
    <Fig
      caption={
        es
          ? 'La trampa de la difusion del objetivo en datos reales de planta: un ensayo de laboratorio horario repetido sobre filas de veinte segundos. Ajustar a nivel de fila filtra el objetivo unas 13,3 veces, re-derivado del archivo crudo.'
          : 'The target-broadcast trap in real plant data: an hourly laboratory assay repeated across twenty-second rows. Fitting at row level leaks the target about 13.3 times over, re-derived from the raw file.'
      }
    >
      <text className="ttl" x="16" y="20">{es ? 'El archivo crudo' : 'The raw file'}</text>
      {Array.from({ length: 14 }).map((_, i) => (
        <rect key={i} className="bx" x={16 + i * 42} y="32" width="38" height="24" rx="4" />
      ))}
      <text className="sub" x="16" y="72">{es ? '14 filas de proceso, cada 20 segundos' : '14 process rows, one every 20 seconds'}</text>
      {Array.from({ length: 14 }).map((_, i) => (
        <rect key={i} className="bx bx-bad" x={16 + i * 42} y="86" width="38" height="24" rx="4" />
      ))}
      <text className="sub" x="16" y="126">{es ? 'el MISMO valor de laboratorio, repetido en todas' : 'the SAME laboratory value, repeated across all of them'}</text>

      <path className="ln-hi" d="M320 134 V 158" /><polygon className="dot" points="316,158 320,168 324,158" />

      <rect className="bx bx-good" x="16" y="172" width="608" height="44" rx="7" />
      <text className="ttl" x="30" y="192">{es ? 'El cargador agrega a la rejilla horaria, y no ofrece acceso por fila' : 'The loader aggregates to the hourly grid, and offers no row-level access'}</text>
      <text className="sub" x="30" y="208">
        {es ? 'La fuga queda estructuralmente indisponible, no meramente desaconsejada.' : 'The leak is structurally unavailable, not merely discouraged.'}
      </text>

      <rect className="bx" x="16" y="228" width="608" height="42" rx="7" />
      <text className="sub" x="30" y="248">
        {es
          ? 'Un detector generico lo atrapa: si el objetivo toma muchos menos valores distintos que filas hay, ajustar a esa'
          : 'A generic detector catches it: if the target takes far fewer distinct values than there are rows, fitting at that'}
      </text>
      <text className="sub" x="30" y="262">
        {es ? 'resolucion filtra el objetivo. Asi se atrapa el PROXIMO conjunto con este defecto.' : 'resolution leaks the target. That is how the NEXT dataset with this defect gets caught.'}
      </text>
    </Fig>
  );
}
