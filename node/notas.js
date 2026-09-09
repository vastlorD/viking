'use strict';

function gerarRelatorio(notas) {
  if (!Array.isArray(notas) || notas.length === 0) {
    throw new Error('Informe pelo menos uma nota.');
  }
  for (const nota of notas) {
    if (typeof nota !== 'number' || !Number.isFinite(nota) || nota < 0 || nota > 10) {
      throw new Error('Cada nota deve ser um número entre 0 e 10.');
    }
  }
  const media = notas.reduce((soma, nota) => soma + nota, 0) / notas.length;
  return { quantidade: notas.length, media, situacao: media >= 7 ? 'Aprovado' : 'Reprovado' };
}

module.exports = { gerarRelatorio };
