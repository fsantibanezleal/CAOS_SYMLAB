/**
 * The App: the workbench, one case at a time.
 *
 * Two zones. A CONTROL SIDEBAR carrying every selector, the global configuration and a live
 * readout, and a MAIN AREA carrying only the tabs and their views. Selection and configuration
 * never sit in the content area, and the content area never gives up width to a list.
 *
 * The sidebar, top to bottom:
 *   1. Source lane, category, case: three dropdowns, not a chip deck. Twenty-five cases across six
 *      categories do not fit a deck in a sidebar column.
 *   2. Search configuration: the ablation. Each entry differs from its neighbour by exactly ONE
 *      mechanism, so moving down the list attributes a measured difference to a named change.
 *   3. View controls for the panes on the right.
 *   4. The readout, refreshed by every selection above it.
 *
 * The tabs follow the order a reader actually needs:
 *   1. Expression   what the search found, next to the relationship we expected, with the verdict
 *   2. Structure    the tree, and the components the expression is built from
 *   3. Validation   parity, residuals per input, extrapolation, partial dependence
 *   4. Live         the same engine run in the browser, on demand
 *   5. Front        accuracy against complexity, and the search that earned it
 *   6. Context      provenance, sampling, caveats, certificate
 */
import { Callout, SubTabs } from '@fasl-work/caos-app-shell';
import { useEffect, useMemo, useState } from 'react';

import type { CaseIndex, RunPayload, VariantPayload } from '../lib/contract.types';
import { loadIndex, loadRun } from '../lib/data';
import { useLang } from '../lib/useLang';
import { CaseNavigator, type SourceLane } from '../render/CaseNavigator';
import { ExpressionPanel } from '../render/ExpressionPanel';
import { ParetoFront } from '../render/ParetoFront';
import { SearchHistory } from '../render/SearchHistory';
import { StructurePanel } from '../render/StructurePanel';
import { ValidationPanel } from '../render/ValidationPanel';
import { CaseContext } from './workbench/CaseContext';
import { LiveLane } from './workbench/LiveLane';
import { groupDigits } from '../lib/format';


