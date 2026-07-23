/**
 * Make a variable DISPLAY name safe to drop into a KaTeX string.
 *
 * Display names come from two worlds. Generator and physics cases author real LaTeX symbols
 * (`\theta`, `\mathrm{NO}_x`, `P_e`). Real-data loaders hand back the source column names verbatim,
 * and those are NOT LaTeX: the flotation target is `%_Silica_Concentrate`, and a leading `%` is a
 * LaTeX COMMENT that eats the rest of the line, so the whole equation `target = expression` rendered
 * blank and the app fell back to showing raw source. `#`, `&`, `$`, `_`, `{`, `}` are specials too.
 *
 * The rule keeps the authored symbols untouched and only rewrites a raw identifier:
 *   - contains a backslash  -> already LaTeX, pass through (`\mathrm{NO}_x`, `\theta`)
 *   - a plain identifier with at most one `_subscript` -> renders fine as-is (`P_e`, `T_amb`, `mu`)
 *   - anything else -> escape every special and set it upright in `\mathrm{...}`
 *     (`%_Silica_Concentrate` -> `\mathrm{\%\_Silica\_Concentrate}`)
 */
export function latexSafeName(name: string): string {
  if (name.includes('\\')) return name;
  if (/^[A-Za-z][A-Za-z0-9]*(_[A-Za-z0-9]+)?$/.test(name)) return name;
  const escaped = name
    .replace(/([%#&$_{}])/g, '\\$1')
    .replace(/~/g, '\\textasciitilde{}')
    .replace(/\^/g, '\\textasciicircum{}');
  return `\\mathrm{${escaped}}`;
}
