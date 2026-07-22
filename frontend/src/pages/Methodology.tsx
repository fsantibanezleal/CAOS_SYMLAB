import { Callout, Cite, Equation, InlineMath, Refs, SubTabs } from '@fasl-work/caos-app-shell';

import {
  FigCertificate,
  FigLinearScaling,
  FigParetoFront,
  FigProtectedVsRejected,
  FigTripleEquivalence,
  FigUnitTyped,
} from '../render/Figures';

import { useLang } from '../lib/useLang';

/**
 * Methodology: one sub-tab per method family, each with the mathematics this build actually uses.
 *
 * The exact constants and behaviours of THIS implementation are stated, not the general idea from
 * the paper. A methodology page that describes the literature rather than the build is a reading
 * list, and a reader cannot use it to check a number.
 */
export default function Methodology() {
  const es = useLang() === 'es';

  const tabs = [
    {
      id: 'representation',
      label: es ? 'Representacion' : 'Representation',
      content: (
        <section>
          <h3>{es ? 'El arbol de expresion, y por que no hay operadores protegidos' : 'The expression tree, and why there are no protected operators'}</h3>
          <p>
            {es
              ? 'Una expresion es un arbol inmutable. Los nodos no llevan identidad propia: se les asigna por un recorrido en preorden, de modo que el espacio de identificadores enteros es IDENTICO en las anotaciones LaTeX, en la lista plana de nodos que se envia a la web y en las referencias por termino. Ese espacio compartido no es una comodidad: es lo que permite que resaltar un termino en la ecuacion resalte el mismo subarbol en el arbol sin un segundo mapeo paralelo.'
              : 'An expression is an immutable tree. Nodes carry no identity of their own: it is assigned by a pre-order walk, so the integer id space is IDENTICAL in the LaTeX annotations, the flat node list shipped to the web, and the per-term references. That shared space is not a convenience: it is what lets highlighting a term in the equation highlight the same subtree in the tree with no second parallel mapping.'}
          </p>
          <p>
            {es
              ? 'La decision que mas separa esta implementacion de una de tutorial es la ausencia de operadores protegidos. La costumbre clasica define una division protegida que devuelve 1,0 cuando el denominador es cero. Eso cambia en silencio la funcion que se esta buscando: la busqueda nunca aprende a evitar la singularidad y la expresion resultante solo tiene sentido en la muestra con la que se ajusto. En el momento en que se extrapola, la proteccion ya no esta y el modelo diverge.'
              : 'The decision that most separates this implementation from a tutorial one is the absence of protected operators. The classical habit defines a protected division returning 1.0 when the denominator is zero. That silently changes the function being searched: the search never learns to avoid the singularity, and the resulting expression is only meaningful on the sample it was fitted to. The moment you extrapolate, the protection is gone and the model diverges.'}{' '}
            <Cite id="keijzer2003" paren />
          </p>
          <Equation
            tex="\text{admissible}(f) \iff \forall \mathbf{x} \in B: \; f(\mathbf{x}) \in \mathbb{R} \;\wedge\; |f(\mathbf{x})| \le M"
            caption={
              es
                ? 'La condicion de admisibilidad. B es la caja de entrada, ensanchada mas alla del rango de entrenamiento; M es una cota de magnitud que descarta expresiones definidas pero numericamente inutiles.'
                : 'The admissibility condition. B is the input box, widened beyond the training range; M is a magnitude bound that discards expressions that are defined but numerically useless.'
            }
          />
          <FigProtectedVsRejected es={es} />
          <Callout variant="honest" title={es ? 'Lo que esto cuesta' : 'What this costs'}>
            <p>
              {es
                ? 'Rechazar en lugar de proteger descarta candidatos que un motor con proteccion habria mantenido. Esa fraccion rechazada se cuenta y se reporta en cada variante, porque dice algo real sobre el conjunto de primitivas y los datos, no porque sea un detalle de implementacion.'
                : 'Rejecting rather than protecting discards candidates a protected engine would have kept. That rejected fraction is counted and reported on every variant, because it says something real about the primitive set and the data, not because it is an implementation detail.'}
            </p>
          </Callout>
          <Refs ids={['koza1992', 'keijzer2003']} label={es ? 'Referencias' : 'References'} />
        </section>
      ),
    },
    {
      id: 'scaling',
      label: es ? 'Escalado y ajuste' : 'Scaling and fitting',
      content: (
        <section>
          <h3>{es ? 'Resolver lo que no hace falta evolucionar' : 'Solving what does not need to be evolved'}</h3>
          <p>
            {es
              ? 'Una busqueda de arboles gasta una parte sorprendente de su presupuesto empujando hojas numericas hacia valores que un optimizador local alcanza en unas pocas iteraciones. Dos mecanismos atacan eso, y son complementarios.'
              : 'A tree search spends a surprising share of its budget nudging numeric leaves towards values a local optimiser reaches in a handful of iterations. Two mechanisms address that, and they are complementary.'}
          </p>
          <p>
            {es
              ? 'El primero es el escalado lineal. Para un objetivo de error cuadratico, la pendiente y el intercepto optimos tienen forma cerrada, asi que no hay que buscarlos: la busqueda queda libre para buscar la FORMA de la relacion, que es en lo que la evolucion es realmente buena.'
              : 'The first is linear scaling. For a squared-error objective the optimal slope and intercept have a closed form, so they need not be searched: the search is freed to look for the SHAPE of the relationship, which is what evolution is actually good at.'}
          </p>
          <Equation
            tex="a = \frac{\operatorname{cov}(y, f)}{\operatorname{var}(f)}, \qquad b = \bar{y} - a\,\bar{f}"
            caption={
              es
                ? 'Pendiente e intercepto optimos en forma cerrada. El candidato escalado a*f + b es optimo en a y b por construccion.'
                : 'Closed-form optimal slope and intercept. The scaled candidate a*f + b is optimal in a and b by construction.'
            }
          />
          <p>
            {es
              ? 'El segundo es el ajuste no lineal de TODAS las hojas numericas por Levenberg-Marquardt, reescrito en el arbol para que la mejora se herede en lugar de redescubrirse cada generacion. Se detecta explicitamente un jacobiano de rango deficiente: cuando dos constantes son redundantes, infinitos pares dan la misma salida y los valores ajustados no llevan informacion, asi que se reportan como no identificables en vez de presentarse como si la llevaran.'
              : 'The second is nonlinear fitting of ALL numeric leaves by Levenberg-Marquardt, written back into the tree so the improvement is inherited rather than rediscovered each generation. A rank-deficient Jacobian is detected explicitly: when two constants are redundant, infinitely many pairs give the same output and the fitted values carry no information, so they are reported as not identifiable rather than presented as if they did.'}{' '}
            <Cite id="kommenda2020" paren />
          </p>
          <FigLinearScaling es={es} />
          <Callout variant="honest" title={es ? 'El escalado cambia lo que significa la expresion' : 'Scaling changes what the expression means'}>
            <p>
              {es
                ? 'La expresion que se reporta es la ESCALADA, con a y b plegados dentro como constantes explicitas. Reportar el esqueleto sin escalar y puntuarlo escalado inflaria cada numero, asi que la expresion mostrada es exactamente la que se puntuo.'
                : 'The expression reported is the SCALED one, with a and b folded in as explicit constants. Reporting an unscaled skeleton and scoring it scaled would inflate every number, so the expression shown is exactly the one that was scored.'}
            </p>
          </Callout>
          <Refs ids={['keijzer2003', 'kommenda2020']} label={es ? 'Referencias' : 'References'} />
        </section>
      ),
    },
    {
      id: 'selection',
      label: es ? 'Seleccion y supervivencia' : 'Selection and survival',
      content: (
        <section>
          <h3>{es ? 'Cuatro teorias distintas de quien se reproduce' : 'Four different theories of who reproduces'}</h3>
          <p>
            {es
              ? 'La seleccion por torneo elige el mejor de un punado al azar juzgando el error agregado. Su debilidad conocida es que el error agregado oculta QUE casos resuelve cada candidato: dos con la misma media pueden ser buenos en partes disjuntas del problema.'
              : 'Tournament selection picks the best of a random handful judged on aggregate error. Its known weakness is that aggregate error hides WHICH cases each candidate solves: two with the same mean can be good at disjoint parts of the problem.'}
          </p>
          <p>
            {es
              ? 'La seleccion epsilon-lexicase juzga un caso de entrenamiento a la vez, en orden aleatorio, conservando solo los que quedan dentro de epsilon del mejor en ese caso. Epsilon se fija automaticamente desde la desviacion absoluta mediana de los errores de ese caso, que es lo que la hace funcionar sobre objetivos continuos.'
              : 'Epsilon-lexicase selection judges one training case at a time, in random order, keeping only those within epsilon of the best on that case. Epsilon is set automatically from the median absolute deviation of that case errors, which is what makes it work on continuous targets at all.'}{' '}
            <Cite id="lacava2016" paren />
          </p>
          <Equation
            tex="\varepsilon_j = \operatorname{median}_i \big| e_{ij} - \operatorname{median}_k e_{kj} \big|"
            caption={
              es
                ? 'El epsilon automatico para el caso j: la desviacion absoluta mediana de los errores en ese caso, entre los individuos que aun sobreviven.'
                : 'The automatic epsilon for case j: the median absolute deviation of the errors on that case, across the individuals still surviving.'
            }
          />
          <FigParetoFront es={es} />
          <Callout variant="honest" title={es ? 'Lo que cuesta, medido en este build' : 'What it costs, measured in this build'}>
            <p>
              {es
                ? 'Con poblacion 100 sobre 10 generaciones y 120 filas: la base tarda 0,30 s, anadir epsilon-lexicase la lleva a 6,73 s, anadir deduplicacion a 0,75 s, y ambas juntas a 13,43 s. Es decir, lexicase domina el costo por un orden de magnitud sobre la deduplicacion.'
                : 'At population 100 over 10 generations on 120 rows: the baseline takes 0.30 s, adding epsilon-lexicase takes it to 6.73 s, adding deduplication takes it to 0.75 s, and both together 13.43 s. Epsilon-lexicase dominates the cost by an order of magnitude over deduplication.'}
            </p>
            <p>
              {es
                ? 'Ese numero se publica porque un metodo de seleccion que compra calidad a 22 veces el tiempo debe compararse a igual PRESUPUESTO, no a igual numero de generaciones. La injusticia de presupuesto es uno de los problemas que la propia literatura de benchmarks reconoce. El 22 viene de una medicion AISLADA con presupuesto pequeno a proposito, asi que es una atribucion limpia y no una cifra de titular: la pagina de Experimentos reporta lo que cuesta cada escalon con los presupuestos PUBLICADOS, sobre los casos reales, y esos multiplos son mayores. Ambos son ciertos y miden cosas distintas.'
                : 'That number is published because a selection method buying quality at 22 times the wall clock must be compared at equal BUDGET, not at equal generation count. Budget unfairness is one of the standing problems the benchmark literature acknowledges itself. The 22 comes from an ISOLATED measurement at a deliberately small budget, so it is a clean attribution rather than a headline figure: the Experiments page reports what each rung costs at the PUBLISHED budgets, over the real cases, and those multiples are larger. Both are true and they measure different things.'}
            </p>
          </Callout>
          <p>
            {es
              ? 'La supervivencia NSGA-II deja de tratar la complejidad como una penalizacion y la convierte en un segundo objetivo, con orden de no dominacion y distancia de aglomeracion para romper empates. Los puntos extremos reciben distancia infinita, que es lo que impide que el frente colapse hacia su centro con las generaciones.'
              : 'NSGA-II survival stops treating complexity as a penalty and makes it a second objective, with non-domination rank and crowding distance breaking ties. Boundary points get infinite distance, which is what stops a front collapsing towards its middle over generations.'}{' '}
            <Cite id="deb2002" paren />
          </p>
          <p>
            {es
              ? 'La supervivencia Pareto edad-aptitud anade la EDAD como objetivo: un individuo joven solo tiene que superar a los viejos en error para sobrevivir, de modo que la busqueda mantiene material fresco y deja de converger prematuramente sobre un unico linaje. Es la receta de Eureqa y es barata.'
              : 'Age-fitness Pareto survival adds AGE as an objective: a young individual only has to beat older ones on error to survive, so the search keeps a supply of fresh material and stops converging prematurely onto one lineage. It is the Eureqa recipe and it is cheap.'}{' '}
            <Cite id="schmidt2011" paren />
          </p>
          <Refs ids={['lacava2016', 'deb2002', 'schmidt2011']} label={es ? 'Referencias' : 'References'} />
        </section>
      ),
    },
    {
      id: 'units',
      label: es ? 'Unidades como restriccion' : 'Units as a constraint',
      content: (
        <section>
          <h3>{es ? 'Restringir la generacion, no filtrar despues' : 'Constraining generation, not filtering afterwards'}</h3>
          <p>
            {es
              ? 'Cada cantidad lleva un vector de siete exponentes sobre las dimensiones base del SI. Hay dos usos, y son distintos en naturaleza. Comprobar una expresion terminada es un filtro y es el uso debil. Restringir la GENERACION, negandose a construir un nodo cuyas unidades no pueden funcionar, es el uso fuerte: la busqueda nunca gasta una evaluacion en el seno de una longitud ni en sumar una masa a un tiempo.'
              : 'Every quantity carries a seven-vector of exponents over the SI base dimensions. There are two uses and they differ in kind. Checking a finished expression is a filter and is the weaker use. Constraining GENERATION, refusing to build a node whose units cannot work, is the strong use: the search never spends an evaluation on the sine of a length or on adding a mass to a time.'}
          </p>
          <Equation
            tex="\dim(a \cdot b) = \dim(a) + \dim(b), \quad \dim(a/b) = \dim(a) - \dim(b), \quad \dim(\sin a) \text{ requires } \dim(a) = \mathbf{0}"
            caption={
              es
                ? 'Las reglas dimensionales que gobiernan la generacion. Una raiz cuadrada halva los exponentes y se RECHAZA cuando alguno es impar, porque ese resultado no existe en la red de exponentes enteros.'
                : 'The dimensional rules that govern generation. A square root halves the exponents and is REFUSED when any is odd, because that result does not exist in the integer exponent lattice.'
            }
          />
          <FigUnitTyped es={es} />
          <Callout variant="honest" title={es ? 'Necesario, nunca suficiente' : 'Necessary, never sufficient'}>
            <p>
              {es
                ? 'La consistencia de unidades es una condicion necesaria para una ley fisica y nunca una suficiente. Una expresion dimensionalmente perfecta puede seguir siendo la ley equivocada, y por eso el protocolo de evaluacion de este laboratorio existe: un ajuste plausible no es un descubrimiento.'
                : 'Unit consistency is a necessary condition for a physical law and never a sufficient one. A dimensionally perfect expression can still be the wrong law, which is exactly why this lab has an evaluation protocol: a plausible-looking fit is not a discovery.'}
            </p>
          </Callout>
          <Refs ids={['buckingham1914', 'tenachi2023']} label={es ? 'Referencias' : 'References'} />
        </section>
      ),
    },
    {
      id: 'complexity',
      label: es ? 'Complejidad y seleccion' : 'Complexity and selection',
      content: (
        <section>
          <h3>{es ? 'Tres medidas, y la regla que elige un punto' : 'Three measures, and the rule that picks one point'}</h3>
          <p>
            {es
              ? 'El conteo de nodos es el estandar del campo y tiene una debilidad que sus propios autores reconocen: ignora la no linealidad anidada. Un seno de un seno de un seno y una suma de tres variables puntuan casi igual, y solo una de las dos es dificil de razonar.'
              : 'Node count is the field default and has a weakness its own authors acknowledge: it ignores nested nonlinearity. A sine of a sine of a sine and a sum of three variables score about the same, and only one of them is hard to reason about.'}
          </p>
          <p>
            {es
              ? 'La longitud de descripcion es la unica de las tres que compara exactitud y complejidad en una escala comun, y por eso es la que realmente selecciona un modelo en lugar de dejar el compromiso al ojo del lector.'
              : 'Description length is the only one of the three that trades accuracy against complexity on a common scale, which is why it is the one that actually selects a model rather than leaving the trade to the reader eye.'}
          </p>
          <Equation
            tex="L(f, D) = \underbrace{|f| \ln |\Sigma|}_{\text{structure}} + \underbrace{k \, \ln 2^{16}}_{\text{constants}} + \underbrace{\tfrac{n}{2}\Big(\ln(2\pi\hat{\sigma}^2) + 1\Big)}_{\text{residuals}}"
            caption={
              es
                ? 'Longitud de descripcion en nats. El primer termino cobra por escribir la estructura, el segundo por cada constante ajustada a una precision declarada, y el tercero por codificar los residuos. Las tres partes viajan en el artefacto para que el compromiso sea visible.'
                : 'Description length in nats. The first term charges for writing the structure down, the second for each fitted constant at a stated precision, and the third for coding the residuals. All three parts travel in the artifact so the trade-off is visible.'
            }
          />
          <ul>
            <li>
              <InlineMath tex="|f|" /> {es ? 'el numero de nodos' : 'the node count'}
            </li>
            <li>
              <InlineMath tex="|\Sigma|" />{' '}
              {es ? 'el tamano del alfabeto: primitivas mas variables mas el simbolo de constante' : 'the alphabet size: primitives plus variables plus the constant symbol'}
            </li>
            <li>
              <InlineMath tex="k" /> {es ? 'el numero de constantes numericas ajustadas' : 'the number of fitted numeric constants'}
            </li>
            <li>
              <InlineMath tex="\hat{\sigma}^2" /> {es ? 'la varianza residual de maxima verosimilitud' : 'the maximum-likelihood residual variance'}
            </li>
          </ul>
          <FigTripleEquivalence es={es} />
          <Callout variant="honest" title={es ? 'Por que NO se elige por mejor exactitud' : 'Why the choice is NOT best accuracy'}>
            <p>
              {es
                ? 'Elegir el miembro mas exacto del frente reproduce exactamente el fallo principal del campo, porque el miembro mas exacto suele ser el mas sobreparametrizado. La regla por defecto aqui es longitud de descripcion minima, y el punto elegido se marca con un anillo en el frente para que la eleccion sea visible y discutible.'
                : 'Choosing the most accurate member of the front reproduces the field headline failure exactly, because the most accurate member is routinely the most over-parameterised one. The default rule here is minimum description length, and the chosen point is ringed on the front so the choice is visible and arguable.'}
            </p>
          </Callout>
          <Refs ids={['rissanen1978', 'defranca2024']} label={es ? 'Referencias' : 'References'} />
        </section>
      ),
    },
    {
      id: 'exhaustive',
      label: es ? 'Busqueda exhaustiva' : 'Exhaustive search',
      content: (
        <section>
          <h3>{es ? 'El unico escalon que puede probar un negativo' : 'The only rung that can prove a negative'}</h3>
          <p>
            {es
              ? 'Todos los demas metodos devuelven la mejor expresion que ENCONTRARON. La enumeracion acotada devuelve la mejor que EXISTE, hasta una complejidad dada sobre un conjunto de primitivas dado. Esa diferencia es lo que justifica su costo, y tambien lo que la convierte en la mejor demostracion interactiva del producto: el espacio es finito y se puede ver encogerse cuando se aprietan las restricciones.'
              : 'Every other method returns the best expression it FOUND. Bounded enumeration returns the best that EXISTS, up to a given complexity over a given primitive set. That difference is what justifies its cost, and also what makes it the best interactive demonstration in the product: the space is finite and can be watched shrinking as the constraints tighten.'}
          </p>
          <FigCertificate es={es} />
          <Callout variant="honest" title={es ? 'La redaccion exacta del certificado importa' : 'The exact wording of the certificate matters'}>
            <p>
              {es
                ? 'Lo que dice: sobre el conjunto de primitivas P y las variables V, se enumeraron y ajustaron todas las expresiones estructuralmente distintas de a lo mas k nodos, y ninguna alcanza una longitud de descripcion menor que la reportada.'
                : 'What it says: over the primitive set P and the variables V, every structurally distinct expression of at most k nodes was enumerated and fitted, and none achieves a lower description length than the one reported.'}
            </p>
            <p>
              {es
                ? 'Lo que NO dice: que no exista una ley mas simple (una ley fuera de P es inalcanzable), que la expresion reportada sea el proceso generador real (ajustar no es descubrir), ni absolutamente nada sobre expresiones de k+1 nodos. Ademas, las constantes se ajustan numericamente DESPUES de enumerar, asi que solo las ESTRUCTURAS quedan cubiertas exhaustivamente.'
                : 'What it does NOT say: that no simpler law exists (a law outside P is unreachable), that the reported expression is the true generating process (fitting is not discovering), or anything at all about expressions of k+1 nodes. And constants are fitted numerically AFTER enumeration, so only expression STRUCTURES are exhaustively covered.'}
            </p>
            <p>
              {es
                ? 'Si la enumeracion alcanza su tope, el certificado se marca INVALIDO y se dice explicitamente. Una enumeracion truncada no prueba nada y jamas debe presentarse como si lo hiciera.'
                : 'If the enumeration hits its cap, the certificate is marked INVALID and says so explicitly. A truncated enumeration proves nothing and must never be presented as if it did.'}
            </p>
          </Callout>
          <Refs ids={['bartlett2023', 'guimera2020']} label={es ? 'Referencias' : 'References'} />
        </section>
      ),
    },
  ];

  return (
    <div className="page-body prose">
      <div className="page-head">
        <h1>{es ? 'Metodologia' : 'Methodology'}</h1>
        <p className="lede">
          {es
            ? 'Cada familia de metodos, con la matematica que este build usa realmente y las constantes exactas que aplica. Lo que sigue describe la implementacion, no la idea general del articulo: una pagina que describe la literatura en vez del build es una lista de lectura, y con ella un lector no puede comprobar ningun numero.'
            : 'Each method family, with the mathematics this build actually uses and the exact constants it applies. What follows describes the implementation, not the general idea from the paper: a page describing the literature rather than the build is a reading list, and a reader cannot check a number with it.'}
        </p>
      </div>
      <SubTabs tabs={tabs} ariaLabel={es ? 'Familias de metodos' : 'Method families'} />
    </div>
  );
}
