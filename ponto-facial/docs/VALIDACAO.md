# Validação e roteiro de execução

## Verificado localmente

19 testes de regras, banco, imagens e contrato do adaptador passaram em Python 3.12. Eles cobrem senha, entradas inválidas, fuso horário, SQL parametrizado, duplicidade concorrente, limpeza/normalização de imagens e respostas simuladas do motor facial.

## Testes de integração

`tests/test_api.py` acrescenta 16 cenários HTTP: acesso administrativo, isolamento do extrato, cadastro, fotos inválidas, geofence, motor indisponível, duplicidade e limite de requisições. Requer `requirements-test.txt`. O ambiente local de edição não permitiu baixar as dependências HTTP; consulte a execução de CI do commit para o resultado desses testes.

## Validação manual necessária

Não foram executados o modelo real DeepFace/TensorFlow, o classificador de autenticidade nem a captura real em câmera/GPS. As fotos do pacote original não foram usadas para medir reconhecimento. Os testes de adaptador usam respostas simuladas e não demonstram acurácia biométrica.

No computador de destino:

1. Instale as dependências faciais e das telas em ambiente virtual Python 3.12.
2. Cadastre uma pessoa participante do teste e confirme o download inicial dos modelos.
3. Registre usando a mesma pessoa, com boa iluminação e localização dentro do raio.
4. Repita com imagem sem rosto, múltiplos rostos, pessoa diferente e tentativa com foto de uma tela. Esses ensaios são necessários para avaliar os modelos no seu ambiente.
5. Recuse permissão de localização e câmera; a interface deve impedir a solicitação incompleta.
6. Verifique a ausência de `data/ponto-*/selfie.jpg` após sucesso, recusa e falha.
7. Confira data UTC no registro e status calculado no fuso configurado.

Se o motor não puder carregar ou executar, a API deve responder 503 e não gravar ponto. Não desative detecção ou antisspoofing para contornar incompatibilidades: verifique o erro no terminal e as versões instaladas.

As dependências usam faixas de versão; uma instalação facial completa ainda precisa ser validada no sistema operacional de destino. Depois de validar, gere um arquivo de versões com `python -m pip freeze > requirements-lock.txt` para reproduzir esse ambiente.