export default function AppPage() {
  const lang = useLang();
  const es = lang === 'es';

  const [index, setIndex] = useState<CaseIndex | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [source, setSource] = useState<SourceLane>('real');
  const [caseId, setCaseId] = useState<string>('');
  const [run, setRun] = useState<RunPayload | null>(null);
  const [variantIndex, setVariantIndex] = useState(0);
  const [memberIndex, setMemberIndex] = useState<number | null>(null);
  const [activeNodeId, setActiveNodeId] = useState<number | null>(null);
  const [longForm, setLongForm] = useState(false);
  const [showRaw, setShowRaw] = useState(false);
  const [collapse, setCollapse] = useState(0);

  useEffect(() => {
    loadIndex()
      .then((loaded) => {
        setIndex(loaded);
        // Honour a ?case= deep link over the default, so a shared URL opens what was shared.
        const requested = new URLSearchParams(window.location.search).get('case');
        const target =
          loaded.cases.find((c) => c.case_id === requested) ??
          // Otherwise open on a REAL measured case: a harder and more honest starting point than a
          // generator whose answer is known in advance.
          loaded.cases.find((c) => c.real_or_synthetic === 'real') ??
          loaded.cases[0];
        if (target) {
          setCaseId(target.case_id);
          setSource(target.real_or_synthetic === 'real' ? 'real' : 'synthetic');
        }
      })
      .catch((err) => setError(String(err)));
  }, []);

  useEffect(() => {
    if (!caseId) return;
    setRun(null);
    setMemberIndex(null);
    setVariantIndex(0);
    setActiveNodeId(null);
    loadRun(caseId)
      .then(setRun)
      .catch((err) => setError(String(err)));
  }, [caseId]);

  const variant: VariantPayload | null = useMemo(() => {
    if (!run || run.notes.variants.length === 0) return null;
    return run.notes.variants[Math.min(variantIndex, run.notes.variants.length - 1)];
  }, [run, variantIndex]);

  /** Best held-out R2 across the configurations, so the readout states real model quality next to
   *  the threshold COUNTS. Without it, a count of zero reads as zero accuracy. */
  const bestTestR2 = useMemo(() => {
    if (!run) return null;
    const values = run.notes.variants
      .map((v) => v.score.best_test_r2)
      .filter((v): v is number => v !== null && Number.isFinite(v));
    return values.length > 0 ? Math.max(...values) : null;
  }, [run]);

  /** The row accounting, with a fallback for artifacts baked before it shipped. Falling back keeps
   *  an older artifact readable instead of rendering blanks where numbers belong. */
  const rows = useMemo(() => {
    const published = run?.dataset.rows;
    if (published) return { ...published, published: true as const };
    const train = run?.dataset.n_rows ?? 0;
    // An artifact baked before the accounting shipped knows its training rows and NOTHING else.
    // Printing "test rows 0" for it would be a false statement, so those fields are withheld
    // rather than filled with a zero that reads as a measurement.
    return { source: null, used: train, train, test: 0, extrapolation: 0, published: false as const };
  }, [run]);

  const member = useMemo(() => {
    if (!variant || variant.pareto.length === 0) return null;
    const target = memberIndex ?? variant.selected_index;
    return variant.pareto[Math.min(target, variant.pareto.length - 1)] ?? variant.pareto[0];
  }, [variant, memberIndex]);

  if (error) {
    return (
      <div className="page-body">
        <Callout
          variant="honest"
          title={es ? 'No se pudieron cargar los artefactos' : 'Artifacts could not be loaded'}
        >
          <p>{error}</p>
          <p>
            {es
              ? 'Los artefactos se generan sin conexion y se publican junto a la aplicacion. Si ves esto, el horneado aun no ha terminado para este despliegue.'
              : 'Artifacts are generated offline and published alongside the app. If you are seeing this, the bake has not completed for this deployment.'}
          </p>
        </Callout>
      </div>
    );
  }

  if (!index) {
    return (
      <div className="page-body">
        <p className="sym-loading">
          {es ? 'Cargando el catalogo de casos...' : 'Loading the case catalogue...'}
        </p>
      </div>
    );
  }

  const subTabs = [
    {
      id: 'expression',
      label: es ? 'Expresion' : 'Expression',
      content:
        member && variant && run ? (
          <ExpressionPanel
            member={member}
            targetSymbol={run.dataset.target.display}
            truthLatex={run.notes.ground_truth_latex}
            truthAvailable={Boolean(run.notes.ground_truth_available ?? run.notes.ground_truth_latex)}
            notCheckableReason={run.notes.not_checkable_reason ?? ''}
            regime={run.notes.regime ?? 'unknown'}
            score={variant.score}
            variantLabel={es ? variant.label_es : variant.label_en}
            longForm={longForm}
            showRaw={showRaw}
            onHoverNode={setActiveNodeId}
            lang={lang}
          />
        ) : (
          <p className="sym-empty">{es ? 'Sin expresion seleccionada.' : 'No expression selected.'}</p>
        ),
    },
    {
      id: 'structure',
      label: es ? 'Estructura' : 'Structure',
      content:
        member && variant ? (
          <StructurePanel
            member={member}
            validation={variant.validation}
            activeNodeId={activeNodeId}
            onHoverNode={setActiveNodeId}
            collapseBelowInfluence={collapse}
            lang={lang}
          />
        ) : null,
    },
    {
      id: 'validation',
      label: es ? 'Paridad y residuos' : 'Parity and residuals',
      content:
        variant && run ? (
          <ValidationPanel
            validation={variant.validation}
            parityInputs={run.notes.parity_inputs}
            lang={lang}
          />
        ) : null,
    },
    {
      id: 'live',
      label: es ? 'En vivo (tu navegador)' : 'Live (your browser)',
      content: run ? <LiveLane run={run} lang={lang} /> : null,
    },
    {
      id: 'front',
      label: es ? 'Frente y busqueda' : 'Front and search',
      content:
        variant && member ? (
          <div className="sym-charts">
            <section className="sym-block">
              <h3>{es ? 'Exactitud frente a complejidad' : 'Accuracy against complexity'}</h3>
              <p className="sym-block-lede">
                {es
                  ? 'Cada punto es una expresion del frente. Haz clic en uno y las demas pestanas cargan esa expresion.'
                  : 'Each point is one expression on the front. Click one and every other tab loads that expression.'}
              </p>
              <ParetoFront
                members={variant.pareto}
                selectedIndex={variant.selected_index}
                activeIndex={member.index}
                onSelect={setMemberIndex}
                exported={variant.pareto_exported}
                total={variant.pareto_total}
                lang={lang}
              />
            </section>
            <section className="sym-block">
              <h3>{es ? 'Progreso de la busqueda' : 'Search progress'}</h3>
              <SearchHistory history={variant.history} score={variant.score} lang={lang} />
            </section>
          </div>
        ) : null,
    },
    {
      id: 'context',
      label: es ? 'Contexto' : 'Context',
      content: run ? <CaseContext run={run} lang={lang} /> : null,
    },
  ];

  const pending = index.coverage.n_cases - index.cases.length;

  return (
    <div className="page-body symlab-layout">
      {/* ---------------------------------------------------------------- CONTROL SIDEBAR */}
      <aside className="symlab-side">
        <CaseNavigator
          entries={index.cases}
          selectedId={caseId}
          onSelect={setCaseId}
          source={source}
          onSourceChange={setSource}
          lang={lang}
        />

        {run && (
          <>
            <section className="sym-control">
              <h3>{es ? 'Configuracion de busqueda' : 'Search configuration'}</h3>
              {/* Grouped by FAMILY. The sparse arm is not a further step along the ladder, and
                  listing it as one would imply it adds a mechanism to the rung above it, which is
                  the single claim the ladder design exists to make. */}
              <label className="sym-nav-field">
                <span className="sym-nav-label">
                  {es ? 'Metodo' : 'Method'}
                </span>
                <select
                  className="sym-select"
                  value={variantIndex}
                  onChange={(event) => {
                    setVariantIndex(Number(event.target.value));
                    setMemberIndex(null);
                  }}
                >
                  <optgroup label={es ? 'Escalera de programacion genetica' : 'Genetic-programming ladder'}>
                    {run.notes.variants.map((v, i) =>
                      (v.method ?? 'gp') === 'gp' ? (
                        <option key={v.id} value={i}>
                          {es ? v.label_es : v.label_en}
                        </option>
                      ) : null,
                    )}
                  </optgroup>
                  {run.notes.variants.some((v) => (v.method ?? 'gp') !== 'gp') && (
                    <optgroup label={es ? 'Otras familias' : 'Other families'}>
                      {run.notes.variants.map((v, i) =>
                        (v.method ?? 'gp') !== 'gp' ? (
                          <option key={v.id} value={i}>
                            {es ? v.label_es : v.label_en}
                          </option>
                        ) : null,
                      )}
                    </optgroup>
                  )}
                </select>
              </label>
              {variant && <p className="sym-control-note">{es ? variant.note_es : variant.note_en}</p>}
              <p className="sym-control-note">
                {(variant?.method ?? 'gp') === 'gp'
                  ? es
                    ? 'La mayoria de los escalones anade exactamente UN mecanismo al anterior, asi que la diferencia medida es atribuible a ese cambio concreto. Tres no lo hacen, y decirlo es justamente el sentido de una ablacion: r2 enciende el escalado lineal Y la guarda de intervalos a la vez, porque la aportacion de Keijzer son ambos; r6 anade age-fitness e islas mientras APAGA la supervivencia multiobjetivo; r7 la vuelve a encender junto con las dos deduplicaciones. Lee esos tres como pasos compuestos.'
                    : 'Most rungs add exactly ONE mechanism to the one above them, so a measured difference is attributable to that named change. Three do not, and saying so is the point of an ablation: r2 turns on linear scaling AND the interval guard together, because Keijzer\'s contribution is both; r6 adds age-fitness and islands while turning multi-objective survival OFF; r7 turns it back on alongside both deduplication switches. Read those three as compound steps.'
                  : es
                    ? 'Esta no es un escalon de la escalera sino OTRA familia de busqueda. Comparala con la escalera completa, no con el escalon de arriba: no anade un mecanismo a nada.'
                    : 'This is not a rung of the ladder but a DIFFERENT search family. Compare it against the ladder as a whole rather than against the entry above it: it does not add a mechanism to anything.'}
              </p>
            </section>

            <section className="sym-control">
              <h3>{es ? 'Vista' : 'View'}</h3>
              <div className="sym-control-chips">
                <button
                  type="button"
                  className={`chip${longForm ? ' on' : ''}`}
                  onClick={() => setLongForm((v) => !v)}
                >
                  {es ? 'forma larga' : 'long form'}
                </button>
                <button
                  type="button"
                  className={`chip${showRaw ? ' on' : ''}`}
                  onClick={() => setShowRaw((v) => !v)}
                >
                  {es ? 'salida cruda' : 'raw output'}
                </button>
              </div>
              <label className="sym-slider-block">
                <span>{es ? 'colapsar bajo influencia' : 'collapse below influence'}</span>
                <input
                  type="range"
                  min={0}
                  max={0.3}
                  step={0.01}
                  value={collapse}
                  onChange={(event) => setCollapse(Number(event.target.value))}
                />
                <output>{collapse.toFixed(2)}</output>
              </label>
            </section>

            {/* `sym-readout` is the chart-hover strip and is display:flex. This block must not
                borrow that class or the heading lands beside the numbers. */}
            <section className="sym-control sym-side-readout">
              <h3>{es ? 'Lectura' : 'Readout'}</h3>
              <div className="sym-side-kpis">
                <div>
                  <span>{es ? 'filas de entrenamiento' : 'training rows'}</span>
                  <strong>{groupDigits(rows.train)}</strong>
                </div>
                {rows.published && (
                  <div>
                    <span>{es ? 'filas de prueba' : 'test rows'}</span>
                    <strong>{groupDigits(rows.test)}</strong>
                  </div>
                )}
                <div>
                  <span>{es ? 'entradas' : 'inputs'}</span>
                  <strong>{run.dataset.n_inputs}</strong>
                </div>
                <div>
                  <span>{es ? 'escalones' : 'rungs'}</span>
                  <strong>{run.notes.variants.length}</strong>
                </div>
                <div>
                  <span>{es ? 'mejor R2' : 'best R2'}</span>
                  <strong>{bestTestR2 === null ? '-' : bestTestR2.toFixed(4)}</strong>
                </div>
              </div>
              <p className="sym-control-note">
                {!rows.published
                  ? es
                    ? `${groupDigits(rows.train)} filas de entrenamiento. Este artefacto se horneo antes de que se publicara el desglose completo de filas; se volvera a hornear.`
                    : `${groupDigits(rows.train)} training rows. This artifact was baked before the full row accounting shipped; it is being re-baked.`
                  : rows.source !== null && rows.source > rows.used
                  ? es
                    ? `${groupDigits(rows.used)} filas usadas de las ${groupDigits(rows.source)} que trae la fuente, submuestreadas de forma determinista. ${groupDigits(rows.extrapolation)} se reservan fuera del soporte.`
                    : `${groupDigits(rows.used)} rows used of the ${groupDigits(rows.source)} the source ships, subsampled deterministically. ${groupDigits(rows.extrapolation)} are held out beyond the support.`
                  : es
                    ? `${groupDigits(rows.used)} filas en total, de las cuales ${groupDigits(rows.extrapolation)} se reservan fuera del soporte de entrenamiento.`
                    : `${groupDigits(rows.used)} rows in total, of which ${groupDigits(rows.extrapolation)} are held out beyond the training support.`}
              </p>
              <dl className="sym-readout-rates">
                <dt>{es ? 'sobre R2 > 0,999' : 'above R2 > 0.999'}</dt>
                <dd>
                  {run.notes.summary.accuracy_solutions} / {run.notes.summary.n_variants}
                </dd>
                <dt>{es ? 'estructura recuperada' : 'structure recovered'}</dt>
                <dd>
                  {run.notes.summary.exact_recovery_rate === null
                    ? es ? 'no comprobable' : 'not checkable'
                    : `${run.notes.summary.exact_recoveries} / ${run.notes.summary.n_variants}`}
                </dd>
              </dl>
              <p className="sym-control-note">
                {run.notes.ground_truth_known
                  ? es
                    ? 'Las dos ultimas cuentan configuraciones, no exactitud. La brecha entre ellas es la medicion mas importante de este laboratorio: ajustar bien no es haber encontrado la ley.'
                    : 'The last two count configurations, not accuracy. The gap between them is this lab’s most important measurement: fitting well is not the same as having found the law.'
                  : es
                    ? 'Este caso no tiene forma cerrada publicada, asi que la recuperacion NO es comprobable y no se reporta como cero.'
                    : 'This case has no published closed form, so recovery is NOT checkable and is not reported as zero.'}
              </p>
            </section>
          </>
        )}

        <p className="sym-catalogue-note">
          {es
            ? `${index.cases.length} casos publicados, ${index.cases.filter((c) => c.real_or_synthetic === 'real').length} sobre datos reales medidos.`
            : `${index.cases.length} published cases, ${index.cases.filter((c) => c.real_or_synthetic === 'real').length} on real measured data.`}
          {pending > 0 && (
            <>
              {' '}
              {es
                ? `El registro define ${index.coverage.n_cases}; los ${pending} restantes se hornean sin conexion.`
                : `The registry defines ${index.coverage.n_cases}; the remaining ${pending} bake offline.`}
            </>
          )}
        </p>
      </aside>

      {/* ---------------------------------------------------------------- CONTENT ONLY */}
      <main className="symlab-main">
        {!run ? (
          <p className="sym-loading">{es ? 'Cargando el caso...' : 'Loading the case...'}</p>
        ) : (
          <>
            <div className="page-head">
              <h1>{es ? run.notes.name_es : run.notes.name_en}</h1>
              <p className="lede">{es ? run.notes.summary_es : run.notes.summary_en}</p>
            </div>
            <SubTabs tabs={subTabs} ariaLabel={es ? 'Vistas del caso' : 'Case views'} />
          </>
        )}
      </main>
    </div>
  );
}
