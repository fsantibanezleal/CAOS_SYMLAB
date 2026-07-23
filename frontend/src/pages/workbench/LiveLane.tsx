/**
 * The Live lane: a real symbolic-regression search running in the reader's browser.
 *
 * This is the differentiator, and it exists because of a hard constraint found during research:
 * there is no maintained JavaScript, TypeScript or WebAssembly symbolic-regression library. The only
 * two options were to run the Python core under Pyodide, or to fork the core into TypeScript. The
 * fork was rejected because it would create two engines that must be kept in agreement forever, and
 * an offline-versus-live parity failure is exactly the kind of defect that produces published
 * numbers nobody can reproduce.
 *
 * So the browser runs the SAME code the pipeline runs. The engine is imported from the committed
 * package source, at a reduced budget, on data generated in the browser from the same generator the
 * offline lane uses. Reduced budget, identical algorithm: the honest form of a live demonstration.
 *
 * That last sentence bounds what this tab can do. Data is regenerated in the browser from a
 * first-principles generator, so the tab can only run the cases that HAVE one. On a measured plant
 * dataset or a physics suite loaded from a file the worker refuses, by design: this line used to
 * fall back to the Monod generator, and a reader on a plant dataset pressed Run and was shown a
 * result for a different problem under their case's heading.
 *
 * The configuration is fixed at the Pareto-survival rung, not taken from the sidebar selection, so
 * the panel names the rung it ran rather than implying it mirrors whatever is selected.
 *
 * Nothing starts automatically. Loading a Python runtime and running an evolutionary search on page
 * view would burn a reader's battery for a result they did not ask for.
 */
import { Callout } from '@fasl-work/caos-app-shell';
import { useCallback, useRef, useState } from 'react';

import type { RunPayload } from '../../lib/contract.types';

type Status = 'idle' | 'loading' | 'running' | 'done' | 'error';

interface LiveResult {
  /** The generator that actually produced the rows, named so the panel cannot imply a case it did
   *  not run. The worker refuses rather than substituting, so this always matches the selection. */
  generator: string;
  latex: string;
  infix: string;
  complexity: number;
  mse: number;
  seconds: number;
  evaluations: number;
  front_size: number;
  method: 'gp' | 'sparse';
  /** Null for the sparse arm, which has neither. Rendering a blank there would read as a missing
   *  number rather than as a budget the method does not have. */
  generations: number | null;
  population: number | null;
}

