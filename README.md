## Análise do processo de release do Bottlerocket na AWS

### TL;DR

Esta análise evidencia um problema no processo de release do Bottlerocket: AMIs podem aparecer no console da AWS antes de release pública, documentação e sinalização operacional estarem alinhadas, levando usuários a adotarem versões prematuramente em produção; a recomendação é que a AWS sincronize AMIs, release estável, documentação, alertas e validações antes da exposição ampla.

### Objetivo

O objetivo desta análise é demonstrar, com evidências coletadas no console da AWS, na AWS CLI, no repositório oficial do Bottlerocket e no site de documentação, que houve desalinhamento entre a publicação das AMIs, o estado da release upstream e a disponibilidade da documentação oficial. A versão `v1.58.0` é usada como estudo de caso porque possui evidências coletadas e reproduzíveis neste repositório.

Com isso, busca-se solicitar à AWS uma revisão do processo de lançamento do Bottlerocket, incluindo critérios mais claros de promoção de AMIs, testes antes da exposição aos usuários, sinalização explícita de versões em pre-release ou rollout parcial e publicação sincronizada da documentação necessária para operação segura em ambientes produtivos.

Este documento consolida evidências sobre a publicação da versão `v1.58.0` do Bottlerocket OS em AMIs oficiais da AWS antes da disponibilização completa da release e da documentação pública correspondente. Este caso deve ser lido como exemplo de um problema de processo: o desalinhamento entre console, release upstream e documentação pode ocorrer em outras versões e representa risco recorrente para usuários. O objetivo é encaminhar a análise para a AWS e solicitar revisão do processo de release, validação e comunicação das versões do Bottlerocket.

### Escopo da evidência

A `v1.58.0` é o caso documentado neste repositório porque há prints, saída de AWS CLI, release upstream e commit de documentação que permitem montar a linha do tempo com evidência verificável. No entanto, a preocupação apresentada é sobre o processo de publicação de versões do Bottlerocket como um todo.

Quando uma versão aparece no console da AWS antes de estar alinhada com release pública, documentação oficial e sinalização de estabilidade, o risco operacional existe independentemente do número da versão. Por isso, a `v1.58.0` deve ser tratada como exemplo concreto de um padrão que precisa ser prevenido em releases futuras e investigado em versões anteriores que tenham apresentado comportamento semelhante.

### Linha do tempo observada

