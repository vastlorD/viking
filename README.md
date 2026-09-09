# Viking — laboratório de Python e Node.js

## Cibersegurança e automação: Integrity Guard

[Integrity Guard](integrity-guard/README.md): monitor defensivo de integridade de arquivos em Python. Cria uma base assinada, detecta arquivos criados, alterados e removidos, gera relatórios JSON e pode ser executado pelo Agendador de Tarefas do Windows ou pelo cron no Linux.

## Projeto em destaque: Ponto Facial

[Ponto Facial Viking](ponto-facial/README.md): sistema Python de presença com cadastro, verificação facial individual, geolocalização, API e painéis de administrador e colaborador. Inclui análise das correções, testes e instruções para Windows. A validação dos modelos reais e da câmera no computador de destino está pendente; veja o [escopo dos testes](ponto-facial/docs/VALIDACAO.md).

## Calculadora de notas e automação

Exemplos básicos de desenvolvimento, automação e cibersegurança defensiva. Comece pela calculadora abaixo ou pelo [analisador de logs](seguranca/README.md), que identifica repetição de falhas de autenticação em um arquivo local com dados fictícios.

Projeto de estudo com a mesma regra de negócio em **Python e Node.js**. Recebe notas de 0 a 10, calcula a média e informa aprovação a partir de 7. O objetivo é praticar funções, listas, validação de entradas e testes automatizados com código pequeno.

## Executar

Clone o projeto e entre na pasta:

```sh
git clone https://github.com/vastlorD/viking.git
cd viking
```

Escolha uma implementação. Não é necessário instalar pacotes externos.

| Implementação | Executar na raiz do repositório | Rodar os testes |
| --- | --- | --- |
| Python | `python3 python/notas.py` | `python3 -m unittest discover -s python -v` |
| Node.js | `node node/cli.js` | `node --test node/notas.test.js` |

Validado com Python 3.12 e Node.js 24. No Windows, se necessário, substitua `python3` por `python` ou `py`.

Digite `8 7 9` e pressione Enter:

```text
Quantidade: 3
Média: 8.00
Situação: Aprovado
```

Notas decimais podem usar ponto ou vírgula: `6,5 7,5`. Separe as notas por espaços. Entrada vazia, texto, valores infinitos e notas fora do intervalo geram erro. A situação usa a média original; o arredondamento para duas casas serve apenas para exibição.

## Organização

| Arquivo | Responsabilidade |
| --- | --- |
| `python/notas.py` | Regra de negócio e interface de terminal em Python |
| `python/test_notas.py` | Testes Python com unittest |
| `node/notas.js` | Regra de negócio exportada como função |
| `node/cli.js` | Entrada e saída pelo terminal |
| `node/notas.test.js` | Testes com o executor nativo do Node.js |
| `GUIA_PRATICO.md` | Explicação do código, exercícios e exemplos reutilizáveis |
| `Untitled2.ipynb` | Notebook original, preservado como histórico de estudo |

As novas versões consolidam a lógica duplicada do notebook em uma função de relatório por linguagem. Não há cadastro de alunos, persistência, interface web ou integração escolar. Este é um exercício local, com regra de aprovação simplificada.

## O que os testes verificam

Média e quantidade, aprovação exatamente em 7, reprovação abaixo de 7, extremos 0 e 10 e rejeição de entradas inválidas. Para testar a interação, execute o programa e experimente uma entrada válida, `fim` (inválida nesta versão) e uma linha vazia.

## Desenvolvimento

Evolução realizada com assistência de IA. O guia descreve as decisões e oferece exercícios para estudar, adaptar e explicar o código. Funcionalidades futuras sugeridas: média ponderada, exportação CSV e cadastro de alunos.
