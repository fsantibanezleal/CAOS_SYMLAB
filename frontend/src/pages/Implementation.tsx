import { Callout, Equation, Refs, SubTabs } from '@fasl-work/caos-app-shell';

import { useLang } from '../lib/useLang';

/**
 * Implementation: the real pipeline, the real constraints, and the defects found while building it.
 *
 * The defect section is the most useful part of this page. Four of the sources the research phase
 * recorded as good turned out to be wrong in ways that return a successful status code, and a reader
 * deciding whether to trust these numbers deserves to know how they were caught.
 */
export default function Implementation() {
  const es = useLang() === 'es';

  const tabs = [
    {
      id: 'pipeline',
      label: es ? 'La tuberia' : 'The pipeline',
      content: (
        <section>
          <h3>{es ? 'Seis etapas con contratos explicitos entre ellas' : 'Six stages with explicit contracts between them'}</h3>
          <ol>
            <li>
              <strong>preprocess</strong>{' '}
              {es
                ? 'carga el caso, aplica el contrato de ingesta y construye TRES particiones: entrenamiento, prueba interior y extrapolacion. La de extrapolacion se toma de las colas de la entrada con mayor rango, de modo que la region de entrenamiento es una caja interior y las filas retenidas quedan realmente fuera del soporte que la busqueda vio.'
                : 'loads the case, applies the ingestion contract, and builds THREE splits: train, interior test, and extrapolation. The extrapolation split is taken from the tails of the widest-ranging input, so the training region is an interior box and the held-out rows genuinely lie outside the support the search ever saw.'}
            </li>
            <li>
              <strong>feature_extraction</strong>{' '}
              {es
                ? 'deriva la caja de intervalos ensanchada, las declaraciones de unidades y un resumen de muestreo que la aplicacion imprime junto al resultado.'
                : 'derives the widened interval box, the unit declarations, and a sampling summary the app prints next to the result.'}
            </li>
            <li>
              <strong>train</strong>{' '}
              {es
                ? 'ejecuta las variantes, registrando el tiempo medido de cada una porque el costo forma parte de su evaluacion.'
                : 'runs the variants, recording each one measured wall-clock because the cost is part of its evaluation.'}
            </li>
            <li>
              <strong>infer</strong>{' '}
              {es
                ? 'puntua cada miembro del frente en las tres regiones por separado, contando las predicciones no finitas en lugar de descartarlas.'
                : 'scores every front member on all three regions separately, counting non-finite predictions rather than dropping them.'}
            </li>
            <li>
              <strong>evaluate</strong>{' '}
              {es
                ? 'aplica la prueba triple de equivalencia y selecciona por longitud de descripcion.'
                : 'applies the triple-equivalence test and selects by description length.'}
            </li>
            <li>
              <strong>export</strong>{' '}
              {es
                ? 'escribe el artefacto de esquema 1.0.0 y, por separado, el manifiesto de auditoria.'
                : 'writes the schema 1.0.0 artifact and, separately, the audit manifest.'}
            </li>
          </ol>
          <Callout variant="note" title={es ? 'Determinismo como requisito, no como detalle' : 'Determinism as a requirement, not a detail'}>
            <p>
              {es
                ? 'Una ejecucion es una funcion pura del caso, la configuracion, la semilla y los datos. Nada escribe el reloj dentro de un artefacto, de modo que regenerar un caso produce una salida identica byte a byte y volver a hornear nunca ensucia el repositorio sin un cambio real detras.'
                : 'A run is a pure function of the case, the configuration, the seed and the data. Nothing writes the clock into an artifact, so regenerating a case produces byte-identical output and a re-bake never dirties the repository without a real change behind it.'}
            </p>
          </Callout>
        </section>
      ),
    },
    {
      id: 'defects',
      label: es ? 'Defectos encontrados' : 'Defects found',
      content: (
        <section>
          <h3>{es ? 'Cuatro fuentes que devolvian codigo de exito y estaban mal' : 'Four sources that returned a success code and were wrong'}</h3>
          <p>
            {es
              ? 'Estos se encontraron verificando el CONTENIDO, no el codigo de estado. Cada uno habria corrompido en silencio numeros publicados.'
              : 'These were found by verifying CONTENT, not the status code. Each one would have silently corrupted published numbers.'}
          </p>
          <div className="sym-table-scroll">
            <table className="sym-table">
              <thead>
                <tr>
                  <th>{es ? 'Defecto' : 'Defect'}</th>
                  <th>{es ? 'Como se presentaba' : 'How it presented'}</th>
                  <th>{es ? 'La realidad' : 'The reality'}</th>
                </tr>
              </thead>
              <tbody>
                <tr>
                  <td>{es ? 'URL de flotacion registrada' : 'Recorded flotation URL'}</td>
                  <td>{es ? 'codigo 200, tamano plausible' : 'status 200, plausible size'}</td>
                  <td>{es ? 'un conjunto de datos completamente distinto' : 'an entirely different dataset'}</td>
                </tr>
                <tr>
                  <td>{es ? 'Los 33 archivos de referencia fisica' : 'All 33 physics benchmark files'}</td>
                  <td>{es ? 'codigo 200, descarga correcta' : 'status 200, downloaded fine'}</td>
                  <td>{es ? 'punteros de almacenamiento, 132 bytes cada uno' : 'storage pointers, 132 bytes each'}</td>
                </tr>
                <tr>
                  <td>{es ? 'Host canonico de las mediciones de friccion' : 'Canonical host for the friction measurements'}</td>
                  <td>{es ? 'citado en la literatura' : 'cited in the literature'}</td>
                  <td>{es ? 'devuelve 404; segunda URL muerta del campo' : 'returns 404; the second dead URL in this field'}</td>
                </tr>
                <tr>
                  <td>{es ? 'Pagina de un conjunto de aguas residuales' : 'A wastewater dataset landing page'}</td>
                  <td>{es ? 'declara que no hay valores faltantes' : 'states there are no missing values'}</td>
                  <td>{es ? 'el archivo contiene 591' : 'the file contains 591'}</td>
                </tr>
              </tbody>
            </table>
          </div>
          <Callout variant="honest" title={es ? 'Lo que cambio como resultado' : 'What changed as a result'}>
            <p>
              {es
                ? 'El cargador ahora VERIFICA el esquema esperado antes de aceptar un archivo, el descargador rechaza la firma de un puntero de almacenamiento, cada fuente se fija por SHA-256 con un archivo de procedencia, y los defectos documentados se llevan textualmente al manifiesto en lugar de corregirse en silencio. Ocultar una trampa es peor que la trampa.'
                : 'The loader now ASSERTS the expected schema before accepting a file, the fetcher rejects the storage-pointer signature outright, every source is pinned by SHA-256 with a provenance sidecar, and documented defects are carried verbatim into the manifest rather than quietly fixed. Hiding a trap is worse than the trap.'}
            </p>
          </Callout>
        </section>
      ),
    },
    {
      id: 'leakage',
      label: es ? 'Fuga y su deteccion' : 'Leakage and its detection',
      content: (
        <section>
          <h3>{es ? 'La trampa de la difusion del objetivo' : 'The target-broadcast trap'}</h3>
          <p>
            {es
              ? 'El conjunto de flotacion registra variables de proceso cada veinte segundos, pero los ensayos de concentrado son mediciones de laboratorio HORARIAS repetidas en cada fila, unas 13,5 veces por valor distinto. Ajustar a nivel de fila filtra el objetivo esa misma cantidad de veces.'
              : 'The flotation dataset records process variables every twenty seconds, but the concentrate assays are HOURLY laboratory measurements repeated across every row, about 13.5 times per distinct value. Fitting at row level leaks the target that many times over.'}
          </p>
          <p>
            {es
              ? 'El cargador agrega a la rejilla horaria y NO ofrece acceso a nivel de fila en absoluto, de modo que la fuga queda estructuralmente indisponible en lugar de meramente desaconsejada. Ademas excluye ambos ensayos de concentrado de las entradas: predecir la silice desde el hierro es leer la respuesta en la otra mitad de la misma medicion de laboratorio, no un sensor virtual.'
              : 'The loader aggregates to the hourly grid and offers NO row-level access at all, so the leak is structurally unavailable rather than merely discouraged. It also excludes both concentrate assays from the inputs: predicting silica from iron is reading the answer off the other half of the same laboratory measurement, not soft sensing.'}
          </p>
          <Equation
            tex="\text{repeat ratio} = \frac{n_{\text{rows}}}{|\{\,\text{distinct } y\,\}|} \;>\; 3 \;\Longrightarrow\; \text{warn}"
            caption={
              es
                ? 'El detector generico. Se dispara cuando el objetivo toma muchos menos valores distintos que filas hay, de modo que atrapa al PROXIMO conjunto con este defecto y no solo al que ya se sabe que lo tiene.'
                : 'The generic detector. It fires when the target takes far fewer distinct values than there are rows, so it catches the NEXT dataset with this defect and not only the one already known to have it.'
            }
          />
          <p>
            {es
              ? 'Verificacion independiente durante esta construccion, sobre el archivo crudo: la recta de planta es Fe = 67,08 - 0,736 Si con correlacion -0,9718, frente a la prediccion estequiometrica de dos minerales 69,94 - 0,699 Si. Se reportan ambas rectas; la diferencia entre ellas dice algo sobre los demas minerales presentes.'
              : 'Independently verified during this build, from the raw file: the plant line is Fe = 67.08 - 0.736 Si with correlation -0.9718, against the two-mineral stoichiometric prediction 69.94 - 0.699 Si. Both lines are reported; the difference between them says something about the other minerals present.'}
          </p>
        </section>
      ),
    },
    {
      id: 'lanes',
      label: es ? 'Los carriles y sus limites' : 'The lanes and their limits',
      content: (
        <section>
          <h3>{es ? 'Por que el carril en vivo es Pyodide y no TypeScript' : 'Why the live lane is Pyodide and not TypeScript'}</h3>
          <p>
            {es
              ? 'Durante la investigacion se verifico contra el registro de paquetes que NO existe ninguna biblioteca mantenida de regresion simbolica en JavaScript, TypeScript o WebAssembly. La unica coincidencia de nombre es un paquete mal publicado cuya propia descripcion dice que es una clase de Python.'
              : 'During the research phase it was verified against the package registry that there is NO maintained JavaScript, TypeScript or WebAssembly symbolic-regression library. The only name match is a mispublished package whose own description says it is a Python class.'}
          </p>
          <p>
            {es
              ? 'Quedaban dos opciones: ejecutar el nucleo de Python bajo Pyodide, o bifurcar el nucleo a TypeScript. La bifurcacion se rechazo porque crearia dos motores que hay que mantener de acuerdo para siempre, y una discrepancia entre lo offline y lo vivo es exactamente el defecto que produce numeros publicados irreproducibles. El navegador ejecuta los MISMOS modulos del paquete, con presupuesto reducido.'
              : 'That left two options: run the Python core under Pyodide, or fork the core into TypeScript. The fork was rejected because it would create two engines that must be kept in agreement forever, and an offline-versus-live disagreement is exactly the defect that produces irreproducible published numbers. The browser runs the SAME package modules, at a reduced budget.'}
          </p>
          <Callout variant="honest" title={es ? 'Sin GPU para la busqueda, y se dice' : 'No GPU for the search, and it says so'}>
            <p>
              {es
                ? 'La programacion genetica de arboles es un trabajo ramificado, irregular y ligado a la CPU. Los dos motores de referencia mas usados no tienen ruta de busqueda en GPU, y la unica opcion nativa en GPU verificada tiene una licencia copyleft incompatible con este producto. Afirmar aceleracion por GPU aqui seria falso, asi que no se afirma.'
                : 'Tree genetic programming is a branchy, irregular, CPU-bound workload. The two most-used reference engines have no GPU search path, and the only verified GPU-native option carries a copyleft licence incompatible with this product. Claiming GPU acceleration here would be false, so it is not claimed.'}
            </p>
          </Callout>
          <Refs ids={['cranmer2023', 'petersen2021']} label={es ? 'Referencias' : 'References'} />
        </section>
      ),
    },
    {
      id: 'package',
      label: es ? 'El paquete extraido' : 'The extracted package',
      content: (
        <section>
          <h3>{es ? 'Por que el evaluador vive en su propio paquete' : 'Why the evaluator lives in its own package'}</h3>
          <p>
            {es
              ? 'El protocolo de equivalencia no es especifico de este laboratorio, asi que vive en un paquete separado con licencia MIT que este producto consume como dependencia. No queda ninguna copia dentro del producto: una segunda copia de una regla de puntuacion es un segundo lugar donde puede divergir, y todo el argumento de ese paquete es que el evaluador debe ser auditable.'
              : 'The equivalence protocol is not specific to this lab, so it lives in a separate MIT-licensed package that this product consumes as a dependency. No copy is left behind inside the product: a second copy of a scoring rule is a second place for it to drift, and the whole argument of that package is that the scorer must be auditable.'}
          </p>
          <Callout variant="note" title={es ? 'Y una razon de licencia' : 'And a licence reason'}>
            <p>
              {es
                ? 'La implementacion de referencia mas usada de este protocolo tiene licencia copyleft fuerte. El paquete extraido esta escrito desde la especificacion publicada, sin reproducir ninguna parte de aquel codigo, que es lo que permite que sea MIT y que este producto lo use.'
                : 'The most-used reference implementation of this protocol is strong-copyleft licensed. The extracted package is written from the published specification without reproducing any part of that code, which is what allows it to be MIT and to be used by this product.'}
            </p>
          </Callout>
        </section>
      ),
    },
  ];

  return (
    <div className="page-body prose">
      <div className="page-head">
        <h1>{es ? 'Implementacion' : 'Implementation'}</h1>
        <p className="lede">
          {es
            ? 'La tuberia real, las restricciones reales, y los defectos encontrados al construirla. Cuatro de las fuentes que la fase de investigacion habia registrado como buenas resultaron estar mal de formas que devuelven un codigo de exito, y quien decida si confiar en estos numeros merece saber como se atraparon.'
            : 'The real pipeline, the real constraints, and the defects found while building it. Four of the sources the research phase recorded as good turned out to be wrong in ways that return a success code, and anyone deciding whether to trust these numbers deserves to know how they were caught.'}
        </p>
      </div>
      <SubTabs tabs={tabs} ariaLabel={es ? 'Aspectos de la implementacion' : 'Implementation aspects'} />
    </div>
  );
}
