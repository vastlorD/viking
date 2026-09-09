# Ponto Facial Viking

**[Passo a passo detalhado de instalação e uso no Windows](docs/PASSO_A_PASSO.md)** — configuração inicial, cadastro, registro de presença, relatórios e solução de dificuldades.

Sistema de estudo para registrar presença com **login, verificação facial individual, horário e localização**. Evolução de um protótipo próprio em Python, refatorado com assistência de IA para tornar as responsabilidades claras e corrigir falhas de acesso.

O colaborador informa sua identidade pelo login; a selfie é comparada apenas à foto desse cadastro (verificação 1:1). O sistema não procura pessoas em uma base aberta nem faz análise de idade, gênero ou emoções.

## Funcionalidades

- Cadastro de colaboradores por administrador, com foto de referência e horário esperado.
- Painel do colaborador com câmera e geolocalização do navegador.
- Comparação com DeepFace/VGG-Face, exigindo um rosto por imagem e teste de autenticidade na selfie.
- Registro em SQLite de data/hora UTC, latitude, longitude, distância da sede e status de chegada.
- Limite de distância configurável e bloqueio de registros repetidos em menos de 60 segundos.
- Extrato individual autenticado e consulta administrativa com exportação CSV.
- Remoção de selfies temporárias ao concluir ou falhar a verificação.

**Estado:** protótipo para demonstração e desenvolvimento. Leia [validação e limitações](docs/VALIDACAO.md). A integração com câmera, localização e modelos reais exige validação no computador de destino; os testes automatizados usam um motor facial controlado, sem fotos reais.

## Instalação no Windows

Base de execução: **Python 3.12, 64 bits**, em ambiente virtual. Os modelos de aprendizado de máquina são grandes e precisam de internet no primeiro uso.

No PowerShell, clone o repositório (ou use `git pull` se já tiver uma cópia) e entre na pasta:

```powershell
git clone https://github.com/vastlorD/viking.git
cd viking/ponto-facial
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-facial.txt -r requirements-ui.txt
Copy-Item .env.example .env
```

Edite `.env` e substitua `SEDE_LAT=0` e `SEDE_LON=0` pelas coordenadas da sua sede. O raio é medido em metros. Não envie esse arquivo ao GitHub. Os valores zero são exemplos, não são a sede real.

Crie a conta administrativa; a senha será solicitada sem aparecer na tela:

```powershell
.\.venv\Scripts\python.exe -m ponto.cli administrador --nome "Administrador"
```

Inicie a API:

```powershell
.\.venv\Scripts\python.exe -m uvicorn ponto.api:create_app --factory --host 127.0.0.1 --port 8000
```

Em um segundo terminal, na mesma pasta, abra o painel administrativo:

```powershell
.\.venv\Scripts\python.exe -m streamlit run admin.py --server.address 127.0.0.1 --server.port 8501
```

Em um terceiro terminal, abra o painel do colaborador:

```powershell
.\.venv\Scripts\python.exe -m streamlit run colaborador.py --server.address 127.0.0.1 --server.port 8502
```

| Endereço local | Uso |
| --- | --- |
| `http://localhost:8501` | Entrar como administrador, cadastrar pessoa e consultar registros |
| `http://localhost:8502` | Entrar como colaborador, autorizar localização e tirar selfie |
| `http://127.0.0.1:8000/docs` | Documentação interativa dos endpoints |

No Linux/macOS: `python3.12 -m venv .venv`, `source .venv/bin/activate`, `cp .env.example .env`; use `python` no lugar de `.\.venv\Scripts\python.exe` nos comandos seguintes.

## Demonstração prática

1. Configure a localização da sede e crie o administrador.
2. Abra o painel administrativo e cadastre uma pessoa participante do teste, com senha de pelo menos 12 caracteres e foto contendo somente seu rosto.
3. Abra o painel do colaborador, entre com essa nova conta e permita câmera e localização.
4. Tire uma selfie e registre. A API verifica senha, raio e face antes de gravar.
5. Confira o extrato e o relatório administrativo. Repita imediatamente para verificar a resposta de duplicidade.
6. Teste com coordenadas fora do raio via `/docs`: deve retornar 403 sem registrar presença.

A localização deve ter sido obtida há no máximo dois minutos no painel. Se estiver antiga, atualize a página e capture novamente. Em outro aparelho, câmera e localização normalmente exigem HTTPS; esta configuração serve apenas o computador local. Não exponha HTTP Basic com senha em uma rede sem HTTPS.

## Estrutura

| Arquivo | Responsabilidade |
| --- | --- |
| `admin.py` / `colaborador.py` | Telas Streamlit |
| `ponto/api.py` | Endpoints, autenticação e autorização |
| `ponto/ui.py` | Cliente HTTP e login compartilhados pelas telas |
| `ponto/config.py` | Configuração por ambiente |
| `ponto/auth.py` | Hash de senha com PBKDF2-SHA256 e salt individual |
| `ponto/database.py` | SQLite e consultas parametrizadas |
| `ponto/rules.py` | Distância, horário e gravação transacional |
| `ponto/images.py` | Limite, validação e normalização de imagens |
| `ponto/face.py` | Adaptador DeepFace e tratamento de falhas |
| `ponto/cli.py` | Criação explícita de administrador |
| `tests/` | Testes sem biometria real |

## API

Autenticação por HTTP Basic: use **Authorize** em `/docs`. A antiga chave compartilhada foi removida. Nome de usuário e senha não são mais campos do formulário de ponto.

| Método e rota | Permissão | Entrada |
| --- | --- | --- |
| `GET /health` | Pública | Disponibilidade da API, não valida os modelos |
| `GET /me` | Usuário autenticado | Dados básicos da conta |
| `POST /colaboradores` | Administrador | Formulário: `nome`, `usuario`, `senha`, `horario`, `tolerancia`, arquivo `foto` |
| `POST /bater-ponto` | Colaborador com foto | Formulário: `lat`, `lon`, arquivo `selfie` |
| `GET /meu-extrato` | Usuário autenticado | Registros da própria conta; `limit` opcional |
| `GET /registros` | Administrador | Registros recentes; `limit` até 1.000 |

Respostas: 201 criado, 401 credenciais inválidas, 403 acesso/face/localização recusados, 409 duplicidade ou foto ausente, 422 entrada inválida, 429 limite local de requisições, 503 motor facial indisponível.

## Testar

Os testes não exigem DeepFace, GPU, fotos de pessoas ou acesso à câmera:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements-test.txt
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

Para testar somente regras, banco, imagens e contrato do adaptador: `python -m unittest discover -s tests -p test_core.py -v` (Pillow necessário).

## Dados e migração

O banco e as duas fotos do pacote original **não estão neste repositório**. A versão usa um banco novo em `data/ponto.sqlite3`; não abre nem migra automaticamente `ponto_viking.db`. Os hashes antigos do Passlib não são importados. Refaça os cadastros de teste; preserve o banco original em local privado caso precise planejar uma migração posteriormente.

Consulte a [análise das mudanças](docs/ANALISE.md) e o [roteiro de validação](docs/VALIDACAO.md).
