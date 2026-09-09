# Guia prático — Python e Node.js

## Como funciona

1. O terminal recebe uma linha de notas separadas por espaços.
2. O programa troca vírgula decimal por ponto e converte cada valor em número.
3. A função de relatório exige pelo menos uma nota e valida o intervalo de 0 a 10.
4. Soma as notas e divide pela quantidade.
5. Devolve quantidade, média e situação; o terminal apresenta o resultado.

Separar cálculo e apresentação permite reutilizar a função em outro programa sem abrir perguntas no terminal. As funções de relatório não gravam arquivos nem fazem chamadas de rede.

## Reutilizar em Python

Na pasta `python`, abra `python3` e execute:

```python
from notas import gerar_relatorio

resultado = gerar_relatorio([6, 8, 10])
print(resultado["media"])     # 8.0
print(resultado["situacao"])  # Aprovado
```

`sum` soma a lista; `len` conta seus itens; o dicionário agrupa a resposta. `raise ValueError` informa uma entrada incorreta. O bloco `if __name__ == "__main__"` abre o terminal apenas quando o arquivo é executado diretamente.

## Reutilizar em Node.js

Na pasta `node`, abra `node` e execute:

```javascript
const { gerarRelatorio } = require('./notas');
const resultado = gerarRelatorio([6, 8, 10]);
console.log(resultado.media);    // 8
console.log(resultado.situacao); // Aprovado
```

`reduce` acumula a soma; `length` conta os elementos; o objeto agrupa a resposta. `throw new Error` sinaliza erro e `try/catch` permite apresentá-lo ao usuário. `module.exports` permite importar a função em outro arquivo.

## Exercícios

1. Execute com `0 10`, `7`, `6.9`, `11` e uma linha vazia. Explique cada resultado.
2. Adicione maior e menor nota ao relatório e inclua testes.
3. Receba o limite de aprovação como parâmetro, mantendo 7 como padrão.
4. Implemente média ponderada com listas de notas e pesos. Valide pesos positivos e quantidades iguais.

## Como apresentar o trabalho

Explique o problema, mostre uma execução, localize a função de cálculo e rode os testes. Discuta por que a lista vazia é recusada e por que arredondar antes de decidir aprovação pode mudar o resultado. Apresente como projeto de estudo e descreva quais partes você implementou ou adaptou, incluindo a assistência de IA.
