/**
 * The App: the workbench, one case at a time.
 *
 * Structure comes from the shared shell, not from this file. `CaseSelector` is the standard case
 * control for this family of apps: it groups by category with real labels, ships the first-level
 * SOURCE control that separates synthetic cases from real measured ones, deep-links the selection
 * into `?case=`, and puts the validation anchor in each chip tooltip. An earlier version of this
 * page hand-rolled a sidebar list instead, which is the exact thing the shared shell exists to
 * prevent: it rendered raw category codes, scattered the controls away from the content, and
 * starved the visualisations of width.
 *
 * The page reads top to bottom as CHOOSE, then SEE, then EXPLORE, at the full page width:
 *
 * 1. `CaseSelector`: source lane, then the case, grouped by category.
 * 2. The case head and a compact strip of what that case is, with the two rates side by side.
 * 3. The variant bar: the ablation. Each chip differs from its neighbour by exactly ONE mechanism,
 *    so moving along it attributes a measured difference to a named change rather than to a bundle.
 * 4. Four sub-tabs: the Expression, the Live browser search, the Front and search, and the Context.
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
        // Open on a REAL measured case when one is published. That is the harder and more honest
        // starting point than a generator whose answer is known in advance.
        const real = loaded.cases.find((c) => c.real_or_synthetic === 'real');
        const first = real ?? loaded.cases[0];
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
          ? 'sin forma cerrada publicada: solo contribuye a las metricas de error'
          : 'no published closed form: contributes to error metrics only',
      expectedBand: `${entry.n_variants} ${es ? 'configuraciones de busqueda' : 'search configurations'}`,
    }));
  }, [index, es]);

  const variant: VariantPayload | null = useMemo(() => {
    if (!run || run.notes.variants.length === 0) return null;
    return run.notes.variants[Math.min(variantIndex, run.notes.variants.length - 1)];
  }, [run, variantIndex]);

  /** The best held-out R2 across the configurations, so the strip states real model quality next to
   *  the threshold COUNTS. Without it, a reader sees a count of zero and reads it as zero accuracy. */
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
            <div className="sym-field-controls">
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
                {es ? 'salida cruda del motor' : 'raw engine output'}
              </button>
              <label className="sym-slider">
                {es ? 'colapsar bajo influencia' : 'collapse below influence'}
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
            </div>

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
    <div className="page-body symlab-page">
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
          synthetic: es ? 'Generador (verdad conocida)' : 'Generator (truth known)',
          real: es ? 'Datos medidos' : 'Measured data',
          lockedNote: es
            ? 'Los casos medidos vienen de un instrumento o de una planta real: no hay parametros que ajustar, solo lo que se registro.'
            : 'Measured cases come from a real instrument or plant: there are no knobs to turn, only what was recorded.',
        }}
      />

      {!run ? (
        <p className="sym-loading">{es ? 'Cargando el caso...' : 'Loading the case...'}</p>
      ) : (
        <>
          <div className="page-head">
            <h1>{es ? run.notes.name_es : run.notes.name_en}</h1>
            <p className="lede">{es ? run.notes.summary_es : run.notes.summary_en}</p>
          </div>

          <div className="sym-kpis">
            <div>
              <span>{es ? 'filas' : 'rows'}</span>
              <strong>{run.dataset.n_rows.toLocaleString()}</strong>
            </div>
            <div>
              <span>{es ? 'entradas' : 'inputs'}</span>
              <strong>{run.dataset.n_inputs}</strong>
            </div>
            <div>
              <span>{es ? 'configuraciones' : 'configurations'}</span>
              <strong>{run.notes.variants.length}</strong>
            </div>
            <div>
              <span>{es ? 'mejor R2 en prueba' : 'best test R2'}</span>
              <strong>{bestTestR2 === null ? '-' : bestTestR2.toFixed(4)}</strong>
            </div>
            {/* Named for what it MEASURES, not for what it sounds like. "accuracy rate" read as
                "how accurate is the model", which is a different question and made a reader
                misinterpret a correct number. It is a COUNT of configurations clearing a threshold. */}
            <div className="sym-kpi-pair">
              <span>
                {es ? 'configs sobre R2 > 0,999' : 'configs above R2 > 0.999'}
              </span>
              <strong>
                {run.notes.summary.accuracy_solutions} / {run.notes.summary.n_variants}
              </strong>
            </div>
            <div className="sym-kpi-pair">
              <span>{es ? 'estructura recuperada' : 'structure recovered'}</span>
              <strong>
                {run.notes.summary.exact_recovery_rate === null
                  ? es ? 'no comprobable' : 'not checkable'
                  : `${run.notes.summary.exact_recoveries} / ${run.notes.summary.n_variants}`}
              </strong>
            </div>
          </div>
          <p className="sym-gap-note">
            {run.notes.ground_truth_known
              ? es
                ? 'Las dos ultimas cuentan configuraciones, no exactitud. La primera cuenta cuantas superan el umbral de solucion por exactitud; la segunda, cuantas recuperaron realmente la expresion correcta. La brecha entre ambas es la medicion mas importante de este laboratorio: ajustar bien no es haber encontrado la ley.'
                : 'The last two count configurations, not accuracy. The first counts how many clear the accuracy-solution threshold; the second, how many actually recovered the correct expression. The gap between them is this lab’s most important measurement: fitting well is not the same as having found the law.'
              : es
                ? 'Este caso no tiene una forma cerrada publicada contra la cual comparar, asi que la recuperacion NO se puede comprobar aqui y no se reporta como cero. Contribuye a las metricas de error unicamente. Los casos con verdad conocida son los que sostienen la tasa de recuperacion.'
                : 'This case has no published closed form to compare against, so recovery is NOT checkable here and is not reported as zero. It contributes to the error metrics only. The cases with a known truth are the ones that carry the recovery rate.'}
          </p>

          <div className="variant-bar">
            <span className="variant-bar-label">
              {es ? 'configuracion de busqueda' : 'search configuration'} ({run.notes.variants.length})
              {' · '}
              {es ? 'reproducido' : 'replayed'}
            </span>
            <div className="variant-chips">
              {run.notes.variants.map((v, i) => (
                <button
                  key={v.id}
                  type="button"
                  className={`variant-chip${i === variantIndex ? ' active' : ''}`}
                  onClick={() => {
                    setVariantIndex(i);
                    setMemberIndex(null);
                  }}
                >
                  {es ? v.label_es : v.label_en}
                </button>
              ))}
            </div>
            {variant && <p className="variant-note">{es ? variant.note_es : variant.note_en}</p>}
          </div>

          <SubTabs tabs={subTabs} ariaLabel={es ? 'Vistas del caso' : 'Case views'} />
        </>
      )}

      {/* The count describes what is SHOWN against what exists. An earlier version quoted the
          registry total next to a much shorter list, which read as a straightforward lie. */}
      <p className="sym-catalogue-note">
        {es
          ? `${index.cases.length} casos publicados, ${index.cases.filter((c) => c.real_or_synthetic === 'real').length} sobre datos reales medidos.`
          : `${index.cases.length} published cases, ${index.cases.filter((c) => c.real_or_synthetic === 'real').length} on real measured data.`}
        {pending > 0 && (
          <>
            {' '}
            {es
              ? `El registro define ${index.coverage.n_cases}; los ${pending} restantes se hornean sin conexion y aparecen al terminar.`
              : `The registry defines ${index.coverage.n_cases}; the remaining ${pending} bake offline and appear as they finish.`}
          </>
        )}
      </p>
    </div>
  );
}
