/**
 * The in-app Architecture modal: the proof, inside the app, that this is a real system.
 *
 * Each tab pairs one hand-authored theme-aware SVG with a bilingual explanation. The SVGs are
 * fetched and INLINED by the shell rather than referenced as images, because an image cannot
 * inherit the page CSS custom properties and would therefore be unreadable in one of the two themes.
 */
import type { ArchitectureConfig } from '@fasl-work/caos-app-shell';

export const ARCHITECTURE: ArchitectureConfig = {
  title_en: 'Architecture and how it works',
  title_es: 'Arquitectura y como funciona',
  tabs: [
    {
      id: 'what-it-is',
      en: 'What it is',
      es: 'Que es',
      svg: 'svg/tech/01-the-app.svg',
      body_en: `SymLab is a public research lab on symbolic regression: recovering an explicit closed-form expression from data, rather than fitting a function whose internals nobody can read.

The deliverable is not one equation. It is a Pareto front of candidate laws, each shown three ways: as readable mathematics, as the operator tree behind that mathematics, and as the search that produced it. Showing only the first is what most tooling does, and it hides both the structure and the evidence.

The claim this lab defends is deliberately narrower than the one the field is often sold on. It is not that symbolic regression discovers natural laws. It is that symbolic regression produces a Pareto front of constrained, dimensionally consistent, extrapolation-tested closed-form models, and that the honest output is the equivalence class rather than a winner.

That narrowing is forced by evidence. The benchmark literature reports a method scoring above 0.999 on the coefficient of determination while recovering the correct structure zero percent of the time. So this lab reports accuracy and recovery as two separate numbers, and treats the gap between them as its headline measurement.`,
      body_es: `SymLab es un laboratorio publico de investigacion sobre regresion simbolica: recuperar una expresion explicita en forma cerrada a partir de datos, en lugar de ajustar una funcion cuyo interior nadie puede leer.

El entregable no es una ecuacion. Es un frente de Pareto de leyes candidatas, cada una mostrada de tres formas: como matematica legible, como el arbol de operadores detras de esa matematica, y como la busqueda que la produjo. Mostrar solo lo primero es lo que hace la mayoria de las herramientas, y oculta tanto la estructura como la evidencia.

La afirmacion que este laboratorio defiende es deliberadamente mas estrecha que la que suele venderse. No es que la regresion simbolica descubra leyes naturales. Es que produce un frente de Pareto de modelos en forma cerrada, restringidos, dimensionalmente consistentes y probados en extrapolacion, y que la salida honesta es la clase de equivalencia, no un ganador.

Ese estrechamiento lo fuerza la evidencia. La literatura de benchmarks reporta un metodo que supera 0,999 en el coeficiente de determinacion mientras recupera la estructura correcta el cero por ciento de las veces. Por eso aqui la exactitud y la recuperacion se reportan como dos numeros separados, y la brecha entre ellos es la medicion principal.`,
    },
    {
      id: 'lanes',
      en: 'The lanes',
      es: 'Los carriles',
      svg: 'svg/tech/02-lanes.svg',
      body_en: `Three lanes, one engine.

OFFLINE is where the real work happens. Datasets are fetched into a vault outside the repository, pinned by SHA-256, and carried with a provenance sidecar recording the licence and the redistribution verdict, which are different questions. The staged pipeline then runs: ingestion contract, feature extraction, the search ladder, inference on held-out and extrapolation data, scoring, and export.

COMMITTED is the boundary. A run is a pure function of the case, the configuration, the seed and the data. Regenerating a case reproduces every scientific number exactly: the same expressions, the same losses, the same verdicts. The measured wall clock IS recorded and does move between runs, deliberately, because what a rung costs is part of its evaluation and comparing methods at equal generation count rather than equal budget is a fairness problem this lab argues about. So a re-bake shows a timing diff and never a result diff.

WEB has two modes. Replay is always the first paint and is a pure rendering of the committed artifact: nothing that Python could compute is recomputed in the browser. The live lane runs the SAME package modules under Pyodide at a reduced budget, and only when the reader asks for it.

That last point is a design constraint, not a preference. There is no maintained JavaScript, TypeScript or WebAssembly symbolic-regression library, so the alternative to Pyodide was forking the engine into TypeScript and then keeping two implementations in agreement forever. An offline-versus-live disagreement is exactly the defect that produces published numbers nobody can reproduce.`,
      body_es: `Tres carriles, un solo motor.

OFFLINE es donde ocurre el trabajo real. Los conjuntos de datos se descargan a una boveda fuera del repositorio, se fijan por SHA-256 y se acompanan de un archivo de procedencia que registra la licencia y el veredicto de redistribucion, que son preguntas distintas. Luego corre la tuberia por etapas: contrato de ingesta, extraccion de caracteristicas, la escalera de busqueda, inferencia sobre datos retenidos y de extrapolacion, evaluacion y exportacion.

COMMITTED es la frontera. Una ejecucion es una funcion pura del caso, la configuracion, la semilla y los datos. Regenerar un caso reproduce exactamente cada numero cientifico: las mismas expresiones, las mismas perdidas, los mismos veredictos. El tiempo medido SI se registra y si cambia entre corridas, a proposito, porque lo que cuesta un escalon forma parte de su evaluacion y comparar metodos a igual numero de generaciones en vez de a igual presupuesto es un problema de justicia que este laboratorio discute. Asi que volver a hornear muestra una diferencia de tiempos y nunca una diferencia de resultados.

WEB tiene dos modos. La reproduccion es siempre el primer render y es una representacion pura del artefacto versionado: nada que Python pudiera calcular se recalcula en el navegador. El carril en vivo ejecuta LOS MISMOS modulos del paquete bajo Pyodide con presupuesto reducido, y solo cuando el lector lo pide.

Ese ultimo punto es una restriccion de diseno, no una preferencia. No existe ninguna biblioteca mantenida de regresion simbolica en JavaScript, TypeScript o WebAssembly, asi que la alternativa a Pyodide era bifurcar el motor a TypeScript y mantener dos implementaciones de acuerdo para siempre. Una discrepancia entre lo offline y lo vivo es exactamente el defecto que produce numeros publicados que nadie puede reproducir.`,
    },
    {
      id: 'web-flow',
      en: 'The web flow',
      es: 'El flujo web',
      svg: 'svg/tech/03-web-flow.svg',
      body_en: `The app loads a case index, gates it on the schema version, and then loads one case payload. A payload whose major schema version this build does not know is refused with a visible message, never rendered as an empty panel: a schema mismatch that shows a blank chart is indistinguishable from a genuine empty result, and that ambiguity is expensive to diagnose.

The method list in the sidebar is the ablation. Each entry is a search configuration, and most of them add exactly ONE mechanism to the entry above, so moving down the list attributes a measured difference to that named change. Three do not, and saying so is the point of an ablation: r2 turns on linear scaling AND the interval guard together, because Keijzer's contribution is both; r6 adds age-fitness and islands while turning multi-objective survival OFF; r7 turns it back on alongside both deduplication switches. Read those three as compound steps. A case whose inputs carry no declared physical dimensions omits the unit-typed entry, rather than offering a configuration that silently does nothing.

Six sub-tabs follow. Expression compares the discovered formula against the relationship expected, with the equivalence verdict between them. Structure is the operator tree and the additive components. Parity and residuals carries the validation views, including extrapolation. Live runs the engine in your browser, on the cases that have a browser-side generator. Front and search shows the Pareto front, where clicking a point loads that expression into every other view, together with the convergence and diversity histories and the measured cost of the rung. Context is the deep write-up.

One detail makes the cross-highlighting work: the node identifiers travel inside the rendered mathematics. The pipeline emits them into the markup, so hovering a term in the equation highlights the same subtree in the tree with no second, parallel mapping to keep synchronised.`,
      body_es: `La aplicacion carga un indice de casos, lo valida contra la version del esquema y luego carga la carga util de un caso. Una carga util cuya version mayor de esquema esta build no conoce se rechaza con un mensaje visible, nunca se dibuja como un panel vacio: un desajuste de esquema que muestra un grafico en blanco es indistinguible de un resultado genuinamente vacio, y esa ambiguedad es cara de diagnosticar.

La lista de metodos de la barra lateral es la ablacion. Cada entrada es una configuracion de busqueda, y la mayoria anade exactamente UN mecanismo a la entrada anterior, de modo que recorrer la lista atribuye una diferencia medida a ese cambio con nombre. Tres no lo hacen, y decirlo es justamente el sentido de una ablacion: r2 activa a la vez el escalado lineal Y la guarda de intervalos, porque la contribucion de Keijzer son ambas; r6 anade edad-aptitud e islas mientras APAGA la supervivencia multiobjetivo; r7 la vuelve a encender junto con los dos interruptores de deduplicacion. Lee esos tres como pasos compuestos. Un caso cuyas entradas no declaran dimensiones fisicas omite la entrada de unidades, en lugar de ofrecer una configuracion que en silencio no hace nada.

Siguen seis sub-pestanas. Expresion compara la formula descubierta con la relacion esperada, con el veredicto de equivalencia entre ambas. Estructura es el arbol de operadores y los componentes aditivos. Paridad y residuos lleva las vistas de validacion, incluida la extrapolacion. En vivo ejecuta el motor en tu navegador, en los casos que tienen un generador ejecutable en el navegador. Frente y busqueda muestra el frente de Pareto, donde hacer clic en un punto lo carga en todas las demas vistas, junto con las historias de convergencia y diversidad y el costo medido del escalon. Contexto es el desarrollo profundo.

Un detalle hace posible el resaltado cruzado: los identificadores de nodo viajan dentro de la matematica renderizada. La tuberia los emite en el marcado, de modo que pasar el cursor por un termino resalta el mismo subarbol en el arbol sin un segundo mapeo paralelo que mantener sincronizado.`,
    },
    {
      id: 'science',
      en: 'The science',
      es: 'La ciencia',
      svg: 'svg/tech/04-the-science.svg',
      body_en: `A candidate expression is proposed, guarded, fitted and then judged.

Proposal uses the classical operator set, including hoist mutation, which is the only operator that reliably makes an expression smaller and therefore the classical counter-pressure against unbounded growth.

The guard is where this departs from a tutorial implementation. Interval arithmetic propagates the input ranges through the candidate and REJECTS anything undefined anywhere in the box, before a single evaluation. There are no protected operators here. Protected division, which returns an arbitrary value when the denominator is zero, silently changes the function being searched and produces expressions that are only meaningful on the sample they were fitted to.

Fitting solves what does not need to be evolved. The outer multiplicative and additive constants have a closed form, and the remaining numeric leaves are fitted by Levenberg-Marquardt and written back into the tree, so the improvement is inherited rather than rediscovered each generation. A rank-deficient Jacobian is detected and reported as constants that are not identifiable, rather than returning arbitrary fitted values.

Selection off the front is by minimum description length, never by best accuracy. Then three independent equivalence tests run, and their disagreements are reported rather than resolved, because any single test is unreliable in a way the other two are not.`,
      body_es: `Una expresion candidata se propone, se protege, se ajusta y luego se juzga.

La propuesta usa el conjunto clasico de operadores, incluida la mutacion de izado, que es el unico operador que reduce de forma fiable el tamano de una expresion y por tanto la contrapresion clasica frente al crecimiento sin limite.

La proteccion es donde esto se separa de una implementacion de tutorial. La aritmetica de intervalos propaga los rangos de entrada por el candidato y RECHAZA cualquier cosa indefinida en algun punto de la caja, antes de una sola evaluacion. Aqui no hay operadores protegidos. La division protegida, que devuelve un valor arbitrario cuando el denominador es cero, cambia en silencio la funcion que se esta buscando y produce expresiones que solo tienen sentido en la muestra con la que se ajustaron.

El ajuste resuelve lo que no hace falta evolucionar. Las constantes multiplicativa y aditiva externas tienen forma cerrada, y las hojas numericas restantes se ajustan por Levenberg-Marquardt y se reescriben en el arbol, de modo que la mejora se hereda en lugar de redescubrirse cada generacion. Un jacobiano de rango deficiente se detecta y se reporta como constantes no identificables, en vez de devolver valores ajustados arbitrarios.

La seleccion sobre el frente es por longitud de descripcion minima, nunca por mejor exactitud. Luego corren tres pruebas de equivalencia independientes, y sus desacuerdos se reportan en lugar de resolverse, porque cualquier prueba aislada es poco fiable de un modo en que las otras dos no lo son.`,
    },
    {
      id: 'contracts',
      en: 'The two contracts',
      es: 'Los dos contratos',
      svg: 'svg/tech/05-data-contracts.svg',
      body_en: `Two contracts bound the pipeline, one at each end.

The ingestion contract declares the required schema, units and ranges, plus an explicit outlier and missing-value policy. Bad data is rejected rather than silently coerced. It also carries a generic detector for the target-broadcast defect: when a target takes far fewer distinct values than there are rows, fitting at that resolution leaks the target, and the detector catches the NEXT dataset with that defect rather than only the one already known to have it.

Real defects found during this build are carried verbatim rather than fixed quietly. One source states it has no missing values and ships 591. One recorded download URL served a completely different dataset with a successful status code, so the loader now asserts the expected schema before accepting the file. Another widely cited host returns a 404 and had to be replaced with a permissively licensed carrier.

The artifact contract is frozen at schema version 1.0.0 and was written before any user interface existed. A TypeScript type mirrors it, so a drift between what the exporter writes and what the app expects fails the build rather than producing a blank panel at runtime.

Three rules inside it are load-bearing: every float is rounded before it ships, node identifiers are one shared integer space across the equation, the tree and the terms, and every colour index is assigned in Python so three consumers cannot drift apart. And every downsample discloses its original count, because showing part of the data is fine and not saying so is not.`,
      body_es: `Dos contratos acotan la tuberia, uno en cada extremo.

El contrato de ingesta declara el esquema requerido, las unidades y los rangos, mas una politica explicita de valores atipicos y faltantes. Los datos malos se rechazan en lugar de coercionarse en silencio. Ademas lleva un detector generico del defecto de difusion del objetivo: cuando un objetivo toma muchos menos valores distintos que filas hay, ajustar a esa resolucion filtra el objetivo, y el detector atrapa al PROXIMO conjunto con ese defecto y no solo al que ya se sabe que lo tiene.

Los defectos reales encontrados durante esta construccion se registran textualmente en lugar de corregirse en silencio. Una fuente declara que no tiene valores faltantes y entrega 591. Una URL de descarga registrada servia un conjunto de datos completamente distinto con codigo de exito, asi que el cargador ahora verifica el esquema esperado antes de aceptar el archivo. Otro host muy citado devuelve 404 y hubo que reemplazarlo por un portador con licencia permisiva.

El contrato de artefacto esta congelado en la version de esquema 1.0.0 y se escribio antes de que existiera ninguna interfaz. Un tipo de TypeScript lo refleja, de modo que una divergencia entre lo que escribe el exportador y lo que espera la aplicacion rompe la compilacion en vez de producir un panel en blanco en tiempo de ejecucion.

Tres reglas internas son portantes: cada numero flotante se redondea antes de enviarse, los identificadores de nodo son un unico espacio de enteros compartido por la ecuacion, el arbol y los terminos, y cada indice de color se asigna en Python para que tres consumidores no puedan divergir. Y todo submuestreo declara su conteo original, porque mostrar parte de los datos esta bien y no decirlo no lo esta.`,
    },
  ],
};
