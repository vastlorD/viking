'use strict';
const test = require('node:test');
const assert = require('node:assert/strict');
const { analisar } = require('./analisar');
const evento = (ip, tipo = 'login_failed') => JSON.stringify({ ip, evento: tipo });

test('alerta no limite e não conta sucesso como falha', () => {
  const texto = [evento('192.0.2.1'), evento('192.0.2.1'), evento('192.0.2.1'),
    evento('192.0.2.2', 'login_success')].join('\n');
  assert.deepEqual(analisar(texto), { linhasValidas: 4, linhasIgnoradas: 0, limite: 3,
    alertas: [{ ip: '192.0.2.1', falhas: 3 }] });
});
test('ignora dados malformados sem interromper o relatório', () => {
  assert.equal(analisar('invalido\nnull\n{}\n' + evento('ip-incorreto')).linhasIgnoradas, 4);
});
test('aceita IPv6 e limite configurável', () => {
  assert.deepEqual(analisar(evento('2001:db8::1'), 1).alertas,
    [{ ip: '2001:db8::1', falhas: 1 }]);
});
test('entrada vazia e contagem abaixo do limite não geram alertas', () => {
  assert.deepEqual(analisar('').alertas, []);
  assert.deepEqual(analisar(evento('192.0.2.1')).alertas, []);
});
test('limites inválidos são rejeitados', () => {
  for (const limite of [0, -1, 1.5, NaN]) assert.throws(() => analisar('', limite));
});
