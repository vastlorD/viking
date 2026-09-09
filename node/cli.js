'use strict';

const readline = require('node:readline');
const { gerarRelatorio } = require('./notas');

const terminal = readline.createInterface({ input: process.stdin, output: process.stdout });
console.log('Viking — calculadora de notas');
terminal.question('Digite notas separadas por espaço (ex.: 8 7 9): ', (entrada) => {
  try {
    const texto = entrada.trim();
    const notas = texto ? texto.split(/\s+/).map(valor => Number(valor.replace(',', '.'))) : [];
    const relatorio = gerarRelatorio(notas);
    console.log(`Quantidade: ${relatorio.quantidade}`);
    console.log(`Média: ${relatorio.media.toFixed(2)}`);
    console.log(`Situação: ${relatorio.situacao}`);
  } catch (erro) {
    console.error(`Não foi possível calcular: ${erro.message}`);
    process.exitCode = 1;
  } finally {
    terminal.close();
  }
});
