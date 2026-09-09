# Passo a passo de uso — Ponto Facial Viking

Guia para instalar, iniciar e demonstrar o sistema no Windows. Na demonstração, você faz primeiro o papel de administrador, para cadastrar uma pessoa, e depois o de colaborador, para registrar a presença.

**Já instalou e configurou? Comece no passo 5.** Não é necessário reinstalar dependências nem recriar usuários a cada utilização.

## 1. Preparar o computador

Tenha Python **3.12 de 64 bits**, Git, câmera e navegador com permissão de localização. A primeira instalação e o download inicial dos modelos faciais precisam de internet.

Abra o PowerShell e confira:

~~~powershell
py -3.12 --version
git --version
~~~

Os comandos devem mostrar as versões instaladas. Se algum não for reconhecido, conclua a instalação correspondente antes de continuar.

## 2. Baixar e preparar o projeto

Execute um comando por vez:

~~~powershell
git clone https://github.com/vastlorD/viking.git
cd viking/ponto-facial
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-facial.txt -r requirements-ui.txt
~~~

Aguarde a conclusão da instalação. As bibliotecas faciais podem levar alguns minutos.

Se você já tem uma cópia, entre na pasta existente e use `git pull` para atualizá-la, preservando suas alterações locais. Não clone novamente sobre uma instalação existente.

## 3. Configurar a localização permitida

Dentro da pasta `ponto-facial`, crie o arquivo de configuração **somente se ele ainda não existir**:

~~~powershell
if (-not (Test-Path .env)) { Copy-Item .env.example .env }
notepad .env
~~~

Substitua estes valores pelas coordenadas do local da demonstração:

~~~text
SEDE_LAT=0
SEDE_LON=0
RAIO_METROS=100
~~~

| Campo | Significado |
| --- | --- |
| SEDE_LAT | Latitude da sede |
| SEDE_LON | Longitude da sede |
| RAIO_METROS | Distância máxima permitida, em metros |

**Não mantenha os zeros do exemplo.** Use ponto decimal e preserve o sinal negativo quando houver. Salve e feche o arquivo. As coordenadas recebidas do navegador serão comparadas com essa sede.

Mantenha o arquivo `.env` fora do GitHub. Se alterar a configuração enquanto o sistema estiver ligado, reinicie o serviço principal.

## 4. Criar o administrador

Faça esta etapa somente uma vez para cada nova conta administrativa:

~~~powershell
.\.venv\Scripts\python.exe -m ponto.cli administrador --nome "Administrador"
~~~

Digite uma senha com **12 a 128 caracteres** e confirme. A senha não aparece enquanto você digita; isso é esperado. Guarde-a para entrar no painel.

Se o usuário já existir, o comando não altera a senha. Use a conta criada anteriormente.

## 5. Ligar os três serviços

Abra **três janelas do PowerShell dentro da pasta ponto-facial**.

Para abrir uma janela nessa pasta, localize-a no Explorador de Arquivos, digite `powershell` na barra de endereço e pressione Enter. Repita para abrir as demais.

### Janela 1 — serviço principal (API)

~~~powershell
.\.venv\Scripts\python.exe -m uvicorn ponto.api:create_app --factory --host 127.0.0.1 --port 8000
~~~

### Janela 2 — painel administrativo

~~~powershell
.\.venv\Scripts\python.exe -m streamlit run admin.py --server.address 127.0.0.1 --server.port 8501
~~~

### Janela 3 — painel do colaborador

~~~powershell
.\.venv\Scripts\python.exe -m streamlit run colaborador.py --server.address 127.0.0.1 --server.port 8502
~~~

**Mantenha as três janelas abertas durante o uso.** A primeira atende às solicitações e as outras duas servem as telas.

