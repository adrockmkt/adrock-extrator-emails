#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import argparse
import subprocess
import sys
from pathlib import Path

import pandas as pd
from urllib.parse import urlparse


def parse_args():
    parser = argparse.ArgumentParser(description="Pipeline: Enriquecido → URLs → Extrator")
    parser.add_argument("--input", required=True, help="CSV enriquecido")
    parser.add_argument("--confidence", type=float, default=0.6, help="Score mínimo de confiança")
    parser.add_argument("--urls-output", default="urls.txt", help="Arquivo urls.txt gerado")
    parser.add_argument("--extrator-script", default="extrator.py", help="Script extrator")
    return parser.parse_args()


def main():
    args = parse_args()

    input_path = Path(args.input)
    if not input_path.exists():
        print(f"Arquivo não encontrado: {input_path}")
        sys.exit(1)

    print("==== LENDO CSV ENRIQUECIDO ====")
    df = pd.read_csv(input_path)

    if "company_website" not in df.columns:
        print("Coluna company_website não encontrada.")
        sys.exit(1)

    print("Filtrando por confidence_score >=", args.confidence)
    df = df[df["confidence_score"] >= args.confidence]

    print("Removendo websites vazios")
    df = df[df["company_website"].notna()]
    df = df[df["company_website"] != ""]

    # Garantir existência de root_domain
    if "root_domain" not in df.columns:
        print("Coluna root_domain não encontrada. Gerando a partir de company_website.")

        def extract_root(url):
            try:
                parsed = urlparse(str(url))
                domain = parsed.netloc.lower()
                return domain.replace("www.", "")
            except Exception:
                return None

        df["root_domain"] = df["company_website"].apply(extract_root)

    print("Removendo root_domain inválido")
    df = df[df["root_domain"].notna()]
    df = df[df["root_domain"] != ""]

    print("Deduplicando por root_domain")
    df = df.drop_duplicates(subset=["root_domain"])

    print(f"{len(df)} domínios válidos encontrados.")

    urls_path = Path(args.urls_output)

    print("Gerando urls.txt")
    df["company_website"].to_csv(urls_path, index=False, header=False)

    print("==== EXECUTANDO EXTRATOR ====")
    subprocess.run(["python3", args.extrator_script], check=True)

    print("==== PIPELINE FINALIZADO ====")


if __name__ == "__main__":
    main()