#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
filter_bottlerocket_amis.py

Busca AMIs oficiais do Bottlerocket publicadas pela AWS, filtrando por:
- versão do Bottlerocket
- versão do Kubernetes
- regiões específicas ou todas as regiões

Também pode buscar o changelog/release notes no GitHub para as versões
Bottlerocket encontradas.

Exemplos:

  python3 analysis/scripts/filter_bottlerocket_amis.py \
    --bottlerocket-version 1.58.0

  python3 analysis/scripts/filter_bottlerocket_amis.py \
    --bottlerocket-version 1.58.0 \
    --k8s-version 1.35 \
    --regions sa-east-1,us-east-1

  python3 analysis/scripts/filter_bottlerocket_amis.py \
    --bottlerocket-version 1.58.0 \
    --output-format json \
    --output-file analysis/data/bottlerocket-1.58.0.json

  python3 analysis/scripts/filter_bottlerocket_amis.py \
    --bottlerocket-version 1.58.0 \
    --changelog
"""

import argparse
import csv
import json
import os
import re
import sys
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any, Dict, List


import boto3
from botocore.exceptions import BotoCoreError, ClientError


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Busca AMIs oficiais do Bottlerocket na AWS."
    )

    parser.add_argument(
        "--bottlerocket-version",
        "-b",
        default="",
        help="Versão do Bottlerocket. Ex: 1.58.0. Vazio = todas.",
    )

    parser.add_argument(
        "--k8s-version",
        "-k",
        default="",
        help="Versão do Kubernetes. Ex: 1.35. Vazio = todas.",
    )

    parser.add_argument(
        "--regions",
        "-r",
        default="",
        help="Regiões separadas por vírgula. Ex: sa-east-1,us-east-1. Vazio = todas.",
    )

    parser.add_argument(
        "--output-format",
        "-f",
        choices=["table", "json", "csv", "tsv"],
        default="table",
        help="Formato de saída. Padrão: table.",
    )

    parser.add_argument(
        "--output-file",
        "-o",
        default="",
        help="Arquivo para salvar o resultado. Se omitido, imprime no stdout.",
    )

    parser.add_argument(
        "--changelog",
        "-c",
        action="store_true",
        help="Busca o changelog no GitHub para as versões Bottlerocket encontradas.",
    )

    parser.add_argument(
        "--github-token",
        default=os.environ.get("GITHUB_TOKEN", ""),
        help="Token GitHub opcional. Também pode ser informado via variável GITHUB_TOKEN.",
    )

    parser.add_argument(
        "--quiet",
        "-q",
        action="store_true",
        help="Reduz logs de progresso no stderr.",
    )

    return parser.parse_args()


def prompt_if_no_args(args: argparse.Namespace) -> argparse.Namespace:
    no_filters = (
        not args.bottlerocket_version
        and not args.k8s_version
        and not args.regions
    )

    if sys.stdin.isatty() and no_filters:
        print("Informe as versões (deixe em branco para buscar todas):")
        print(" - Versão do Bottlerocket. Ex: 1.58.0")
        print(" - Versão do Kubernetes. Ex: 1.35")
        print(" - Regiões separadas por vírgula. Ex: sa-east-1,us-east-1")
        print()

        args.bottlerocket_version = input("Versão do Bottlerocket: ").strip()
        args.k8s_version = input("Versão do Kubernetes: ").strip()
        args.regions = input("Regiões: ").strip()

        changelog_input = input("Buscar changelog no GitHub? (s/N): ").strip()
        if changelog_input.lower() == "s":
            args.changelog = True

    return args


def build_filter_pattern(bottlerocket_version: str, k8s_version: str) -> str:
    br_part = bottlerocket_version if bottlerocket_version else "*"
    k8s_part = k8s_version if k8s_version else "*"

    return f"bottlerocket-aws-k8s-{k8s_part}-*-v{br_part}-*"


def get_regions(regions_arg: str) -> List[str]:
    if regions_arg:
        return [
            region.strip()
            for region in regions_arg.split(",")
            if region.strip()
        ]

    ec2 = boto3.client("ec2")
    response = ec2.describe_regions(AllRegions=False)

    return sorted(
        region["RegionName"]
        for region in response.get("Regions", [])
    )


def extract_k8s_version(name: str) -> str:
    match = re.search(r"bottlerocket-aws-k8s-([^-]+)", name)
    return match.group(1) if match else ""


def extract_bottlerocket_version(name: str) -> str:
    match = re.search(r"-v([0-9]+\.[0-9]+\.[0-9]+)-", name)
    return match.group(1) if match else ""


def extract_variant(name: str) -> str:
    """
    Exemplo:
      bottlerocket-aws-k8s-1.35-fips-x86_64-v1.58.0-c5c37032

    Retorna:
      fips

    Para nomes sem variante clara, retorna string vazia.
    """
    match = re.search(
        r"bottlerocket-aws-k8s-[^-]+-(?P<variant>.+)-(?P<arch>x86_64|arm64)-v",
        name,
    )

    if not match:
        return ""

    return match.group("variant")


def version_sort_key(version: str) -> List[int]:
    result = []

    for part in str(version).split("."):
        try:
            result.append(int(part))
        except ValueError:
            result.append(0)

    return result


def query_amis(region: str, filter_pattern: str) -> List[Dict[str, Any]]:
    ec2 = boto3.client("ec2", region_name=region)

    response = ec2.describe_images(
        Owners=["amazon"],
        Filters=[
            {
                "Name": "name",
                "Values": [filter_pattern],
            }
        ],
    )

    results = []

    for image in response.get("Images", []):
        name = image.get("Name", "")

        results.append(
            {
                "K8S_Version": extract_k8s_version(name),
                "Bottlerocket_Version": extract_bottlerocket_version(name),
                "Region": region,
                "AMI_ID": image.get("ImageId", ""),
                "Arch": image.get("Architecture", ""),
                "Variant": extract_variant(name),
                "Name": name,
                "CreationDate": image.get("CreationDate", ""),
                "OwnerId": image.get("OwnerId", ""),
                "Public": image.get("Public", ""),
            }
        )

    return results


def sort_results(rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    return sorted(
        rows,
        key=lambda item: (
            version_sort_key(str(item.get("K8S_Version", ""))),
            version_sort_key(str(item.get("Bottlerocket_Version", ""))),
            str(item.get("Region", "")),
            str(item.get("Variant", "")),
            str(item.get("Arch", "")),
            str(item.get("CreationDate", "")),
        ),
    )


def render_table(rows: List[Dict[str, Any]]) -> str:
    headers = [
        "K8S_Version",
        "Bottlerocket_Version",
        "Region",
        "AMI_ID",
        "Arch",
        "Variant",
        "Name",
        "CreationDate",
    ]

    if not rows:
        return "Nenhuma AMI encontrada.\n"

    widths = {header: len(header) for header in headers}

    for row in rows:
        for header in headers:
            widths[header] = max(
                widths[header],
                len(str(row.get(header, ""))),
            )

    lines = []

    lines.append(
        "  ".join(
            header.ljust(widths[header])
            for header in headers
        )
    )

    lines.append(
        "  ".join(
            "-" * widths[header]
            for header in headers
        )
    )

    for row in rows:
        lines.append(
            "  ".join(
                str(row.get(header, "")).ljust(widths[header])
                for header in headers
            )
        )

    return "\n".join(lines) + "\n"


def render_json(rows: List[Dict[str, Any]]) -> str:
    return json.dumps(rows, indent=2, ensure_ascii=False) + "\n"


def render_delimited(rows: List[Dict[str, Any]], delimiter: str) -> str:
    from io import StringIO

    headers = [
        "K8S_Version",
        "Bottlerocket_Version",
        "Region",
        "AMI_ID",
        "Arch",
        "Variant",
        "Name",
        "CreationDate",
        "OwnerId",
        "Public",
    ]

    output = StringIO()
    writer = csv.DictWriter(
        output,
        fieldnames=headers,
        delimiter=delimiter,
        extrasaction="ignore",
    )

    writer.writeheader()

    for row in rows:
        writer.writerow(row)

    return output.getvalue()


def render_output(rows: List[Dict[str, Any]], output_format: str) -> str:
    if output_format == "json":
        return render_json(rows)

    if output_format == "csv":
        return render_delimited(rows, ",")

    if output_format == "tsv":
        return render_delimited(rows, "\t")

    return render_table(rows)


def write_or_print(content: str, output_file: str) -> None:
    if output_file:
        path = Path(output_file)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
    else:
        print(content, end="")


def get_unique_bottlerocket_versions(rows: List[Dict[str, Any]]) -> List[str]:
    versions = {
        str(row.get("Bottlerocket_Version", "")).strip()
        for row in rows
        if str(row.get("Bottlerocket_Version", "")).strip()
    }

    return sorted(
        versions,
        key=version_sort_key,
    )


def fetch_github_release_changelog(
    version: str,
    github_token: str = "",
) -> str:
    url = (
        "https://api.github.com/repos/"
        f"bottlerocket-os/bottlerocket/releases/tags/v{version}"
    )

    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": "bottlerocket-ami-analysis",
    }

    if github_token:
        headers["Authorization"] = f"Bearer {github_token}"

    request = urllib.request.Request(
        url,
        headers=headers,
        method="GET",
    )

    try:
        with urllib.request.urlopen(request, timeout=20) as response:
            payload = json.loads(response.read().decode("utf-8"))

    except urllib.error.HTTPError as exc:
        return (
            f"AVISO: Não foi possível obter o changelog para v{version}. "
            f"HTTP {exc.code}."
        )

    except urllib.error.URLError as exc:
        return (
            f"AVISO: Não foi possível obter o changelog para v{version}. "
            f"Erro: {exc.reason}"
        )

    except json.JSONDecodeError:
        return (
            f"AVISO: Não foi possível obter o changelog para v{version}. "
            "Resposta inválida da API do GitHub."
        )

    body = payload.get("body") or ""

    if not body.strip():
        return (
            f"AVISO: Não foi possível obter o changelog para v{version}. "
            "Release sem body ou versão não encontrada."
        )

    return body.strip()


def print_changelogs(
    rows: List[Dict[str, Any]],
    github_token: str = "",
) -> None:
    versions = get_unique_bottlerocket_versions(rows)

    if not versions:
        print(
            "\nAVISO: Nenhuma versão Bottlerocket encontrada para buscar changelog.",
            file=sys.stderr,
        )
        return

    print()
    print("=" * 60)
    print("Changelog no GitHub do Bottlerocket")
    print("=" * 60)

    for version in versions:
        print()
        print(f"CHANGELOG PARA BOTTLEROCKET v{version}:")
        print("-" * 60)

        changelog = fetch_github_release_changelog(
            version=version,
            github_token=github_token,
        )

        print(changelog)
        print("-" * 60)


def print_summary(
    rows: List[Dict[str, Any]],
    regions: List[str],
    filter_pattern: str,
    quiet: bool,
) -> None:
    if quiet:
        return

    by_region: Dict[str, int] = {}

    for row in rows:
        region = str(row.get("Region", ""))
        by_region[region] = by_region.get(region, 0) + 1

    print("", file=sys.stderr)
    print("Resumo:", file=sys.stderr)
    print(f"  Padrão consultado: {filter_pattern}", file=sys.stderr)
    print(f"  Regiões consultadas: {len(regions)}", file=sys.stderr)
    print(f"  Total de AMIs: {len(rows)}", file=sys.stderr)

    if by_region:
        print("  AMIs por região:", file=sys.stderr)

        for region in sorted(by_region):
            print(f"    - {region}: {by_region[region]}", file=sys.stderr)


def main() -> int:
    args = parse_args()
    args = prompt_if_no_args(args)

    filter_pattern = build_filter_pattern(
        bottlerocket_version=args.bottlerocket_version,
        k8s_version=args.k8s_version,
    )

    if not args.quiet:
        print(f"Buscando AMIs com o padrão: {filter_pattern}", file=sys.stderr)
        print("=" * 60, file=sys.stderr)

    try:
        regions = get_regions(args.regions)
    except (BotoCoreError, ClientError) as exc:
        print(f"Erro ao listar regiões: {exc}", file=sys.stderr)
        return 1

    all_results: List[Dict[str, Any]] = []

    for region in regions:
        if not args.quiet:
            print(f"Consultando região: {region}...", file=sys.stderr)

        try:
            region_results = query_amis(region, filter_pattern)
        except (BotoCoreError, ClientError) as exc:
            print(f"  -> erro ao consultar {region}: {exc}", file=sys.stderr)
            continue

        if region_results:
            all_results.extend(region_results)

            if not args.quiet:
                print(
                    f"  -> {len(region_results)} AMI(s) encontrada(s)",
                    file=sys.stderr,
                )

    all_results = sort_results(all_results)

    output = render_output(
        rows=all_results,
        output_format=args.output_format,
    )

    write_or_print(output, args.output_file)

    if all_results and args.changelog:
        print_changelogs(
            rows=all_results,
            github_token=args.github_token,
        )

    print_summary(
        rows=all_results,
        regions=regions,
        filter_pattern=filter_pattern,
        quiet=args.quiet,
    )

    if args.output_file and not args.quiet:
        print(f"  Resultado salvo em: {args.output_file}", file=sys.stderr)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