| Data | Evidência | Observação |
| --- | --- | --- |
| `2026-04-01` | AMIs `v1.58.0` publicadas na AWS | Dados em [`analysis/data/data.txt`](analysis/data/data.txt) e print do AMI Catalog indicam AMIs oficiais com `OwnerAlias: amazon` e `Publish date: 2026-04-01`. |
| `2026-04-07` | Release `v1.58.0` no GitHub | Print da release mostra `v1.58.0` como `Pre-release` em `Apr 7`. A página pública do GitHub também mostra `Pre-release` e data de publicação em `08 Apr 01:25` UTC. |
| Após a publicação da AMI | Rollout interrompido | A release informa que o rollout da `v1.58.0` foi interrompido por regressão em pull de imagens de container e recomenda `v1.59.0`. |
| `2026-05-01` | Documentação `1.58.x` adicionada ao site | Commit [`3cdac2f2`](https://github.com/bottlerocket-os/bottlerocket-project-website/commit/3cdac2f2ad88c89a74a1ca6f112ddf614dc157e8) adiciona a documentação `1.58.x` e marca a versão como current. |

### Evidências

#### 1. AMIs `v1.58.0` disponíveis na AWS em `2026-04-01`

O script [`analysis/scripts/filter_bottlerocket_amis.sh`](analysis/scripts/filter_bottlerocket_amis.sh) consulta AMIs com `--owners amazon` e filtra pelo padrão:

```text
bottlerocket-aws-k8s-*-*-v1.58.0-*
```

O resultado salvo em [`analysis/data/data.txt`](analysis/data/data.txt) mostra:

- `17` regiões consultadas.
- `48` AMIs encontradas por região.
- `816` AMIs no total.
- Todas as entradas visíveis foram criadas em `2026-04-01T...Z`.
- O sufixo da AMI corresponde ao commit/tag `c5c37032`, o mesmo hash curto mostrado na release `v1.58.0`.

Exemplo em `sa-east-1`:

```text
bottlerocket-aws-k8s-1.35-fips-x86_64-v1.58.0-c5c37032  2026-04-01T22:59:03.000Z
```

![Consulta via AWS CLI retornando AMIs Bottlerocket v1.58.0 em sa-east-1](analysis/img/bottlerocket-1.58.0.png)

O AMI Catalog do console da AWS também mostra uma AMI oficial `v1.58.0`, com `OwnerAlias: amazon`, `Verified provider` e `Publish date: 2026-04-01`.

![AMI Bottlerocket v1.58.0 publicada no AMI Catalog da AWS](analysis/img/bottlerocket-aws-1.58.0.png)

#### 2. Release pública marcada como pre-release e com rollout interrompido

A release [`v1.58.0`](https://github.com/bottlerocket-os/bottlerocket/releases/tag/v1.58.0) aparece como `Pre-release`. O print coletado mostra a data `Apr 7`, o tag `v1.58.0` e o commit `c5c3703`.

O mesmo print registra o aviso de que o rollout da `v1.58.0` foi interrompido porque a versão introduziu uma regressão que causa falhas no pull de certas imagens de container, com recomendação de uso da `v1.59.0`.

![Release v1.58.0 marcada como pre-release e com aviso de regressão](analysis/img/bottlerocket-release-v1.58.0.png)

Essa evidência é crítica porque a AMI já estava disponível no console antes da release pública e antes de a própria página de release indicar uma versão pronta para uso amplo.

#### 3. Documentação `1.58.x` publicada depois da disponibilização das AMIs

O print do site do Bottlerocket mostra a documentação navegando em `1.57.x`; a versão `1.58.x` não aparece na lista lateral naquele momento.

![Site do Bottlerocket ainda sem documentação 1.58.x disponível](analysis/img/bottlerocket-website.png)

O commit [`3cdac2f2`](https://github.com/bottlerocket-os/bottlerocket-project-website/commit/3cdac2f2ad88c89a74a1ca6f112ddf614dc157e8) atualiza o site para `1.58.0`, adiciona a árvore `content/en/os/1.58.x/` e altera `data/versions/current.toml` de `1.57` para `1.58`. O patch desse commit inclui `125` arquivos alterados, com `5.850` linhas adicionadas, incluindo documentação de API, settings, bootstrap, variantes, pacotes e informações de versão.

![Commit que adiciona a documentação 1.58.x ao site do Bottlerocket](analysis/img/bottlerocket-website-1.58.0.png)

### Impacto operacional

Quando uma AMI nova aparece no console da AWS como imagem oficial, usuários tendem a interpretá-la como pronta para uso. No caso evidenciado pela `v1.58.0`, essa interpretação é perigosa porque:

- A AMI `v1.58.0` estava publicada antes da release pública aparecer como disponível de forma clara.
- A release foi marcada como `Pre-release`, indicando uma fase de disponibilização ainda não concluída.
- Houve uma regressão reconhecida na própria release, com interrupção do rollout.
- A documentação `1.58.x` ainda não estava disponível no site no momento inicial, forçando usuários a buscar parâmetros e mudanças diretamente no código fonte.
- Mudanças de bootstrap, settings, variantes, pacotes ou comportamento de runtime podem afetar diretamente clusters Kubernetes e cargas produtivas.

Esse tipo de desalinhamento cria uma janela em que a AWS disponibiliza uma imagem consumível no console, mas o usuário ainda não tem sinais suficientes de maturidade, risco e documentação operacional para adotá-la com segurança.

### Risco para ambientes produtivos

O risco não está apenas na existência de uma regressão específica da `v1.58.0`. O ponto central é a combinação de três fatores que pode afetar qualquer versão:

1. AMI oficial disponível para seleção no console.
2. Release upstream ainda em estado de pre-release ou rollout incompleto.
3. Documentação operacional publicada depois da AMI.

Em ambientes produtivos, isso pode resultar em:

- Substituição de nodes por uma versão afetada.
- Falhas de workloads por erro no pull de imagens de container.
- Dificuldade de rollback, troubleshooting e validação por falta de documentação da versão.
- Necessidade de consultar o código fonte do Bottlerocket para descobrir parâmetros de bootstrap e settings.
- Exposição de usuários a uma versão que ainda não deveria ser promovida como opção segura no console.

### Recomendações para a AWS

Solicita-se que a AWS revise o fluxo de publicação de AMIs Bottlerocket para reduzir risco de adoção prematura:

- Não expor AMIs novas no console/AMI Catalog antes da release pública estar estável e documentada.
- Separar claramente AMIs de pre-release, rollout parcial ou validação interna de AMIs recomendadas para produção.
- Adicionar gating de release que valide a existência da documentação correspondente antes da promoção da AMI.
- Exibir no console avisos de risco quando uma versão estiver em pre-release, rollout parcial, rollback ou com regressão conhecida.
- Aumentar a cobertura de testes antes da promoção global, especialmente para pull de imagens de container, variantes Kubernetes, variantes NVIDIA/FIPS e bootstrap.
- Publicar notas operacionais e parâmetros de bootstrap/settings junto com a AMI, não semanas depois.
- Adotar um período de canary/regional rollout com critérios objetivos de promoção antes de tornar a versão amplamente visível.
- Garantir que recomendações de versão no console, no repositório e no site do Bottlerocket estejam sincronizadas.

### Conclusão

Com base nos dados coletados, a `v1.58.0` foi publicada como AMI oficial na AWS em `2026-04-01`, apareceu posteriormente como release pública `Pre-release` e teve o rollout interrompido por regressão. A documentação `1.58.x` foi adicionada ao site apenas em `2026-05-01`. Esse caso é uma evidência concreta do problema, mas não deve ser interpretado como ocorrência isolada.

Esse fluxo cria uma janela de risco para usuários que confiam no console da AWS como fonte de verdade para escolher imagens oficiais. A recomendação é que a AWS trate a promoção de AMIs Bottlerocket como parte de um processo atômico para todas as versões: release estável, AMI publicada, documentação disponível, notas operacionais e alertas de regressão devem estar sincronizados antes da exposição ampla para usuários.

### Fontes e artefatos

- Release oficial Bottlerocket `v1.58.0`: <https://github.com/bottlerocket-os/bottlerocket/releases/tag/v1.58.0>
- Commit de documentação `1.58.x` no site: <https://github.com/bottlerocket-os/bottlerocket-project-website/commit/3cdac2f2ad88c89a74a1ca6f112ddf614dc157e8>
- Script de coleta de AMIs: [`analysis/scripts/filter_bottlerocket_amis.py`](analysis/scripts/filter_bottlerocket_amis.sh)
- Resultado da coleta: [`analysis/data/data.txt`](analysis/data/data.txt)
- Prints de evidência: [`analysis/img/`](analysis/img/)
- Documentação AWS para localizar AMIs: <https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/finding-an-ami.html>
