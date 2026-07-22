/** Language, read from the shared shell so the toggle in the header drives every panel. */
import { useShellLang } from '@fasl-work/caos-app-shell';

export type Lang = 'en' | 'es';

export function useLang(): Lang {
  return useShellLang() as Lang;
}
