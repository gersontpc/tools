# Análise do processo de release do Bottlerocket na AWS

## TL;DR

Esta análise evidencia um possível problema no processo de release do Bottlerocket: AMIs oficiais podem aparecer no console da AWS antes de release pública, documentação e sinalização operacional estarem plenamente alinhadas.

No caso analisado, a versão `v1.58.0` do Bottlerocket foi observada como AMI oficial publicada na AWS em `2026-04-01`, enquanto a release pública apareceu posteriormente marcada como `Pre-release`, com rollout interrompido por regressão. A documentação `1.58.x` foi adicionada ao site apenas em `2026-05-01`.

A recomendação é que a AWS sincronize AMIs, release estável, documentação, alertas operacionais e validações antes da exposição ampla dessas imagens no console e no AMI Catalog.

---

## Objetivo

O objetivo deste repositório é demonstrar, com evidências coletadas no console da AWS, na AWS CLI, no repositório oficial do Bottlerocket e no site de documentação, que houve desalinhamento entre:

- publicação de AMIs oficiais;
- estado da release upstream;
- disponibilidade da documentação oficial;
- comunicação de risco operacional.

A versão `v1.58.0` é usada como estudo de caso porque possui evidências coletadas e reproduzíveis neste repositório.

Com isso, busca-se solicitar à AWS uma revisão do processo de lançamento do Bottlerocket, incluindo critérios mais claros de promoção de AMIs, testes antes da exposição aos usuários, sinalização explícita de versões em `pre-release` ou rollout parcial e publicação sincronizada da documentação necessária para operação segura em ambientes produtivos.

---

## Escopo da evidência

A `v1.58.0` é o caso documentado neste repositório porque há prints, saída de AWS CLI, release upstream e commit de documentação que permitem montar uma linha do tempo com evidência verificável.

No entanto, a preocupação apresentada não se limita a essa versão específica. O ponto central é o processo de publicação de versões do Bottlerocket como um todo.

Quando uma versão aparece no console da AWS antes de estar alinhada com release pública, documentação oficial e sinalização de estabilidade, o risco operacional existe independentemente do número da versão.

Por isso, a `v1.58.0` deve ser tratada como exemplo concreto de um padrão que precisa ser prevenido em releases futuras e investigado em versões anteriores que possam ter apresentado comportamento semelhante.

---

## Estrutura do repositório

    .
    ├── README.md
    └── analysis
        ├── data
        │   ├── data.txt
        │   ├── bottlerocket-1.58.0.json
        │   └── bottlerocket-1.58.0.tsv
        ├── img
        │   ├── bottlerocket-1.58.0.png
        │   ├── bottlerocket-aws-1.58.0.png
        │   ├── bottlerocket-release-v1.58.0.png
        │   ├── bottlerocket-website.png
        │   └── bottlerocket-website-1.58.0.png
        └── scripts
            ├── filter_bottlerocket_amis.sh
            └── filter_bottlerocket_amis.py

Descrição dos diretórios:

| Caminho | Descrição |
| --- | --- |
| `analysis/scripts/` | Scripts usados para coletar AMIs Bottlerocket publicadas pela AWS. |
| `analysis/data/` | Saídas brutas das coletas, em texto, JSON ou TSV. |
| `analysis/img/` | Prints usados como evidência visual. |
| `README.md` | Consolidação da análise, linha do tempo, impacto e recomendações. |

---

## Linha do tempo observada

| Data | Evidência | Observação |
| --- | --- | --- |
| `2026-04-01` | AMIs `v1.58.0` publicadas na AWS | Dados em `analysis/data/data.txt` e print do AMI Catalog indicam AMIs oficiais com `OwnerAlias: amazon` e `Publish date: 2026-04-01`. |
| `2026-04-07` | Release `v1.58.0` no GitHub | Print da release mostra `v1.58.0` como `Pre-release` em `Apr 7`. A página pública do GitHub também mostra `Pre-release` e data de publicação em `08 Apr 01:25` UTC. |
| Após a publicação da AMI | Rollout interrompido | A release informa que o rollout da `v1.58.0` foi interrompido por regressão em pull de imagens de container e recomenda `v1.59.0`. |
| `2026-05-01` | Documentação `1.58.x` adicionada ao site | Commit `3cdac2f2` adiciona a documentação `1.58.x` e marca a versão como current. |

