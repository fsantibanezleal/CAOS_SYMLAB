import { Callout, Cite, Equation, Refs, SubTabs } from '@fasl-work/caos-app-shell';

import { AblationResult } from '../render/AblationResult';
import { FigThreeSplits, FigTripleEquivalence } from '../render/Figures';
import { useEffect, useState } from 'react';

import { loadIndex, loadRun } from '../lib/data';
import type { CaseIndex, RunPayload } from '../lib/contract.types';
import { useLang } from '../lib/useLang';

/**
 * Experiments: the design, the protocol, and the coverage matrix computed from the real index.
 *
 * The coverage table is read from the shipped artifacts rather than typed into the page, so it
 * cannot drift away from what was actually baked. A hand-written coverage claim is the easiest kind
 * of number to leave stale.
 */
export default function Experiments() {
  const es = useLang() === 'es';
  const [index, setIndex] = useState<CaseIndex | null>(null);
  const [runs, setRuns] = useState<RunPayload[]>([]);

  useEffect(() => {
    loadIndex()
      .then((loaded) => {
        setIndex(loaded);
        // The ablation summary needs every run, not the index: the per-rung equivalence verdict
        // lives on the variant score, which the index does not carry.
        return Promise.all(loaded.cases.map((entry) => loadRun(entry.case_id).catch(() => null)));
      })
      .then((loaded) => setRuns(loaded.filter((r): r is RunPayload => r !== null)))
      .catch(() => setIndex(null));
  }, []);

  const tabs = [
    {
      id: 'design',
      label: es ? 'Diseno' : 'Design',
      content: (
        <section>
          <h3>{es ? 'Que pregunta responde cada experimento' : 'What question each experiment answers'}</h3>
          <p>
            {es
              ? 'Las variantes de un caso no son un recorrido de metodos. La mayoria anade exactamente UN mecanismo a la anterior, de modo que una diferencia medida se atribuye a ese cambio con nombre. Tres no lo hacen, y decirlo es justamente el sentido de una ablacion: r2 activa a la vez el escalado lineal Y la guarda de intervalos, porque la contribucion de Keijzer son ambas; r6 activa la supervivencia edad-aptitud Y las islas, que son un mecanismo con dos interruptores; r7 activa los dos interruptores de deduplicacion. Ningun escalon APAGA nunca un mecanismo: antes r6 quitaba la supervivencia multiobjetivo y r7 la reponia, lo que dejaba sin atribucion la diferencia medida en r6, y ahora una prueba falla si eso vuelve. Lee esos tres como pasos compuestos, marcados abajo, y los demas como incrementos limpios.'
              : 'The variants of a case are not a tour of methods. Most rungs add exactly ONE mechanism to the one above them, so a measured difference is attributable to that named change. Three do not, and saying so is the point of an ablation: r2 turns on linear scaling AND the interval guard together, because the Keijzer contribution is both; r6 turns on age-fitness survival AND islands, which are one mechanism behind two switches; r7 turns on both deduplication switches. No rung ever turns a mechanism OFF: r6 used to drop multi-objective survival and r7 to restore it, which made the difference measured at r6 unattributable, and a test now fails if that returns. Read those three as compound steps, marked below, and the rest as clean increments.'}
          </p>
          <div className="sym-table-scroll">
            <table className="sym-table">
              <thead>
                <tr>
                  <th>{es ? 'Escalon' : 'Rung'}</th>
                  <th>{es ? 'Mecanismo anadido' : 'Mechanism added'}</th>
                  <th>{es ? 'La pregunta que responde' : 'The question it answers'}</th>
                </tr>
              </thead>
              <tbody>
                <tr>
                  <td>1</td>
                  <td>{es ? 'ninguno, la base de 1992' : 'none, the 1992 baseline'}</td>
                  <td>{es ? 'la condicion de control que todo lo demas debe superar' : 'the control condition everything else must beat'}</td>
                </tr>
                <tr>
                  <td>2</td>
                  <td>
                    {es ? 'escalado lineal y guardas de intervalo' : 'linear scaling and interval guards'}{' '}
                    <em>{es ? '(compuesto: dos interruptores)' : '(compound: two switches)'}</em>
                  </td>
                  <td>{es ? 'cuanto del trabajo era resolver constantes en vez de buscar forma' : 'how much of the work was solving constants rather than searching for shape'}</td>
                </tr>
                <tr>
                  <td>3</td>
                  <td>{es ? 'ajuste no lineal de constantes' : 'nonlinear constant tuning'}</td>
                  <td>{es ? 'que queda por ganar tras el escalado en forma cerrada' : 'what remains to gain after closed-form scaling'}</td>
                </tr>
                <tr>
                  <td>4</td>
                  <td>{es ? 'supervivencia de Pareto' : 'Pareto survival'}</td>
                  <td>{es ? 'si tratar la complejidad como objetivo bate tratarla como penalizacion' : 'whether complexity as an objective beats complexity as a penalty'}</td>
                </tr>
                <tr>
                  <td>5</td>
                  <td>{es ? 'seleccion epsilon-lexicase' : 'epsilon-lexicase selection'}</td>
                  <td>{es ? 'si conservar especialistas compensa su costo medido' : 'whether preserving specialists is worth its measured cost'}</td>
                </tr>
                <tr>
                  <td>6</td>
                  <td>
                    {es
                      ? 'edad-aptitud e islas, con la supervivencia multiobjetivo APAGADA'
                      : 'age-fitness and islands, with multi-objective survival turned OFF'}{' '}
                    <em>{es ? '(compuesto: tres cambios)' : '(compound: three changes)'}</em>
                  </td>
                  <td>{es ? 'si la convergencia prematura estaba limitando el resultado' : 'whether premature convergence was limiting the result'}</td>
                </tr>
                <tr>
                  <td>7</td>
                  <td>
                    {es
                      ? 'deduplicacion estructural y semantica, con la supervivencia multiobjetivo encendida de nuevo'
                      : 'structural and semantic deduplication, with multi-objective survival turned back on'}{' '}
                    <em>{es ? '(compuesto: tres cambios)' : '(compound: three changes)'}</em>
                  </td>
                  <td>{es ? 'que fraccion del presupuesto se gastaba en repetir evaluaciones' : 'what fraction of the budget was spent repeating evaluations'}</td>
                </tr>
                <tr>
                  <td>8</td>
                  <td>{es ? 'generacion con unidades' : 'unit-typed generation'}</td>
                  <td>{es ? 'que aporta restringir la generacion frente a filtrar despues' : 'what constraining generation buys over filtering afterwards'}</td>
                </tr>
              </tbody>
            </table>
          </div>
          <Callout variant="honest" title={es ? 'El brazo de comparacion mono-objetivo' : 'The single-objective comparison arm'}>
            <p>
              {es
                ? 'El escalon 4 solo significa algo si existe una alternativa real contra la cual compararlo, asi que se incluye un brazo con la complejidad como termino de penalizacion en lugar de segundo objetivo. Sin el, la afirmacion de que el frente es mejor no seria comprobable.'
                : 'Rung 4 only means something if there is a real alternative to compare it against, so a comparison arm carrying complexity as a penalty term rather than a second objective ships alongside it. Without that, the claim that the front is better would not be checkable.'}
            </p>
          </Callout>
        </section>
      ),
    },
    {
      id: 'result',
      label: es ? 'Lo que midio' : 'What it measured',
      content: <AblationResult runs={runs} lang={es ? 'es' : 'en'} />,
    },
    {
      id: 'protocol',
      label: es ? 'Protocolo' : 'Protocol',
      content: (
        <section>
          <h3>{es ? 'Tres particiones, no dos' : 'Three splits, not two'}</h3>
          <p>
            {es
              ? 'La particion de prueba habitual responde si el modelo generaliza a filas no vistas dentro de la misma region. La particion de extrapolacion responde una pregunta distinta y mucho mas dura: si la forma descubierta sigue teniendo sentido donde ningun dato la restringio. La literatura de benchmarks es explicita en que ahi es donde todos los metodos se degradan, y en que las suites estandar la sirven mal.'
              : 'The usual test split answers whether the model generalises to unseen rows inside the same region. The extrapolation split answers a different and much harder question: whether the discovered form remains sensible where no data constrained it. The benchmark literature is explicit that this is where every method degrades, and that the standard suites under-serve it.'}{' '}
            <Cite id="defranca2024" paren />
          </p>
          <p>
            {es
              ? 'Se construye reteniendo las colas de la entrada con mayor rango, de modo que la region de entrenamiento es una caja interior. Cuando un caso es demasiado pequeno para que eso deje un entrenamiento utilizable, la particion se OMITE y el manifiesto lo dice, en lugar de fabricarse.'
              : 'It is built by holding out the tails of the widest-ranging input, so the training region is an interior box. Where a case is too small for that to leave a usable training set, the split is SKIPPED and the manifest says so, rather than being faked.'}
          </p>
          <FigThreeSplits es={es} />
          <h3>{es ? 'La prueba triple de equivalencia' : 'The triple-equivalence test'}</h3>
          <p>
            {es
              ? 'Ninguna prueba estructural aislada es fiable, asi que corren tres y se reportan sus desacuerdos en lugar de resolverlos.'
              : 'No single structural test is reliable, so three run and their disagreements are reported rather than resolved.'}
          </p>
          <FigTripleEquivalence es={es} />
          <Equation
            tex="d(f, g) = \frac{\mathrm{lev}\big(\tau(f), \tau(g)\big)}{\max\big(|\tau(f)|, |\tau(g)|\big)} \in [0, 1]"
            caption={
              es
                ? 'La distancia estructural: distancia de edicion normalizada entre las secuencias de tokens en preorden, con las constantes colapsadas a un solo simbolo para que la deriva numerica no cuente como diferencia estructural. Es la unica de las tres pruebas que da credito graduado.'
                : 'The structural distance: normalised edit distance between the pre-order token sequences, with constants collapsed to a single symbol so numeric drift is not scored as structural difference. It is the only one of the three tests that gives graded credit.'
            }
          />
          <Callout variant="honest" title={es ? 'Se publica la tasa de fallo del propio evaluador' : 'The failure rate of the scorer itself is published'}>
            <p>
              {es
                ? 'Cuando el simplificador se agota o lanza una excepcion, eso es un defecto de la HERRAMIENTA DE MEDICION, no del metodo medido. La practica comun lo cuenta como fallo del metodo, lo que penaliza sistematicamente a quien produce expresiones que el simplificador encuentra dificiles. Aqui esa tasa se reporta como un numero de primera clase.'
                : 'When the simplifier times out or throws, that is a defect of the MEASUREMENT TOOL, not of the method being measured. Common practice counts it as a method failure, which systematically penalises whichever method produces expressions the simplifier finds hard. Here that rate is reported as a first-class number.'}
            </p>
          </Callout>
          <Refs ids={['lacava2021', 'matsubara2022', 'defranca2024']} label={es ? 'Referencias' : 'References'} />
        </section>
      ),
    },
    {
      id: 'coverage',
      label: es ? 'Matriz de cobertura' : 'Coverage matrix',
      content: (
        <section>
          <h3>{es ? 'Lo que hay realmente horneado' : 'What is actually baked'}</h3>
          <p>
            {es
              ? 'Esta tabla se lee de los artefactos publicados, no se escribe a mano en la pagina, de modo que no puede quedar desactualizada respecto de lo que realmente se horneo.'
              : 'This table is read from the published artifacts rather than typed into the page, so it cannot drift away from what was actually baked.'}
          </p>
          {index ? (
            <>
              <div className="sym-table-scroll">
                <table className="sym-table">
                  <thead>
                    <tr>
                      <th>{es ? 'Caso' : 'Case'}</th>
                      <th>{es ? 'Categoria' : 'Category'}</th>
                      <th>{es ? 'Variantes' : 'Variants'}</th>
                      <th>{es ? 'Tasa de exactitud' : 'Accuracy rate'}</th>
                      <th>{es ? 'Tasa de recuperacion' : 'Recovery rate'}</th>
                      <th>{es ? 'Segundos' : 'Seconds'}</th>
                    </tr>
                  </thead>
                  <tbody>
                    {index.cases.map((entry) => (
                      <tr key={entry.case_id}>
                        <td>
                          <code>{entry.case_id}</code>
                        </td>
                        <td>{entry.category}</td>
                        <td>{entry.n_variants}</td>
                        <td>{(entry.summary.accuracy_solution_rate * 100).toFixed(0)}%</td>
                        <td>
                          {entry.summary.exact_recovery_rate === null
                            ? es
                              ? 'no comprobable'
                              : 'not checkable'
                            : `${(entry.summary.exact_recovery_rate * 100).toFixed(0)}%`}
                        </td>
                        <td>{entry.summary.total_seconds.toFixed(0)}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
              <p className="sym-note">
                {es
                  ? `${index.n_cases} casos publicados, generados el ${index.generated_on} con la version ${index.engine_version} del motor.`
                  : `${index.n_cases} cases published, generated on ${index.generated_on} with engine version ${index.engine_version}.`}
              </p>
            </>
          ) : (
            <p className="sym-empty">
              {es
                ? 'El indice de casos aun no esta disponible en este despliegue.'
                : 'The case index is not available in this deployment yet.'}
            </p>
          )}
          <Callout variant="honest" title={es ? 'Por que la columna de recuperacion suele decir no comprobable' : 'Why the recovery column often says not checkable'}>
            <p>
              {es
                ? 'Solo los casos con una respuesta publicada contribuyen a una tasa de recuperacion. Mezclarlos con los que no la tienen permitiria citar un porcentaje que incluye en silencio problemas donde la recuperacion no se puede comprobar, que es precisamente la clase de numero que este laboratorio existe para no producir.'
                : 'Only cases with a published answer contribute to a recovery rate. Mixing them with cases that have none would allow quoting a percentage that silently includes problems where recovery cannot be checked, which is precisely the kind of number this lab exists not to produce.'}
            </p>
          </Callout>
        </section>
      ),
    },
    {
      id: 'traps',
      label: es ? 'Trampas evitadas' : 'Traps avoided',
      content: (
        <section>
          <h3>{es ? 'Lo que se hizo para no inflar los resultados' : 'What was done not to inflate the results'}</h3>
          <ul>
            <li>
              <strong>{es ? 'Sin mejor-de-N.' : 'No best-of-N.'}</strong>{' '}
              {es
                ? 'Cada variante reporta su ejecucion con la semilla declarada, no la mejor de varias.'
                : 'Every variant reports its run at the declared seed, not the best of several.'}
            </li>
            <li>
              <strong>{es ? 'Sin seleccion por exactitud.' : 'No selection by accuracy.'}</strong>{' '}
              {es
                ? 'El punto reportado del frente se elige por longitud de descripcion; el criterio se imprime junto al frente.'
                : 'The reported point on the front is chosen by description length, and the criterion is printed next to the front.'}
            </li>
            <li>
              <strong>{es ? 'Sin promediar regiones.' : 'No averaging across regions.'}</strong>{' '}
              {es
                ? 'Entrenamiento, prueba y extrapolacion se reportan por separado; promediarlas oculta exactamente donde falla el metodo.'
                : 'Train, test and extrapolation are reported separately; averaging them hides exactly where the method fails.'}
            </li>
            <li>
              <strong>{es ? 'Sin descartar predicciones no finitas.' : 'No dropping non-finite predictions.'}</strong>{' '}
              {es
                ? 'Se cuentan y se reportan: una expresion que diverge en un tercio de la region de extrapolacion no debe presentar un error limpio en el resto.'
                : 'They are counted and reported: an expression diverging over a third of the extrapolation region must not present a clean error on the remainder.'}
            </li>
            <li>
              <strong>{es ? 'Contaminacion declarada.' : 'Contamination declared.'}</strong>{' '}
              {es
                ? 'El conjunto de fisica publicado lleva un aviso: es publico desde 2019 y esta dentro del corpus de preentrenamiento de los metodos preentrenados, asi que sus resultados llevan esa advertencia.'
                : 'The published physics set carries a warning: it has been public since 2019 and is inside the pretraining corpus of the pretrained methods, so results from those carry that caveat.'}
            </li>
          </ul>
          <Refs ids={['lacava2021', 'shojaee2025']} label={es ? 'Referencias' : 'References'} />
        </section>
      ),
    },
  ];

  return (
    <div className="page-body prose">
      <div className="page-head">
        <h1>{es ? 'Experimentos' : 'Experiments'}</h1>
        <p className="lede">
          {es
            ? 'El diseno, el protocolo y la matriz de cobertura leida de los artefactos reales. Cuatro de los siete pasos de la escalera anaden exactamente un mecanismo al anterior; los otros tres son compuestos y se marcan como tales, que es la diferencia entre una ablacion y una demostracion.'
            : 'The design, the protocol, and the coverage matrix read from the real artifacts. Four of the seven steps up the ladder add exactly one mechanism to the rung above; the other three are compound and are marked as such, which is the difference between an ablation and a demonstration.'}
        </p>
      </div>
      <SubTabs tabs={tabs} ariaLabel={es ? 'Aspectos experimentales' : 'Experimental aspects'} />
    </div>
  );
}
