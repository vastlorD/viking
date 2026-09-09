'use strict';

const test = require('node:test');
const assert = require('node:assert/strict');
const { gerarRelatorio } = require('./notas');

test('calcula média e quantidade', () => {
  assert.deepEqual(gerarRelatorio([8, 7, 9]), { quantidade: 3, media: 8, situacao: 'Aprovado' });
});
test('respeita limite de aprovação sem arredondar antes', () => {
  assert.equal(gerarRelatorio([7]).situacao, 'Aprovado');
  assert.equal(gerarRelatorio([6.999]).situacao, 'Reprovado');
});
test('aceita extremos válidos', () => {
  assert.equal(gerarRelatorio([0, 10]).media, 5);
});
test('rejeita entradas inválidas', () => {
  for (const notas of [[], [-1], [11], [NaN], [Infinity], [true], ['8'], null]) {
    assert.throws(() => gerarRelatorio(notas));
  }
});