---

## Evidências

### 1. AMIs `v1.58.0` disponíveis na AWS em `2026-04-01`

O script `analysis/scripts/filter_bottlerocket_amis.sh` consulta AMIs com `--owners amazon` e filtra pelo padrão:

    bottlerocket-aws-k8s-*-*-v1.58.0-*

O resultado salvo em `analysis/data/data.txt` mostra:

- `17` regiões consultadas;
- `48` AMIs encontradas por região;
- `816` AMIs no total;
- todas as entradas visíveis foram criadas em `2026-04-01T...Z`;
- o sufixo da AMI corresponde ao commit/tag `c5c37032`, o mesmo hash curto mostrado na release `v1.58.0`.

Exemplo em `sa-east-1`:

    bottlerocket-aws-k8s-1.35-fips-x86_64-v1.58.0-c5c37032  2026-04-01T22:59:03.000Z

Print da consulta via AWS CLI:

![Consulta via AWS CLI retornando AMIs Bottlerocket v1.58.0 em sa-east-1](analysis/img/bottlerocket-1.58.0.png)

O AMI Catalog do console da AWS também mostra uma AMI oficial `v1.58.0`, com:

- `OwnerAlias: amazon`;
- `Verified provider`;
- `Publish date: 2026-04-01`.

![AMI Bottlerocket v1.58.0 publicada no AMI Catalog da AWS](analysis/img/bottlerocket-aws-1.58.0.png)

---

### 2. Release pública marcada como pre-release e com rollout interrompido

A release oficial `v1.58.0` aparece como `Pre-release`.

O print coletado mostra:

- data `Apr 7`;
- tag `v1.58.0`;
- commit `c5c3703`;
- aviso de regressão;
- recomendação de uso da `v1.59.0`.

O mesmo print registra que o rollout da `v1.58.0` foi interrompido porque a versão introduziu uma regressão que causa falhas no pull de certas imagens de container.

![Release v1.58.0 marcada como pre-release e com aviso de regressão](analysis/img/bottlerocket-release-v1.58.0.png)

Essa evidência é crítica porque a AMI já estava disponível no console antes da release pública estar sinalizada como pronta para uso amplo.

---

### 3. Documentação `1.58.x` publicada depois da disponibilização das AMIs

O print do site do Bottlerocket mostra a documentação navegando em `1.57.x`; a versão `1.58.x` ainda não aparece na lista lateral naquele momento.

![Site do Bottlerocket ainda sem documentação 1.58.x disponível](analysis/img/bottlerocket-website.png)

O commit `3cdac2f2` no repositório do site do Bottlerocket atualiza a documentação para `1.58.0`, adiciona a árvore:

    content/en/os/1.58.x/

E altera:

    data/versions/current.toml

De:

    1.57

Para:

    1.58

O patch desse commit inclui:

- `125` arquivos alterados;
- `5.850` linhas adicionadas;
- documentação de API;
- settings;
- bootstrap;
- variantes;
- pacotes;
- informações de versão.

![Commit que adiciona a documentação 1.58.x ao site do Bottlerocket](analysis/img/bottlerocket-website-1.58.0.png)

---

## Como reproduzir a coleta

### Pré-requisitos

É necessário ter:

- Python 3.9 ou superior;
- credenciais AWS configuradas;
- permissão para executar `ec2:DescribeRegions`;
- permissão para executar `ec2:DescribeImages`;
- pacote `boto3`.

Instalação da dependência:

    pip install boto3

Ou usando `requirements.txt`:

    pip install -r requirements.txt

Conteúdo sugerido para `requirements.txt`:

    boto3>=1.34.0
    botocore>=1.34.0

---

## Uso do script Python

O script recomendado é:

    analysis/scripts/filter_bottlerocket_amis.py

Ele consulta AMIs oficiais do Bottlerocket usando:

    Owners=["amazon"]

