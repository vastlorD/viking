'use strict';

const fs = require('node:fs');
const { isIP } = require('node:net');

function analisar(texto, limite = 3) {
  if (!Number.isInteger(limite) || limite < 1) {
    throw new Error('O limite deve ser um inteiro positivo.');
  }
  const falhas = new Map();
  let ignoradas = 0;
  let validas = 0;
  for (const linha of texto.split(/\r?\n/)) {
    if (!linha.trim()) continue;
    let evento;
    try {
      evento = JSON.parse(linha);
    } catch {
      ignoradas++;
      continue;
    }
    if (!evento || typeof evento.ip !== 'string' || !isIP(evento.ip)
        || !['login_failed', 'login_success'].includes(evento.evento)) {
      ignoradas++;
      continue;
    }
    validas++;
    if (evento.evento === 'login_failed') {
      falhas.set(evento.ip, (falhas.get(evento.ip) || 0) + 1);
    }
  }
  const alertas = [...falhas.entries()]
    .filter(([, quantidade]) => quantidade >= limite)
    .map(([ip, quantidade]) => ({ ip, falhas: quantidade }))
    .sort((a, b) => b.falhas - a.falhas || a.ip.localeCompare(b.ip));
  return { linhasValidas: validas, linhasIgnoradas: ignoradas, limite, alertas };
}

if (require.main === module) {
  try {
    const arquivo = process.argv[2];
    if (!arquivo) throw new Error('Uso: node seguranca/analisar.js arquivo.jsonl [limite]');
    const limite = process.argv[3] === undefined ? 3 : Number(process.argv[3]);
    const texto = fs.readFileSync(arquivo, 'utf8');
    console.log(JSON.stringify(analisar(texto, limite), null, 2));
  } catch (erro) {
    console.error(erro.message);
    process.exitCode = 1;
  }
}

module.exports = { analisar };
