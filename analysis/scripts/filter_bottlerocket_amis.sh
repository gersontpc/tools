#!/bin/bash

set -euo pipefail

# Check for changelog flag anywhere in the arguments
FETCH_CHANGELOG=false
NEW_ARGS=()
for arg in "$@"; do
    if [[ "$arg" == "--changelog" || "$arg" == "-c" ]]; then
        FETCH_CHANGELOG=true
    else
        NEW_ARGS+=("$arg")
    fi
done
set -- "${NEW_ARGS[@]+"${NEW_ARGS[@]}"}"

# If positional args are provided, use them; otherwise prompt interactively when running in a TTY.
BOTTLEROCKET_VERSION_ARG="${1-}"
K8S_VERSION_ARG="${2-}"
REGIONS_ARG="${3-}"

if [[ -t 0 && -z "$BOTTLEROCKET_VERSION_ARG" && -z "$K8S_VERSION_ARG" && -z "$REGIONS_ARG" ]]; then
    echo "Informe as versões (deixe em branco para buscar todas):"
    echo " - Versão do Bottlerocket (ex: 1.58.0). Deixe em branco para todas."
    echo " - Versão do Kubernetes (ex: 1.35). Deixe em branco para todas."
    echo " - Regiões (separadas por vírgula). Deixe em branco para todas as regiões."
    read -r -p "Versão do Bottlerocket: " BOTTLEROCKET_VERSION
    read -r -p "Versão do Kubernetes: " K8S_VERSION
    read -r -p "Regiões (comma-separated): " REGIONS
    read -r -p "Buscar changelog no GitHub? (s/N): " FETCH_CHANGELOG_INPUT
    if [[ "$FETCH_CHANGELOG_INPUT" =~ ^[Ss]$ ]]; then
        FETCH_CHANGELOG=true
    fi
else
    BOTTLEROCKET_VERSION="${BOTTLEROCKET_VERSION_ARG}"
    K8S_VERSION="${K8S_VERSION_ARG}"
    REGIONS="${REGIONS_ARG}"
fi

# Treat empty values as wildcards in the AMI name pattern
BR_PART="${BOTTLEROCKET_VERSION:-*}"
K8S_PART="${K8S_VERSION:-*}"
FILTER_PATTERN="bottlerocket-aws-k8s-${K8S_PART}-*-v${BR_PART}-*"

get_regions() {
    if [[ -n "$REGIONS" ]]; then
        echo "$REGIONS" | tr ',' '\n'
    else
        aws ec2 describe-regions \
            --query 'Regions[].RegionName' \
            --output text | tr '\t' '\n'
    fi
}

query_amis() {
    local region="$1"
    aws ec2 describe-images \
        --region "$region" \
        --owners amazon \
        --filters "Name=name,Values=${FILTER_PATTERN}" \
        --query 'Images[*].{AMI_ID:ImageId,Name:Name,Region:'"'${region}'"',Arch:Architecture,CreationDate:CreationDate}' \
        --output json 2>/dev/null
}

echo "Buscando AMIs com o padrao: ${FILTER_PATTERN}"
echo "=================================================="

all_results="[]"

while IFS= read -r region; do
    echo "Consultando regiao: ${region}..." >&2
    result=$(query_amis "$region")

    if [[ "$result" != "[]" && -n "$result" ]]; then
        all_results=$(echo "$all_results $result" | jq -s 'add')
        count=$(echo "$result" | jq 'length')
        echo "  -> ${count} AMI(s) encontrada(s)" >&2
    fi
done < <(get_regions)

echo ""
echo "Resultado final:"
{
    echo -e "K8S_Version\tRegion\tAMI_ID\tArch\tName\tCreationDate"
    echo "$all_results" | jq -r '
      map(. + {k8s: (try (.Name | capture("bottlerocket-aws-k8s-(?<k8s>[^-]+)").k8s) catch "")})
      | sort_by(.k8s | split(".") | map(tonumber? // 0))
      | .[] | [.k8s, .Region, .AMI_ID, .Arch, .Name, .CreationDate] | @tsv'
} | column -t -s $'\t'

echo ""
echo "Total: $(echo "$all_results" | jq 'length') AMI(s)"

# ==============================================================================
# SEÇÃO: BUSCAR CHANGELOG NO GITHUB (OPCIONAL)
# ==============================================================================
if [[ "$all_results" != "[]" && "$FETCH_CHANGELOG" == "true" ]]; then
    echo -e "\n=================================================="
    echo "Buscando Changelog no GitHub do Bottlerocket..."
    echo "=================================================="

    br_versions=$(echo "$all_results" | jq -r '
        map(try (.Name | capture("-v(?<br>[0-9]+\\.[0-9]+\\.[0-9]+)").br) catch empty) 
        | unique | .[]' 2>/dev/null)

    if [[ -n "$br_versions" ]]; then
        for version in $br_versions; do
            echo -e "\nCHANGELOG PARA BOTTLEROCKET v${version}:"
            echo "--------------------------------------------------"
            
            changelog=$(curl -s "https://api.github.com/repos/bottlerocket-os/bottlerocket/releases/tags/v${version}" | jq -r '.body // empty')
            
            if [[ -n "$changelog" ]]; then
                echo "$changelog"
            else
                echo "AVISO: Nao foi possivel obter o changelog para a v${version} (Limite de API ou versao nao encontrada)."
            fi
            echo "--------------------------------------------------"
