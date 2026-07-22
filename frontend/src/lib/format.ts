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

/**
 * A coefficient of determination, formatted so it never CLAIMS to be 1 when it is not.
 *
 * `toFixed(5)` renders 0.999999998 as "1.00000". Printed beside a verdict reading "structure not
 * recovered", that reads as a contradiction: zero error and a failure to find the law cannot both
 * be true, so a reader concludes one of the numbers is broken and stops trusting both. The real
 * finding, a near-perfect fit with the wrong structure, is exactly what the rounding erased.
 *
 * So a value inside 1e-5 of 1, without being 1, is shown as its distance FROM 1. "1 - 2e-9" is
 * unambiguous, compact, and cannot be misread as an exact fit. An R2 that genuinely is 1 still
 * prints as "1", because for an exactly recovered law that is the truth.
 */
export function formatR2(value: number | null, digits = 5): string {
  if (value === null || !Number.isFinite(value)) return 'n/a';
  if (value === 1) return '1';
  if (value > 1 - 1e-5 && value < 1) {
    const gap = 1 - value;
    return `1 - ${gap.toExponential(1)}`;
  }
  return value.toFixed(digits);
}