E filtra pelo padrão de nome:

    bottlerocket-aws-k8s-{k8s_version}-*-v{bottlerocket_version}-*

Quando uma versão não é informada, ela é tratada como wildcard `*`.

---

### Buscar AMIs de uma versão específica do Bottlerocket

    python3 analysis/scripts/filter_bottlerocket_amis.py \
      --bottlerocket-version 1.58.0

Forma curta:

    python3 analysis/scripts/filter_bottlerocket_amis.py \
      -b 1.58.0

---

### Buscar AMIs por versão do Bottlerocket e Kubernetes

    python3 analysis/scripts/filter_bottlerocket_amis.py \
      --bottlerocket-version 1.58.0 \
      --k8s-version 1.35

Forma curta:

    python3 analysis/scripts/filter_bottlerocket_amis.py \
      -b 1.58.0 \
      -k 1.35

---

### Limitar a busca a regiões específicas

    python3 analysis/scripts/filter_bottlerocket_amis.py \
      --bottlerocket-version 1.58.0 \
      --regions sa-east-1,us-east-1

Forma curta:

    python3 analysis/scripts/filter_bottlerocket_amis.py \
      -b 1.58.0 \
      -r sa-east-1,us-east-1

---

### Buscar uma combinação específica

Exemplo: Bottlerocket `1.58.0`, Kubernetes `1.35`, somente em `sa-east-1` e `us-east-1`:

    python3 analysis/scripts/filter_bottlerocket_amis.py \
      --bottlerocket-version 1.58.0 \
      --k8s-version 1.35 \
      --regions sa-east-1,us-east-1

---

## Formatos de saída

O script suporta os seguintes formatos:

| Formato | Uso |
| --- | --- |
| `table` | Saída legível no terminal. Padrão. |
| `json` | Saída estruturada para evidência bruta. |
| `csv` | Saída para planilhas. |
| `tsv` | Saída compatível com análise textual e terminal. |

---

### Saída em tabela

    python3 analysis/scripts/filter_bottlerocket_amis.py \
      --bottlerocket-version 1.58.0 \
      --output-format table

---

### Saída em JSON

    python3 analysis/scripts/filter_bottlerocket_amis.py \
      --bottlerocket-version 1.58.0 \
      --output-format json

Salvar em arquivo:

    python3 analysis/scripts/filter_bottlerocket_amis.py \
      --bottlerocket-version 1.58.0 \
      --output-format json \
      --output-file analysis/data/bottlerocket-1.58.0.json

---

### Saída em TSV

    python3 analysis/scripts/filter_bottlerocket_amis.py \
      --bottlerocket-version 1.58.0 \
      --output-format tsv \
      --output-file analysis/data/bottlerocket-1.58.0.tsv

---

### Saída em CSV

    python3 analysis/scripts/filter_bottlerocket_amis.py \
      --bottlerocket-version 1.58.0 \
      --output-format csv \
      --output-file analysis/data/bottlerocket-1.58.0.csv

---

## Exemplo de resultado esperado

Exemplo simplificado:

    K8S_Version  Bottlerocket_Version  Region     AMI_ID                 Arch    Variant  Name                                                        CreationDate
    -----------  --------------------  ---------  ---------------------  ------  -------  ----------------------------------------------------------  ------------------------
    1.35         1.58.0                sa-east-1  ami-xxxxxxxxxxxxxxxxx  x86_64  fips     bottlerocket-aws-k8s-1.35-fips-x86_64-v1.58.0-c5c37032     2026-04-01T22:59:03.000Z

Resumo esperado no `stderr`:

    Resumo:
      Padrão consultado: bottlerocket-aws-k8s-*-*-v1.58.0-*
      Regiões consultadas: 17
      Total de AMIs: 816
      AMIs por região:
        - sa-east-1: 48
        - us-east-1: 48
        - ...

---

## Uso do script shell original

O repositório também pode manter o script shell original:

    analysis/scripts/filter_bottlerocket_amis.sh

