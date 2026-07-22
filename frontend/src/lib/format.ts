/**
 * Number formatting that does not change meaning with the reader's regional settings.
 *
 * `toLocaleString()` with no locale argument uses the BROWSER's locale, so a Spanish-locale browser
 * reading the English page rendered 2550 rows as "2.550" and 12000 evaluations as "12.000", both of
 * which a reader parses as a decimal. A count must mean the same thing to every reader, so the
 * grouping separator is fixed here as a thin space, which no locale reads as a decimal point.
 */

const THIN_SPACE = ' ';

export function groupDigits(value: number): string {
  if (!Number.isFinite(value)) return '-';
  return value.toLocaleString('en-US').replace(/,/g, THIN_SPACE);
}
