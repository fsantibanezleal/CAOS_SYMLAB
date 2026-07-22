/**
 * Loading the committed artifacts.
 *
 * Every fetch is cache-busted with the app version. Static hosting serves the entry document from a
 * CDN cache, and a stale data file next to a fresh bundle is a failure mode that presents as
 * "the numbers are wrong" rather than as an error, which makes it expensive to diagnose.
 *
 * The schema is asserted on arrival. A payload whose major version this build does not understand is
 * refused visibly rather than rendered as an empty panel.
 */
import {
  assertSchemaSupported,
  type CaseIndex,
  type RunPayload,
} from './contract.types';
import { VERSION } from './links';

const BASE = `${import.meta.env.BASE_URL ?? '/'}data`;

async function fetchJson<T>(path: string): Promise<T> {
  const response = await fetch(`${path}?v=${VERSION}`, { cache: 'no-cache' });
  if (!response.ok) {
    throw new Error(`${path} returned ${response.status} ${response.statusText}`);
  }
  return (await response.json()) as T;
}

let indexCache: Promise<CaseIndex> | null = null;

export function loadIndex(): Promise<CaseIndex> {
  if (!indexCache) {
    indexCache = fetchJson<CaseIndex>(`${BASE}/manifests/index.json`).then((index) => {
      assertSchemaSupported(index.schema_version, 'the case index');
      return index;
    });
  }
  return indexCache;
}

const runCache = new Map<string, Promise<RunPayload>>();

export function loadRun(caseId: string): Promise<RunPayload> {
  const cached = runCache.get(caseId);
  if (cached) return cached;
  const pending = fetchJson<RunPayload>(`${BASE}/derived/${caseId}/run.json`).then((run) => {
    assertSchemaSupported(run.schema_version, `case ${caseId}`);
    return run;
  });
  runCache.set(caseId, pending);
  return pending;
}
