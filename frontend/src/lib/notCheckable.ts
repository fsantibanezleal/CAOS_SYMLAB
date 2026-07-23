/**
 * Spanish for the "why recovery is not checkable" reasons.
 *
 * The reason is authored in English in the pipeline (`physics_truths.py :: not_checkable_reason`) and
 * shipped in the artifact, so on a Spanish page the label was translated but the sentence stayed
 * English. There is a small, stable set of these, so they are translated here keyed on the English
 * text, with the English used as the fallback if the pipeline wording ever changes. The proper home
 * is a bilingual field in the artifact; until that is baked, this keeps the Spanish page Spanish.
 */
const ES: Record<string, string> = {
  "This case is measurement from a plant or an instrument. No published closed form exists to recover, so it contributes to the error metrics and to no recovery rate. Reporting it as zero recovery would be a false statement about the method.":
    "Este caso es una medición de planta o instrumento. No existe una forma cerrada publicada que recuperar, así que contribuye a las métricas de error y a ninguna tasa de recuperación. Reportarlo como cero recuperación sería una afirmación falsa sobre el método.",

  "This problem has a published law, but no machine-comparable expression is wired for it in this lab, so recovery is not scored. That is a gap here rather than a finding.":
    "Este problema tiene una ley publicada, pero no hay una expresión comparable por máquina conectada en este laboratorio, así que la recuperación no se puntúa. Es una brecha aquí y no un hallazgo.",

  "Snell's law in the form theta1 = arcsin(n*sin(theta2)). The operator set has no inverse-sine primitive, so the target lies outside the space the search can reach. Recovery is reported as not checkable rather than as zero, because a zero here would describe the primitive set rather than the method.":
    "La ley de Snell en la forma theta1 = arcsin(n*sin(theta2)). El conjunto de operadores no tiene un primitivo de arcoseno, así que el objetivo queda fuera del espacio que la búsqueda puede alcanzar. La recuperación se reporta como no evaluable y no como cero, porque un cero aquí describiría el conjunto de operadores y no el método.",

  "The curve is piecewise: zero below cut-in, zero above cut-out, and capped at rated power between. The operator set has no comparison, no minimum and no indicator, so the law cannot be written in the language the search uses. Reporting zero recovery would describe the primitive set rather than the method.":
    "La curva es por tramos: cero bajo la velocidad de arranque, cero sobre la de corte, y limitada a la potencia nominal entre ambas. El conjunto de operadores no tiene comparación, ni mínimo, ni indicador, así que la ley no se puede escribir en el lenguaje que usa la búsqueda. Reportar cero recuperación describiría el conjunto de operadores y no el método.",

  "%Fe = 69.94 - 0.699 %SiO2 assumes the ore is hematite and quartz only. Measured rows deviate by 6.5 percent at the median and 11.8 percent at worst, so the line is a reference to compare against and not a law to recover. An expression that fits the ore better than this line is a better description of the ore, and scoring it as a failed recovery would invert that.":
    "%Fe = 69.94 - 0.699 %SiO2 supone que la mena es solo hematita y cuarzo. Las filas medidas se desvían 6.5 por ciento en la mediana y 11.8 por ciento en el peor caso, así que la línea es una referencia para comparar y no una ley que recuperar. Una expresión que ajuste la mena mejor que esta línea es una mejor descripción, y puntuarla como recuperación fallida invertiría eso.",
};

/** The reason in the requested language: Spanish where known, else the original (English) text. */
export function notCheckableReasonText(reason: string, lang: 'en' | 'es'): string {
  if (lang !== 'es' || !reason) return reason;
  return ES[reason.trim()] ?? reason;
}