export function LiveLane({ run, lang }: { run: RunPayload; lang: 'en' | 'es' }) {
  const es = lang === 'es';
  const [status, setStatus] = useState<Status>('idle');
  const [message, setMessage] = useState('');
  const [result, setResult] = useState<LiveResult | null>(null);
  const [population, setPopulation] = useState(80);
  const [generations, setGenerations] = useState(12);
  const [seed, setSeed] = useState(0);
  /** Which search FAMILY runs in the browser. The sparse arm has no population and no generations,
   *  so those controls are hidden for it rather than shown doing nothing. */
  const [method, setMethod] = useState<'gp' | 'sparse'>('gp');
  const workerRef = useRef<Worker | null>(null);

  const start = useCallback(() => {
    setStatus('loading');
    setMessage(es ? 'Cargando el motor de Python en el navegador...' : 'Loading the Python engine in the browser...');
    setResult(null);

    const worker = new Worker(new URL('../../live/search.worker.ts', import.meta.url), {
      type: 'module',
    });
    workerRef.current?.terminate();
    workerRef.current = worker;

    worker.onmessage = (event: MessageEvent) => {
      const data = event.data as { kind: string; text?: string; result?: LiveResult };
      if (data.kind === 'status') {
        setStatus('running');
        setMessage(data.text ?? '');
      } else if (data.kind === 'result' && data.result) {
        setResult(data.result);
        setStatus('done');
        setMessage('');
      } else if (data.kind === 'error') {
        setStatus('error');
        setMessage(data.text ?? 'unknown error');
      }
    };

    worker.postMessage({
      generatorId: run.notes.case_id,
      population,
      generations,
      seed,
      method,
    });
  }, [run.notes.case_id, population, generations, seed, method, es]);

  const isSparse = method === 'sparse';

  const stop = useCallback(() => {
    workerRef.current?.terminate();
    workerRef.current = null;
    setStatus('idle');
    setMessage('');
  }, []);

  return (
    <div className="sym-live">
      <Callout variant="note" title={es ? 'La misma implementacion, presupuesto reducido' : 'The same implementation, reduced budget'}>
        <p>
          {es
            ? 'Esta busqueda ejecuta EL MISMO codigo que el horneado sin conexion, cargado en el navegador. No es una reimplementacion en JavaScript: mantener dos motores de acuerdo para siempre es exactamente el tipo de defecto que produce numeros publicados que nadie puede reproducir. Con el mismo caso, semilla y presupuesto, ambos carriles devuelven la MISMA expresion, y eso se comprueba en vez de afirmarse: un arnes de paridad ejecuta esta pestana en un navegador real y la tuberia en local, y los compara. El presupuesto aqui es menor, asi que espera una expresion mas simple que la de la pestana Expresion, no una ley distinta. Regenera sus datos en el navegador a partir de un generador de primeros principios, asi que solo corre en los casos que este laboratorio genera por si mismo: sobre datos medidos, o sobre una suite de fisica cargada desde archivo como los casos de Feynman y Strogatz, se niega, porque ejecutar otro problema bajo el nombre de este caso seria peor que no ejecutar nada.'
            : 'This search runs THE SAME code as the offline bake, loaded into the browser. It is not a JavaScript reimplementation: keeping two engines in agreement forever is exactly the kind of defect that produces published numbers nobody can reproduce. At the same case, seed and budget the two lanes return the IDENTICAL expression, which is checked rather than claimed: a parity harness drives this tab in a real browser and the pipeline locally and compares them. The budget here is smaller, so expect a simpler expression than the Expression tab shows, not a different law. It regenerates its data in the browser from a first-principles generator, so it runs only on the cases this lab generates itself: on a measured dataset, or on a physics suite loaded from a file such as the Feynman and Strogatz cases, it refuses, because running a different problem under this case name would be worse than not running at all.'}
        </p>
        <p>
          {es
            ? 'Nada se ejecuta hasta que lo pidas. Cargar un runtime de Python y correr una busqueda evolutiva al abrir la pagina gastaria la bateria del lector por un resultado que no pidio.'
            : 'Nothing runs until you ask. Loading a Python runtime and running an evolutionary search on page view would burn a reader battery for a result they did not ask for.'}
        </p>
      </Callout>

      <div className="sym-live-controls">
        <label className="sym-live-method">
          {es ? 'familia' : 'family'}
          <select
            className="sym-select"
            value={method}
            onChange={(event) => setMethod(event.target.value as 'gp' | 'sparse')}
            disabled={status === 'running' || status === 'loading'}
          >
            <option value="gp">{es ? 'programacion genetica' : 'genetic programming'}</option>
            <option value="sparse">{es ? 'regresion dispersa' : 'sparse regression'}</option>
          </select>
        </label>
        {/* The sparse arm has no population and no generations. Showing those sliders for it would
            offer knobs that change nothing, which is worse than not offering them. */}
        <label hidden={isSparse}>
          {es ? 'poblacion' : 'population'}
          <input
            type="range"
            min={30}
            max={200}
            step={10}
            value={population}
            onChange={(event) => setPopulation(Number(event.target.value))}
            disabled={status === 'running' || status === 'loading'}
          />
          <output>{population}</output>
        </label>
        <label hidden={isSparse}>
          {es ? 'generaciones' : 'generations'}
          <input
            type="range"
            min={4}
            max={40}
            step={2}
            value={generations}
            onChange={(event) => setGenerations(Number(event.target.value))}
            disabled={status === 'running' || status === 'loading'}
          />
          <output>{generations}</output>
        </label>
        <label>
          {es ? 'semilla' : 'seed'}
          <input
            type="number"
            min={0}
            max={999}
            value={seed}
            onChange={(event) => setSeed(Number(event.target.value))}
            disabled={status === 'running' || status === 'loading'}
          />
        </label>
        {status === 'running' || status === 'loading' ? (
          <button type="button" className="chip on" onClick={stop}>
            {es ? 'detener' : 'stop'}
          </button>
        ) : (
          <button type="button" className="chip on" onClick={start}>
            {es ? 'ejecutar la busqueda aqui' : 'run the search here'}
          </button>
        )}
      </div>

      {message && <p className="sym-live-status">{message}</p>}

      {status === 'error' && (
        <Callout variant="honest" title={es ? 'La ejecucion en vivo fallo' : 'The live run failed'}>
          <p>{message}</p>
          <p>
            {es
              ? 'La vista de reproduccion sigue disponible: el resultado horneado no depende de este panel.'
              : 'The replay view is unaffected: the baked result does not depend on this panel.'}
          </p>
        </Callout>
      )}

      {result && (
        <div className="sym-live-result">
          <h4>{es ? 'Lo que encontro tu navegador' : 'What your browser found'}</h4>
          <pre className="sym-live-expression">{result.infix}</pre>
          <dl>
            <dt>{es ? 'generador' : 'generator'}</dt>
            <dd>{result.generator}</dd>
            <dt>{es ? 'complejidad' : 'complexity'}</dt>
            <dd>{result.complexity}</dd>
            <dt>MSE</dt>
            <dd>{result.mse.toExponential(3)}</dd>
            <dt>{es ? 'segundos' : 'seconds'}</dt>
            <dd>{result.seconds.toFixed(1)}</dd>
            <dt>{es ? 'presupuesto' : 'budget'}</dt>
            <dd>
              {result.population === null || result.generations === null
                ? es
                  ? 'sin poblacion ni generaciones: el brazo disperso no tiene ninguna de las dos'
                  : 'no population and no generations: the sparse arm has neither'
                : `${result.population} x ${result.generations}`}
            </dd>
          </dl>
          <p className="sym-note">
            {es
              ? 'Compara esto con el resultado horneado del escalon de supervivencia de Pareto, que es la configuracion que este panel ejecuta siempre, y no con la variante seleccionada en la barra lateral. Una diferencia no es un error: el presupuesto es mucho menor aqui y las filas se regeneran en el navegador, y ver cuanto cambia el resultado con el presupuesto es en si mismo el punto.'
              : 'Compare this with the baked result for the Pareto-survival rung, which is the configuration this panel always runs, not with whichever variant is selected in the sidebar. A difference is not an error: the budget here is far smaller and the rows are regenerated in the browser, and seeing how much the result moves with the budget is itself the point.'}
          </p>
        </div>
      )}
    </div>
  );
}