Exemplo:

    chmod +x analysis/scripts/filter_bottlerocket_amis.sh

    analysis/scripts/filter_bottlerocket_amis.sh 1.58.0 "" ""

Buscar Bottlerocket `1.58.0`, Kubernetes `1.35`, em regiões específicas:

    analysis/scripts/filter_bottlerocket_amis.sh 1.58.0 1.35 sa-east-1,us-east-1

O script shell usa:

- `aws ec2 describe-regions`;
- `aws ec2 describe-images`;
- `jq`;
- `column`.

Dependências do shell script:

    aws --version
    jq --version

---

## Comparação entre os scripts

| Item | Shell script | Python script |
| --- | --- | --- |
| AWS CLI | Necessário | Não necessário |
| `jq` | Necessário | Não necessário |
| `column` | Necessário | Não necessário |
| `boto3` | Não necessário | Necessário |
| JSON nativo | Parcial | Sim |
| CSV/TSV | Manual | Sim |
| Melhor para automação | Médio | Alto |
| Melhor para evidência estruturada | Médio | Alto |

O script Python é recomendado para coletas reproduzíveis e anexação de evidências brutas em JSON/CSV/TSV.

---

## Campos coletados

O script Python coleta os seguintes campos:

| Campo | Descrição |
| --- | --- |
| `K8S_Version` | Versão Kubernetes extraída do nome da AMI. |
| `Bottlerocket_Version` | Versão Bottlerocket extraída do nome da AMI. |
| `Region` | Região AWS consultada. |
| `AMI_ID` | ID da AMI. |
| `Arch` | Arquitetura da AMI, como `x86_64` ou `arm64`. |
| `Variant` | Variante da AMI, como `fips`, `nvidia`, etc. |
| `Name` | Nome completo da AMI. |
| `CreationDate` | Data de criação/publicação da imagem. |
| `OwnerId` | ID da conta proprietária da AMI. |
| `Public` | Indica se a AMI é pública. |

---

## Validação da evidência

Para fortalecer a análise, recomenda-se validar os seguintes pontos:

1. Confirmar que as AMIs foram retornadas com `Owners=["amazon"]`.
2. Confirmar que o nome das AMIs contém `v1.58.0`.
3. Confirmar que o `CreationDate` das AMIs é `2026-04-01T...Z`.
4. Confirmar que o AMI Catalog mostra `OwnerAlias: amazon`.
5. Confirmar que o console mostra `Verified provider`.
6. Comparar o sufixo da AMI com o commit/tag exibido na release.
7. Confirmar que a release pública estava marcada como `Pre-release`.
8. Confirmar que a própria release indica interrupção de rollout.
9. Confirmar que a documentação `1.58.x` foi adicionada posteriormente.
10. Confirmar a data do commit que adicionou a documentação ao site.

---

## Impacto operacional

Quando uma AMI nova aparece no console da AWS como imagem oficial, usuários tendem a interpretá-la como pronta para uso.

No caso evidenciado pela `v1.58.0`, essa interpretação pode ser perigosa porque:

- a AMI `v1.58.0` estava publicada antes da release pública aparecer de forma clara como estável;
- a release foi marcada como `Pre-release`;
- houve regressão reconhecida na própria release;
- o rollout foi interrompido;
- a documentação `1.58.x` ainda não estava disponível no site no momento inicial;
- usuários poderiam precisar consultar diretamente o código fonte para descobrir parâmetros, mudanças de bootstrap ou settings;
- alterações de runtime, variantes, bootstrap, pacotes e configurações podem afetar diretamente clusters Kubernetes e cargas produtivas.

Esse tipo de desalinhamento cria uma janela em que a AWS disponibiliza uma imagem consumível no console, mas o usuário ainda não tem sinais suficientes de maturidade, risco e documentação operacional para adotá-la com segurança.

---

## Risco para ambientes produtivos

O risco não está apenas na existência de uma regressão específica da `v1.58.0`.

O ponto central é a combinação de três fatores:

1. AMI oficial disponível para seleção no console.
2. Release upstream ainda em estado de `Pre-release`, rollout parcial ou rollout interrompido.
3. Documentação operacional publicada depois da AMI.

