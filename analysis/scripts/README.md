# Como executar o script de coleta

## Objetivo

O objetivo do script é consultar AMIs oficiais do Bottlerocket publicadas pela AWS, filtrando por versão do Bottlerocket, versão do Kubernetes e regiões, para gerar evidências reproduzíveis da data de publicação e disponibilidade dessas imagens.

Este guia mostra apenas como executar o script `filter_bottlerocket_amis.py` usando um ambiente virtual Python (`venv`).

## Pré-requisitos

- Python 3.9 ou superior.
- Credenciais AWS configuradas.
- Permissões AWS para `ec2:DescribeRegions` e `ec2:DescribeImages`.

## Passo a passo

Execute os comandos a partir da raiz do repositório.

Crie o ambiente virtual:

```bash
python3 -m venv .venv
```

Ative o ambiente virtual:

```bash
source .venv/bin/activate
```

Instale as dependências:

```bash
python -m pip install --upgrade pip
python -m pip install -r analysis/scripts/requirements.txt
```

Execute a coleta:

```bash
python analysis/scripts/filter_bottlerocket_amis.py \
  --bottlerocket-version 1.58.0
```

Exemplo filtrando versão do Kubernetes e regiões:

```bash
python analysis/scripts/filter_bottlerocket_amis.py \
  --bottlerocket-version 1.58.0 \
  --k8s-version 1.35 \
  --regions sa-east-1,us-east-1
```

Exemplo salvando a saída em JSON:

```bash
python analysis/scripts/filter_bottlerocket_amis.py \
  --bottlerocket-version 1.58.0 \
  --output-format json \
  --output-file analysis/data/bottlerocket-1.58.0.json
```

Ao finalizar, desative o ambiente virtual:

```bash
deactivate
```
