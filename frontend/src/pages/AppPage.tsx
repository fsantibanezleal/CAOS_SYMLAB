/**
 * The App: the workbench, one case at a time.
 *
 * The two-zone shape is the house standard and is not re-derived here: a CONTROL SIDEBAR carrying
 * every selector, the global configuration and a live readout, and a MAIN AREA that carries only the
 * tabs and their views. Selection and configuration never sit in the content area, and the content
 * area never has to give up width to a list.
 *
 * The sidebar, top to bottom:
 *   1. Data source and case, through the shared shell `CaseSelector` (grouped by category, with the
 *      synthetic-versus-measured lane control and `?case=` deep linking).
 *   2. Search configuration: the ablation. Each entry differs from its neighbour by exactly ONE
 *      mechanism, so moving down the list attributes a measured difference to a named change.
 *   3. View controls: the global rendering knobs for the panes on the right.
 *   4. The live readout, refreshed by every selection above it.
 *
 * The main area is the four sub-tabs and nothing else.
 */
import { Callout, CaseSelector, SubTabs, type CaseDef, type CaseKind } from '@fasl-work/caos-app-shell';
import { useEffect, useMemo, useState } from 'react';

import type { CaseIndex, RunPayload, VariantPayload } from '../lib/contract.types';
import { loadIndex, loadRun } from '../lib/data';
import { useLang } from '../lib/useLang';
import { EquationView } from '../render/EquationView';
import { ExpressionTree } from '../render/ExpressionTree';
import { ExtrapolationPlot, ParityPlot, PartialDependence } from '../render/ModelValidation';
import { ParetoFront } from '../render/ParetoFront';
import { SearchHistory } from '../render/SearchHistory';
import { CaseContext } from './workbench/CaseContext';
import { LiveLane } from './workbench/LiveLane';