Em ambientes produtivos, isso pode resultar em:

- substituição de nodes por uma versão afetada;
- falhas de workloads por erro no pull de imagens de container;
- dificuldade de rollback;
- dificuldade de troubleshooting;
- dificuldade de validação prévia;
- falta de documentação da versão em uso;
- necessidade de consultar código fonte para identificar parâmetros de bootstrap e settings;
- exposição de usuários a uma versão que ainda não deveria ser promovida como opção segura no console.

---

## Recomendações para a AWS

Solicita-se que a AWS revise o fluxo de publicação de AMIs Bottlerocket para reduzir risco de adoção prematura.

Recomendações:

- Não expor AMIs novas no console/AMI Catalog antes da release pública estar estável e documentada.
- Separar claramente AMIs de `pre-release`, rollout parcial ou validação interna de AMIs recomendadas para produção.
- Adicionar gating de release que valide a existência da documentação correspondente antes da promoção da AMI.
- Exibir no console avisos de risco quando uma versão estiver em `pre-release`, rollout parcial, rollback ou com regressão conhecida.
- Aumentar a cobertura de testes antes da promoção global.
- Testar explicitamente pull de imagens de container.
- Testar variantes Kubernetes.
- Testar variantes NVIDIA.
- Testar variantes FIPS.
- Testar cenários de bootstrap.
- Publicar notas operacionais junto com a AMI.
- Publicar parâmetros de bootstrap/settings junto com a AMI.
- Adotar período de canary/regional rollout com critérios objetivos de promoção.
- Garantir que recomendações de versão no console, no repositório e no site do Bottlerocket estejam sincronizadas.

---

## Conclusão

Com base nos dados coletados, a `v1.58.0` foi publicada como AMI oficial na AWS em `2026-04-01`.

Posteriormente, apareceu como release pública marcada como `Pre-release`, com rollout interrompido por regressão. A documentação `1.58.x` foi adicionada ao site apenas em `2026-05-01`.

Esse caso é uma evidência concreta do problema, mas não deve ser interpretado como ocorrência isolada.

O fluxo observado cria uma janela de risco para usuários que confiam no console da AWS como fonte de verdade para escolher imagens oficiais.

A recomendação é que a AWS trate a promoção de AMIs Bottlerocket como parte de um processo atômico para todas as versões:

- release estável;
- AMI publicada;
- documentação disponível;
- notas operacionais publicadas;
- alertas de regressão disponíveis;
- sinalização clara de rollout;
- exposição ampla somente após validação.

---

## Fontes e artefatos

- Release oficial Bottlerocket `v1.58.0`:  
  <https://github.com/bottlerocket-os/bottlerocket/releases/tag/v1.58.0>

- Commit de documentação `1.58.x` no site:  
  <https://github.com/bottlerocket-os/bottlerocket-project-website/commit/3cdac2f2ad88c89a74a1ca6f112ddf614dc157e8>

- Script de coleta via shell:  
  `analysis/scripts/filter_bottlerocket_amis.sh`

- Script de coleta via Python:  
  `analysis/scripts/filter_bottlerocket_amis.py`

- Resultado da coleta:  
  `analysis/data/data.txt`

- Resultado estruturado JSON:  
  `analysis/data/bottlerocket-1.58.0.json`

- Resultado estruturado TSV:  
  `analysis/data/bottlerocket-1.58.0.tsv`

- Prints de evidência:  
  `analysis/img/`

- Documentação AWS para localizar AMIs:  
  <https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/finding-an-ami.html>

---

## Observação

Esta análise não afirma que todas as AMIs Bottlerocket estejam incorretas ou inseguras. O ponto apresentado é de processo, comunicação e sincronização entre publicação de AMI, estado da release, documentação e sinalização de risco operacional.

A existência de uma AMI oficial no console pode ser interpretada por usuários como recomendação implícita de uso. Por isso, recomenda-se que versões em validação, rollout parcial, rollback, pre-release ou com regressão conhecida tenham sinalização explícita antes de ficarem amplamente visíveis para seleção.

