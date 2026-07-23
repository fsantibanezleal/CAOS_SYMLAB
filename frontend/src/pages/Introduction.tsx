import { Callout, Cite, Equation, InlineMath, Refs } from '@fasl-work/caos-app-shell';

import { useLang } from '../lib/useLang';

/**
 * Introduction: what the problem is, why it is hard, and what this lab will and will not claim.
 *
 * The honesty section is not a disclaimer at the end. It is placed where a reader arrives at it
 * before they have formed an impression, because the single most useful thing this page can do is
 * stop someone reading a good fit as a discovery.
 */
export default function Introduction() {
  const es = useLang() === 'es';

  return (
    <div className="page-body prose">
      <div className="page-head">
        <h1>{es ? 'Introduccion' : 'Introduction'}</h1>
        <p className="lede">
          {es ? (
            <>
              La regresion simbolica busca una expresion explicita <InlineMath tex="f(\mathbf{x})" /> que
              explique los datos, en lugar de ajustar una funcion cuyo interior nadie puede leer. Este
              laboratorio recorre dos familias de busqueda sobre los mismos casos abiertos con el mismo
              protocolo, una escalera de programacion genetica y un brazo disperso no evolutivo, y reporta un
              frente de Pareto de leyes candidatas en vez de un ganador. No afirma que la regresion simbolica
              descubra leyes naturales: esa distincion es el tema de esta pagina.
            </>
          ) : (
            <>
              Symbolic regression searches for an explicit expression <InlineMath tex="f(\mathbf{x})" /> that
              explains the data, rather than fitting a function whose internals nobody can read. This lab runs
              two search families over the same open cases with the same protocol, a genetic-programming
              ladder and a non-evolutionary sparse arm, and reports a Pareto front of candidate laws rather
              than a winner. It does not claim that symbolic regression discovers natural laws, and that
              distinction is what this page is about.
            </>
          )}
        </p>
      </div>

      <section>
        <h2>{es ? 'El problema, dicho con precision' : 'The problem, stated precisely'}</h2>
        <p>
          {es
            ? 'Dado un conjunto de pares entrada-salida, se busca una expresion construida a partir de un conjunto declarado de primitivas y de las variables de entrada, que minimice conjuntamente el error y la complejidad. Las dos partes importan: minimizar solo el error produce expresiones enormes que ajustan el ruido, y minimizar solo la complejidad produce una constante.'
            : 'Given a set of input-output pairs, the task is to find an expression built from a declared set of primitives and the input variables, minimising error and complexity jointly. Both halves matter: minimising error alone produces enormous expressions that fit the noise, and minimising complexity alone produces a constant.'}
        </p>
        <Equation
          tex="\min_{f \in \mathcal{G}} \; \Big( \underbrace{\tfrac{1}{n}\sum_{i=1}^{n} \big(y_i - f(\mathbf{x}_i)\big)^2}_{\text{error}} , \; \underbrace{C(f)}_{\text{complexity}} \Big)"
          caption={
            es
              ? 'El problema como optimizacion multiobjetivo sobre la gramatica G. La solucion no es un punto sino un frente: el conjunto de expresiones que no son dominadas en ambos objetivos a la vez.'
              : 'The problem as a multi-objective optimisation over the grammar G. The solution is not a point but a front: the set of expressions not dominated on both objectives at once.'
          }
        />
        <ul>
          <li>
            <InlineMath tex="\mathcal{G}" />{' '}
            {es
              ? 'la gramatica: el conjunto de primitivas permitidas y las variables de entrada. Dos motores con conjuntos de primitivas distintos NO estaban resolviendo el mismo problema, y por eso cada ejecucion aqui registra el suyo.'
              : 'the grammar: the permitted primitives and the input variables. Two engines given different primitive sets were NOT solving the same problem, which is why every run here records its own.'}
          </li>
          <li>
            <InlineMath tex="C(f)" />{' '}
            {es
              ? 'la complejidad. Aqui se reportan tres medidas: conteo de nodos, un conteo ponderado por legibilidad y la longitud de descripcion en nats. La eleccion cambia que expresion queda en el codo del frente, asi que las tres viajan en el artefacto.'
              : 'the complexity. Three measures are reported here: node count, a readability-weighted count, and description length in nats. The choice changes which expression sits at the elbow of the front, so all three travel in the artifact.'}
          </li>
          <li>
            <InlineMath tex="n" />{' '}
            {es ? 'el numero de filas de entrenamiento, disjuntas de las de prueba y de las de extrapolacion.' : 'the number of training rows, disjoint from the test and extrapolation rows.'}
          </li>
        </ul>
        <Refs ids={['koza1992', 'schmidt2009']} label={es ? 'Referencias' : 'References'} />
      </section>

      <section>
        <h2>{es ? 'Por que es dificil' : 'Why it is hard'}</h2>
        <p>
          {es
            ? 'El espacio de busqueda es discreto y crece de forma catastrofica. El numero de arboles binarios distintos con n nodos internos es el numero de Catalan, y multiplicado por las elecciones de operador y de terminal en cada posicion crece muy rapido: con los cuatro operadores aritmeticos y cuatro variables de entrada, un arbol de veintiun nodos ya admite del orden de 10^18 formas distintas. La cota depende del conjunto de primitivas y del numero de variables, asi que ambos se declaran aqui en lugar de dejarlos implicitos. Ningun metodo enumera eso; todos hacen un compromiso.'
            : 'The search space is discrete and grows catastrophically. The number of distinct binary trees with n internal nodes is the Catalan number, and multiplied by the operator and terminal choices at each position it grows very fast: with the four arithmetic operators and four input variables, a twenty-one node tree already admits of the order of 10^18 distinct forms. The bound depends on the primitive set and on the number of variables, so both are stated here rather than left implicit. No method enumerates that; every method makes a compromise.'}
        </p>
        <Equation
          tex="|\mathcal{G}_n| \;\sim\; C_n \cdot |\mathcal{O}|^{n} \cdot (|\mathcal{V}|+1)^{n+1}, \qquad C_n = \frac{1}{n+1}\binom{2n}{n}"
          caption={
            es
              ? 'Una cota de conteo: los arboles de Catalan multiplicados por las elecciones de operador en los nodos internos y de terminal en las hojas.'
              : 'A counting bound: Catalan tree shapes multiplied by the operator choices at the internal nodes and the terminal choices at the leaves.'
          }
        />
        <p>
          {es
            ? 'El problema tambien es NP-dificil, aunque conviene decirlo con cuidado. La reduccion publicada parte de Unbounded Subset Sum usando un unico punto de datos, primitivas solo de suma y ajuste exacto. Es dureza real, pero no es un resultado de inaproximabilidad y no explica los modos de fallo que se observan en la practica.'
            : 'The problem is also NP-hard, though that deserves care. The published reduction is from Unbounded Subset Sum using a single data point, addition-only primitives and exact fit. That is genuine hardness, but it is not an inapproximability result and it does not explain the failure modes seen in practice.'}
        </p>
        <Refs ids={['virgolin2022', 'defranca2024']} label={es ? 'Referencias' : 'References'} />
      </section>

      <section>
        <h2>{es ? 'Lo que la evidencia dice hoy' : 'What the evidence says today'}</h2>
        <p>
          {es
            ? 'La evaluacion mas amplia disponible comparo doce metodos modernos y concluyo que NO existe un algoritmo dominante que devuelva el mejor modelo en todos los criterios. La recuperacion exacta solo ocurrio en los niveles de dificultad mas faciles. La tarea de extrapolacion resulto, en sus palabras, muy dificil, y la exactitud obtenida por la mayoria de los modelos fue deficiente, a menudo con R2 negativo. Y ningun algoritmo recupero la expresion correcta con ausencia completa de caracteristicas irrelevantes.'
            : 'The broadest available evaluation compared twelve modern methods and concluded there is NO dominating algorithm returning the best model on every criterion. Exact recovery happened only at the easiest difficulty levels. The extrapolation task proved, in its words, very challenging, and the accuracy most models obtained was subpar, often with a negative R-squared. And no algorithm recovered the correct expression with a complete absence of irrelevant features.'}{' '}
          <Cite id="defranca2024" paren />
        </p>
        <Callout variant="honest" title={es ? 'El numero que fundamenta este laboratorio' : 'The number this lab is built on'}>
          <p>
            {es
              ? 'En el nivel FACIL del conjunto SRSD-Feynman, el transformador preentrenado de extremo a extremo alcanzo 26,7 por ciento de problemas con R2 por encima de 0,999, con una tasa de solucion de 0,00 por ciento y una distancia de edicion normalizada de 1,00. Los tres numeros salen de la misma columna de la misma tabla. Es decir: ajuste practicamente perfecto, estructura completamente equivocada, en los problemas mas faciles del conjunto.'
              : 'On the EASY tier of the SRSD-Feynman set, the end-to-end pretrained transformer reached 26.7 percent of problems at R-squared above 0.999, with a 0.00 percent solution rate and a normalised edit distance of 1.00. All three numbers come from the same column of the same table. That is: a practically perfect fit, the completely wrong structure, on the easiest problems in the set.'}{' '}
            <Cite id="matsubara2022" paren />
          </p>
          <p>
            {es
              ? 'Por eso este laboratorio reporta la tasa de exactitud y la tasa de recuperacion como dos numeros separados, en cada caso, y nunca los promedia en uno solo. La brecha entre ambos ES el hallazgo.'
              : 'That is why this lab reports the accuracy rate and the recovery rate as two separate numbers, on every case, and never averages them into one. The gap between them IS the finding.'}
          </p>
        </Callout>
        <Refs ids={['matsubara2022', 'lacava2021', 'shojaee2025']} label={es ? 'Referencias' : 'References'} />
      </section>

      <section>
        <h2>{es ? 'El enfoque de este laboratorio' : 'The approach this lab takes'}</h2>
        <ol>
          <li>
            {es
              ? 'Correr toda la escalera sobre los MISMOS casos con el MISMO protocolo, en lugar de comparar numeros publicados que se midieron con presupuestos y conjuntos de primitivas distintos.'
              : 'Run the whole ladder on the SAME cases with the SAME protocol, instead of comparing published numbers measured under different budgets and primitive sets.'}
          </li>
          <li>
            {es
              ? 'Restringir la generacion, no solo filtrar despues. La aritmetica de intervalos rechaza candidatos indefinidos antes de evaluarlos, y el analisis dimensional impide construir expresiones que suman una masa a un tiempo.'
              : 'Constrain generation, not only filter afterwards. Interval arithmetic rejects undefined candidates before evaluating them, and dimensional analysis stops an expression that adds a mass to a time from ever being built.'}
          </li>
          <li>
            {es
              ? 'Probar la extrapolacion como una particion de primera clase, no como una nota al pie, porque ahi es donde la literatura dice que todos los metodos se degradan.'
              : 'Test extrapolation as a first-class split rather than a footnote, because that is where the literature says every method degrades.'}
          </li>
          <li>
            {es
              ? 'Medir la estructura con tres pruebas independientes y publicar sus desacuerdos, incluida la tasa de fallo de la propia herramienta de medicion.'
              : 'Measure structure with three independent tests and publish their disagreements, including the failure rate of the measurement tool itself.'}
          </li>
        </ol>
        <Refs ids={['keijzer2003', 'tenachi2023', 'buckingham1914']} label={es ? 'Referencias' : 'References'} />
      </section>

      <section>
        <h2>{es ? 'Lo que este laboratorio NO es' : 'What this lab is NOT'}</h2>
        <ul>
          <li>
            {es
              ? 'No es una afirmacion de que la regresion simbolica descubra leyes naturales a partir de datos. La evidencia de arriba es el argumento en contra de ese encuadre, y se cita dentro del producto.'
              : 'It is not a claim that symbolic regression discovers natural laws from data. The evidence above is the argument against that framing, and it is cited inside the product.'}
          </li>
          <li>
            {es
              ? 'No es una tabla de clasificacion. Reporta frentes y clases de equivalencia, con el protocolo impreso junto a cada numero.'
              : 'It is not a leaderboard. It reports fronts and equivalence classes, with the protocol printed next to every number.'}
          </li>
          <li>
            {es
              ? 'No es una herramienta de AutoML. Donde el aumento de gradiente simplemente gana, la documentacion lo dice y lo muestra.'
              : 'It is not an AutoML tool. Where gradient boosting simply wins, the documentation says so and shows it.'}
          </li>
          <li>
            {es
              ? 'No es descubrimiento causal. Una forma que ajusta no es un mecanismo, y esa trampa tiene su propia seccion en la metodologia.'
              : 'It is not causal discovery. A form that fits is not a mechanism, and that trap has its own section in the methodology.'}
          </li>
          <li>
            {es
              ? 'No afirma programacion genetica acelerada por GPU. La busqueda de arboles es un trabajo ramificado y ligado a la CPU, y la unica opcion nativa en GPU verificada tiene una licencia incompatible con este producto.'
              : 'It does not claim GPU-accelerated genetic programming. Tree search is a branchy, CPU-bound workload, and the only verified GPU-native option carries a licence incompatible with this product.'}
          </li>
        </ul>
        <Refs ids={['cranmer2020', 'udrescu2020']} label={es ? 'Referencias' : 'References'} />
      </section>
    </div>
  );
}
