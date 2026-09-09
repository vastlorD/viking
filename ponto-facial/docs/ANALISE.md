# Análise e decisões de refatoração

## Problemas encontrados no material original

| Problema | Alteração |
| --- | --- |
| Qualquer colaborador autenticado podia entrar no painel administrativo | Papéis `admin` e `employee`, conferidos na API |
| Extrato por nome de usuário sem autenticação | Extrato limitado à conta autenticada |
| Chave de API e senhas padrão no código | Removidas; administrador criado por terminal com senha própria |
| Script administrativo conferia um login e criava outro | Uma única identificação validada, sem criação duplicada |
| Caminhos de upload montados com usuário e timestamp | Identificadores aleatórios, sem nomes fornecidos pelo cliente |
| Selfies persistiam após recusa ou sucesso | Diretório temporário com remoção garantida no fluxo normal e em exceções |
| Upload sem validação do conteúdo | JPEG/PNG normalizados, até 5 MB e 16 MP; metadados removidos |
| Geolocalização e raio fixos no fonte | Configuração por ambiente e validação numérica |
| Chamada de geocodificação externa a cada batida | Coordenadas e distância locais, sem transmissão ao Nominatim |
| Horário dependia do fuso do servidor | Armazenamento UTC e cálculo usando fuso configurado |
| Repetição de batidas sem proteção | Intervalo mínimo, conferido junto da inserção em transação SQLite |
| DeepFace pesado dentro de endpoint `async` | Endpoint síncrono executado pelo FastAPI fora do event loop; acesso ao motor serializado |
| Sessões abertas e consultas por colaborador em loop | Conexões curtas e consulta com JOIN |
| Dependências vazias, scripts incompletos e arquivo de teste que alterava o banco | Listas de dependências por função e testes isolados |

## Escolhas para manter o código compreensível

- Mantido FastAPI no backend, Streamlit nas telas e DeepFace para verificação.
- SQLite acessado pela biblioteca padrão, sem ORM para este esquema de duas tabelas.
- Sem JWT, Redis ou serviços externos: HTTP Basic é adequado à demonstração local; uma implantação exige transporte HTTPS.
- CSV substitui o Excel para reduzir dependências. O painel protege campos textuais contra interpretação como fórmula.
- A selfie não é guardada no histórico. A foto de referência fica em diretório privado local para permitir novas comparações.
- O motor carrega sob demanda; não há retorno positivo de demonstração na aplicação. A substituição do motor existe apenas nos testes.
- O painel do colaborador acrescenta captura por câmera e localização, ausente dos arquivos originais enviados.

## Limites conhecidos

A comparação é probabilística: pode rejeitar a pessoa correta ou aceitar indevidamente. A opção antisspoofing é uma camada adicional, não uma prova de presença nem validação certificada. A API recebe coordenadas fornecidas pelo cliente; elas podem ser manipuladas. O painel exige leitura recente, mas isso não autentica a posição.

A regra de atraso mantém o escopo simples do protótipo: horário fixo no mesmo dia local. Não há escala noturna, entrada/saída, pausas, banco de horas ou cálculo de jornada. Cada presença recebe a mesma regra de horário. Não apresentar como sistema de folha de pagamento ou ponto homologado.

Fotos de referência e registros não são criptografados pela aplicação. Use armazenamento e backups protegidos, política de retenção e acesso restrito antes de uso com dados reais. Selfies temporárias podem permanecer se o processo ou computador for encerrado abruptamente; o diretório `data/` deve continuar privado.

O limitador permite até 20 requisições autenticadas por minuto por IP observado pela API e por processo. Com Streamlit, as requisições partem do servidor do painel: usuários podem compartilhar esse limite. Ele é básico e não substitui limitação distribuída no proxy. Limite também o corpo da requisição no proxy: a validação de 5 MB ocorre após o parser multipart receber o arquivo.

## Referências técnicas

- [FastAPI: HTTP Basic](https://fastapi.tiangolo.com/advanced/security/http-basic-auth/)
- [FastAPI: arquivos e formulários](https://fastapi.tiangolo.com/tutorial/request-forms-and-files/)
- [DeepFace: verificação e antisspoofing](https://github.com/serengil/deepface)
- [Componente de geolocalização do navegador](https://github.com/aghasemi/streamlit_js_eval)

O código foi revisado com assistência de IA a partir do projeto fornecido pelo autor. Dados privados e credenciais do original foram excluídos da publicação. Troque credenciais que tenham sido utilizadas no protótipo original antes de qualquer uso real.