| Endereço no navegador do mesmo computador | Finalidade |
| --- | --- |
| [localhost:8501](http://localhost:8501) | Painel administrativo |
| [localhost:8502](http://localhost:8502) | Painel do colaborador |
| [127.0.0.1:8000/docs](http://127.0.0.1:8000/docs) | Documentação interativa da API |

Esses links locais funcionam depois de iniciar os serviços; não são demonstrações hospedadas no GitHub.

## 6. Cadastrar a pessoa da demonstração

Abra o painel administrativo e entre com o usuário **administrador** e a senha criada no passo 4.

Escolha **Cadastrar colaborador** e preencha:

| Campo | Exemplo para demonstração |
| --- | --- |
| Nome completo | Nome da pessoa participante |
| Usuário | colaborador_teste |
| Senha inicial | Uma senha própria com pelo menos 12 caracteres |
| Foto | Foto nítida contendo somente o rosto da pessoa cadastrada |
| Horário de entrada | Horário previsto para a demonstração |
| Tolerância | 10 minutos |

Clique em **Cadastrar** e aguarde a confirmação. No primeiro uso, o motor facial pode precisar baixar modelos. O cadastro exige uma foto com um único rosto detectável.

O colaborador deve ter uma conta própria: o administrador sem foto não registra presença.

## 7. Registrar a presença

Abra o painel do colaborador:

1. Entre com **colaborador_teste** e a senha desse cadastro.
2. Permita o acesso à localização quando o navegador solicitar.
3. Permita o acesso à câmera.
4. Tire uma selfie com boa iluminação e apenas seu rosto visível.
5. Clique em **Registrar ponto**.
6. Aguarde a confirmação antes de fechar a página.

A API confere credenciais, distância da sede e correspondência facial antes de gravar. A selfie é comparada à foto do usuário autenticado.

Se aparecer uma mensagem de localização antiga, atualize a página, aguarde uma nova leitura e tire outra selfie. O painel exige uma leitura obtida há no máximo dois minutos.

## 8. Conferir e exportar o resultado

No painel do colaborador, clique em **Consultar meu extrato**.

No painel administrativo, escolha **Registros** e confira:

- Pessoa registrada.
- Data e hora.
- Latitude e longitude.
- Distância da sede.
- Status de chegada.

Clique em **Baixar CSV** para exportar os registros exibidos.

**Os horários do registro estão em UTC.** Por exemplo, com São Paulo em UTC−3, 12h UTC correspondem a 9h locais. O cálculo do atraso usa o fuso configurado em `TIMEZONE`.

## 9. Demonstrar os controles

| Teste | Resultado esperado |
| --- | --- |
| Registrar novamente antes de 60 segundos | Bloqueio de duplicidade |
| Entrar com senha incorreta | Acesso negado |
| Usar conta de colaborador no painel administrativo | Acesso negado |
| Não fornecer localização ou selfie | Solicitação incompleta bloqueada |
| Selfie recusada pelo motor facial | Nenhum ponto gravado |
| Localização fora do raio | Nenhum ponto gravado |

Para testar o raio diretamente na API: abra **/docs**, clique em **Authorize**, use a conta do colaborador, expanda **POST /bater-ponto** e selecione **Try it out**. Informe coordenadas válidas distantes da sede, anexe a selfie e clique em **Execute**. O resultado esperado é HTTP 403.

A interpretação das imagens depende do modelo; uma demonstração bem-sucedida não é uma medição de precisão biométrica.

## 10. Encerrar e voltar a usar

Pressione **Ctrl+C** em cada uma das três janelas do PowerShell para encerrar.

Na próxima utilização:

1. Abra os três terminais na pasta do projeto.
2. Execute os comandos do passo 5.
3. Abra os painéis no navegador e entre com as contas já cadastradas.

Não recrie o ambiente virtual, o administrador ou os colaboradores. Os dados ficam em `data/ponto.sqlite3` e as fotos de referência em `data/references/`. Não apague a pasta `data/` para reiniciar o aplicativo.

## Dificuldades frequentes

| Situação | O que conferir |
| --- | --- |
| Comando não encontra o Python da pasta .venv | Verifique se o terminal está dentro de ponto-facial e se o passo 2 foi concluído |
| API indisponível | Verifique a primeira janela do PowerShell e a porta 8000 |
| Porta já está em uso | Confira se o serviço já está aberto em outra janela |
| Usuário já existe | Use a conta anterior; o comando de criação não redefine senhas |
| Câmera ou localização bloqueadas | Confira as permissões do navegador para localhost e atualize a página |
| Fora do raio permitido | Confira coordenadas da sede, sinal negativo e precisão da localização recebida |
| Motor facial indisponível | Confira o erro no terminal, dependências e download dos modelos; não desative a detecção para contornar o erro |
| Muitas tentativas | Aguarde um minuto; o limitador local pode ser compartilhado pelos usuários do painel |
| Mensagem de duplicidade | Aguarde o intervalo mínimo de 60 segundos |
| Acesso pelo celular não funciona | Esta configuração atende somente o computador local; outro aparelho exige configuração adicional e HTTPS |

## Escopo da demonstração

O responsável pelo projeto relatou que concluiu o procedimento com sucesso no próprio computador. Isso complementa os testes automatizados, sem substituir a avaliação de precisão facial em diferentes condições.

O sistema continua sendo um protótipo de presença: não calcula jornada completa, pausas ou banco de horas. A localização é informada pelo cliente, e o reconhecimento facial é probabilístico. Veja [validação](VALIDACAO.md) e [análise técnica](ANALISE.md) para os limites conhecidos.

[Voltar ao README](../README.md)
