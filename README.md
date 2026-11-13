# Viking

**Um laboratório de programação, automação e segurança defensiva.**

O Viking reúne projetos que fui construindo para aprender na prática. Começou com exercícios de lógica e evoluiu para ferramentas maiores, cada uma com seus próprios desafios. Este repositório não é um produto único: é um espaço de estudo, testes e evolução.

## Explore os projetos

| Projeto | Tecnologia | O que faz | Situação |
| --- | --- | --- | --- |
| [Calculadora de notas](python/notas.py) | Python | Calcula média, valida entradas e informa aprovação | Exemplo executável |
| [Calculadora de notas](node/notas.js) | Node.js | Mesma regra de negócio em JavaScript | Exemplo executável |
| [Analisador de logs](seguranca/README.md) | Node.js | Resume falhas de autenticação de arquivos JSONL | Exemplo defensivo |
| [Integrity Guard](integrity-guard/README.md) | Python | Monitora alterações de arquivos com hashes e base assinada | Ferramenta experimental |
| [Ponto Facial](ponto-facial/README.md) | Python | Protótipo de registro de presença com verificação facial individual | Requer validação em ambiente real |

## Comece pelas calculadoras

Clone o repositório:

```sh
git clone https://github.com/vastlorD/viking.git
cd viking
```

**Python**

```sh
python python/notas.py
python -m unittest discover -s python -v
```

**Node.js**

```sh
node node/cli.js
node --test node/notas.test.js
```

Digite, por exemplo, `8 7 9`. O resultado é média **8,00**, situação **Aprovado**. As notas devem estar entre 0 e 10; a aprovação começa em 7.

**Analisador de logs**

```sh
node seguranca/analisar.js seguranca/exemplo.jsonl
node --test seguranca/analisar.test.js
```

O analisador usa eventos JSONL fictícios. Alertas de falhas repetidas não comprovam a ocorrência de um ataque.

## Testes e validação

Em **13/11/2026**, foram reproduzidos localmente os arquivos das calculadoras e do analisador de logs, obtidos do GitHub, com seus testes:

- Python 3.13: **4 testes aprovados**.
- Node.js 22: **9 testes aprovados** (4 da calculadora e 5 do analisador).

**Importante:** os testes foram executados sobre cópias reconstruídas a partir dos arquivos consultados, não sobre um clone integral do repositório. Não houve reexecução dos testes do Integrity Guard nem validação de câmera, localização ou modelos reais do Ponto Facial. Veja o [registro técnico](docs/REVISAO-2026-11-13.md).

## Organização e aprendizado

- [Guia prático](GUIA_PRATICO.md): entenda e adapte as calculadoras.
- [Integrity Guard](integrity-guard/README.md): documentação e comandos de uso.
- [Segurança](seguranca/README.md): limitações e testes do analisador.
- [Ponto Facial](ponto-facial/README.md): instalação, cuidados e validação pendente.
- [Central de Projetos](https://github.com/vastlorD/central-de-projetos): catálogo e roadmap geral.

O notebook original `Untitled2.ipynb` foi preservado como parte do histórico.

## Próximos passos

Reexecutar a suíte completa em um clone do repositório, revisar dependências e manter a documentação alinhada ao código. Qualquer uso de dados biométricos, localização ou informações de terceiros exige revisão cuidadosa de privacidade e autorização.

---

*Desenvolvimento e documentação com assistência de IA. Meu objetivo aqui é aprender, melhorar e mostrar com clareza o que cada projeto realmente faz.*
