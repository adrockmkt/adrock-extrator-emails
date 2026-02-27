#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Worker unitário de enriquecimento por empresa.
Processa exatamente 1 empresa por execução.
Preparado para uso industrial com checkpoint granular.
"""

import argparse
import json
import sys
from pathlib import Path
from datetime import datetime

import pandas as pd
from places_client import get_company_website


def parse_args():
    parser = argparse.ArgumentParser(description="Enriquecimento individual por empresa")
    parser.add_argument("--company-name", required=True)
    parser.add_argument("--company-website", required=False, default="")
    parser.add_argument("--segment", required=True)
    parser.add_argument("--output-dir", default="csv_enriquecido_individual")
    return parser.parse_args()


def main():
    args = parse_args()

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Buscar website real via Google Places
    website = get_company_website(args.company_name)

    if not website:
        print(f"[SKIP] Empresa {args.company_name} sem website encontrado via Places.")
        sys.exit(0)

    enriched_data = {
        "company_name": args.company_name,
        "company_website": website,
        "confidence_score": 0.9,
        "enriched_at": datetime.utcnow().isoformat()
    }

    output_file = output_dir / f"{args.segment}_enriched_individual.csv"

    df = pd.DataFrame([enriched_data])

    if output_file.exists():
        df_existing = pd.read_csv(output_file)
        df_final = pd.concat([df_existing, df], ignore_index=True)
    else:
        df_final = df

    df_final.to_csv(output_file, index=False)

    print(f"[OK] Empresa {args.company_name} enriquecida com sucesso.")


if __name__ == "__main__":
    main()