export default function AppPage() {
  const lang = useLang();
  const es = lang === 'es';

  const [index, setIndex] = useState<CaseIndex | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [source, setSource] = useState<CaseKind>('real');
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
        // Open on a REAL measured case when one is published: a harder and more honest starting
        // point than a generator whose answer is known in advance.
        const first = loaded.cases.find((c) => c.real_or_synthetic === 'real') ?? loaded.cases[0];
        if (first) {
          setCaseId(first.case_id);
          setSource(first.real_or_synthetic === 'real' ? 'real' : 'synthetic');
        }
      })
      .catch((err) => setError(String(err)));
  }, []);

  useEffect(() => {
    if (!caseId) return;
    setRun(null);
    setMemberIndex(null);
    setVariantIndex(0);
    loadRun(caseId)
      .then(setRun)
      .catch((err) => setError(String(err)));
  }, [caseId]);

  /** The published cases in the shell's own case shape. The single-letter category code is an
   *  internal key and never reaches the screen: the human name goes on the group label. */
  const cases: CaseDef[] = useMemo(() => {
    if (!index) return [];
    return index.cases.map((entry) => ({
      id: entry.case_id,
      name: es ? entry.name_es : entry.name_en,
      category: entry.category_name ?? entry.category,
      kind: entry.real_or_synthetic === 'real' ? 'real' : 'synthetic',
      anchor: entry.ground_truth_known
        ? es
          ? 'la ley verdadera se conoce, asi que la recuperacion es comprobable'
          : 'the true law is known, so recovery is checkable'
        : es
          ? 'sin forma cerrada publicada: contribuye solo a las metricas de error'
          : 'no published closed form: contributes to error metrics only',
      expectedBand: `${entry.n_variants} ${es ? 'configuraciones' : 'configurations'}`,
    }));
  }, [index, es]);

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
          <div className="sym-field">
            <EquationView
              member={member}
              targetSymbol={run.dataset.target.display}
              activeNodeId={activeNodeId}
              onHoverNode={setActiveNodeId}
              longForm={longForm}
              showRaw={showRaw}
              lang={lang}
            />

            <h3>{es ? 'La estructura detras de la formula' : 'The structure behind the formula'}</h3>
            <ExpressionTree
              payload={member.tree}
              activeNodeId={activeNodeId}
              onHoverNode={setActiveNodeId}
              collapseBelowInfluence={collapse}
              lang={lang}
            />

            <div className="sym-two-col">
              <section>
                <h3>{es ? 'Paridad y residuos' : 'Parity and residuals'}</h3>
                <ParityPlot validation={variant.validation} lang={lang} />
              </section>
              <section>
                <h3>{es ? 'Fuera del soporte' : 'Outside the support'}</h3>
                <ExtrapolationPlot validation={variant.validation} lang={lang} />
              </section>
            </div>

            <h3>{es ? 'Dependencia parcial' : 'Partial dependence'}</h3>
            <PartialDependence validation={variant.validation} lang={lang} />
          </div>
        ) : (
          <p className="sym-empty">{es ? 'Sin expresion seleccionada.' : 'No expression selected.'}</p>
        ),
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
            <h3>{es ? 'Exactitud frente a complejidad' : 'Accuracy against complexity'}</h3>
            <ParetoFront
              members={variant.pareto}
              selectedIndex={variant.selected_index}
              activeIndex={member.index}
              onSelect={setMemberIndex}
              exported={variant.pareto_exported}
              total={variant.pareto_total}
              lang={lang}
            />
            <h3>{es ? 'Progreso de la busqueda' : 'Search progress'}</h3>
            <SearchHistory history={variant.history} score={variant.score} lang={lang} />
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
        <CaseSelector
          cases={cases}
          selectedId={caseId}
          onSelect={setCaseId}
          source={source}
          onSourceChange={setSource}
          deepLink
          lang={lang}
          ariaLabel={es ? 'Seleccion de caso' : 'Case selection'}
          text={{
            source: es ? 'Origen de los datos' : 'Data source',
            synthetic: es ? 'Generador' : 'Generator',
            real: es ? 'Datos medidos' : 'Measured data',
            lockedNote: es
              ? 'Los casos medidos vienen de una planta o instrumento real: no hay parametros que ajustar, solo lo que se registro.'
              : 'Measured cases come from a real plant or instrument: there are no knobs to turn, only what was recorded.',
          }}
        />

        {run && (
          <>
            <section className="sym-control">
              <h3>{es ? 'Configuracion de busqueda' : 'Search configuration'}</h3>
              <p className="sym-control-note">
                {es
                  ? 'Cada entrada anade UN mecanismo a la anterior, asi que la diferencia medida es atribuible.'
                  : 'Each entry adds ONE mechanism to the one above it, so a measured difference is attributable.'}
              </p>
              <ul className="sym-variant-list">
                {run.notes.variants.map((v, i) => (
                  <li key={v.id}>
                    <button
                      type="button"
                      className={`sym-variant-button${i === variantIndex ? ' on' : ''}`}
                      onClick={() => {
                        setVariantIndex(i);
                        setMemberIndex(null);
                      }}
                    >
                      {es ? v.label_es : v.label_en}
                    </button>
                  </li>
                ))}
              </ul>
              {variant && (
                <p className="sym-control-note">{es ? variant.note_es : variant.note_en}</p>
              )}
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

            <section className="sym-control sym-readout">
              <h3>{es ? 'Lectura' : 'Readout'}</h3>
              <dl>
                <dt>{es ? 'filas' : 'rows'}</dt>
                <dd>{run.dataset.n_rows.toLocaleString()}</dd>
                <dt>{es ? 'entradas' : 'inputs'}</dt>
                <dd>{run.dataset.n_inputs}</dd>
                <dt>{es ? 'configuraciones' : 'configurations'}</dt>
                <dd>{run.notes.variants.length}</dd>
                <dt>{es ? 'mejor R2 prueba' : 'best test R2'}</dt>
                <dd>{bestTestR2 === null ? '-' : bestTestR2.toFixed(4)}</dd>
              </dl>
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
