# Analisador local de falhas de autenticação

Exemplo de automação defensiva em Node.js, sem dependências externas. Lê um arquivo JSONL (um objeto JSON por linha), conta falhas por IP e gera um relatório JSON. O limite padrão é três falhas no arquivo inteiro.

## Executar na raiz do repositório

```sh
node seguranca/analisar.js seguranca/exemplo.jsonl
node seguranca/analisar.js seguranca/exemplo.jsonl 5
node --test seguranca/analisar.test.js
```

No primeiro comando, o IP fictício `192.0.2.10` aparece com três falhas. No segundo, nenhum IP atinge o limite de cinco. Para salvar um relatório local:

```sh
node seguranca/analisar.js seguranca/exemplo.jsonl > relatorio.json
```

## Formato de entrada

```json
{"ip":"192.0.2.10","evento":"login_failed"}
```

Eventos aceitos: `login_failed` e `login_success`. Linhas vazias são desconsideradas. JSON inválido, IP inválido e eventos desconhecidos entram em `linhasIgnoradas`. O programa conta linhas válidas e mostra os alertas em ordem decrescente de falhas. IPv4 e IPv6 são aceitos.

## Base do código

`fs.readFileSync` lê o arquivo; `JSON.parse` interpreta cada linha; `isIP` valida o endereço; `Map` guarda a contagem por IP. `filter` seleciona contagens no limite ou acima; `sort` organiza a saída. A função `analisar` é exportada para reutilização e testada sem acessar arquivos.

## Limitações

O alerta indica repetição de falhas, não comprova ataque. Não há janela de tempo, correlação por usuário, bloqueio ou monitoramento contínuo. Um login bem-sucedido não zera falhas anteriores. O arquivo inteiro é lido em memória; use arquivos pequenos. Endereços IPv6 com escritas diferentes são contados separadamente. Não é um parser direto de logs SSH ou Windows: é necessário convertê-los ao formato descrito. Não realiza conexões de rede.

## Exercícios práticos

1. Acrescente eventos fictícios e veja como o resultado muda.
2. Adicione um campo de data e conte falhas em uma janela de cinco minutos.
3. Leia arquivos grandes linha a linha.
4. Implemente um adaptador para um formato real de log e escreva testes com amostras anonimizadas.

Desenvolvido com assistência de IA como projeto de estudo em automação e cibersegurança defensiva. Validado com Node.js 24.
