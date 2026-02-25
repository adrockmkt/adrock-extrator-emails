#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
enriquecer_sites_google_maps.py (v2 - production ready)

Enriquece empresas com:
- website oficial
- place_id
- formatted_address
- confidence_score

Suporta:
- argumentos CLI (--input, --output, --limit, --sleep)
- resume automático (não reprocessa empresas já salvas)
- validação de arquivo
- logging estruturado
"""

import csv
import os
import time
import argparse
import logging
import requests
from dotenv import load_dotenv
from pathlib import Path

# =========================
# Configuração Logging
# =========================
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s"
)

# =========================
# API URLs
# =========================
TEXT_SEARCH_URL = "https://maps.googleapis.com/maps/api/place/textsearch/json"
PLACE_DETAILS_URL = "https://maps.googleapis.com/maps/api/place/details/json"

# =========================
# Utilidades
# =========================
def calculate_confidence(company_name, returned_name, website):
    score = 0.0
    company_lower = company_name.lower()

    if returned_name and company_lower in returned_name.lower():
        score += 0.5

    if website and company_lower.split()[0] in website.lower():
        score += 0.4

    if website:
        score += 0.1

    return round(min(score, 1.0), 2)


def normalize_name(name):
    return name.strip().lower()


def validate_input_file(path):
    if not os.path.exists(path):
        raise FileNotFoundError(f"Arquivo de entrada não encontrado: {path}")

    if os.path.getsize(path) == 0:
        raise ValueError(f"Arquivo vazio: {path}")


# =========================
# Google API
# =========================
def get_place_data(session, api_key, company_name):
    params = {
        "query": f"{company_name} site oficial",
        "key": api_key
    }

    response = session.get(TEXT_SEARCH_URL, params=params, timeout=15)
    data = response.json()

    if not data.get("results"):
        return None

    return data["results"][0]


def get_place_details(session, api_key, place_id):
    params = {
        "place_id": place_id,
        "fields": "name,website,formatted_address",
        "key": api_key
    }

    response = session.get(PLACE_DETAILS_URL, params=params, timeout=15)
    return response.json().get("result")


# =========================
# Processo Principal
# =========================
def main():

    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True, help="CSV de entrada")
    parser.add_argument("--output", required=True, help="CSV enriquecido")
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--sleep", type=float, default=0.8)
    args = parser.parse_args()

    validate_input_file(args.input)

    load_dotenv()
    api_key = os.getenv("GOOGLE_MAPS_API_KEY")

    if not api_key:
        raise ValueError("GOOGLE_MAPS_API_KEY não encontrada no .env")

    processed_companies = set()

    # Resume mode
    if os.path.exists(args.output):
        with open(args.output, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                processed_companies.add(normalize_name(row["company_name"]))

        logging.info(f"Resume ativado: {len(processed_companies)} empresas já processadas.")

    session = requests.Session()

    total = 0
    enriched_count = 0

    with open(args.input, newline="", encoding="utf-8") as infile, \
         open(args.output, "a", newline="", encoding="utf-8") as outfile:

        reader = csv.DictReader(infile)

        fieldnames = [
            "company_name",
            "company_website",
            "place_id",
            "formatted_address",
            "confidence_score",
            "segment",
            "source"
        ]

        writer = csv.DictWriter(outfile, fieldnames=fieldnames)

        if os.path.getsize(args.output) == 0:
            writer.writeheader()

        for row in reader:

            if args.limit and enriched_count >= args.limit:
                break

            company_name = row["company_name"]

            if normalize_name(company_name) in processed_companies:
                continue

            total += 1
            logging.info(f"Buscando: {company_name}")

            place_data = get_place_data(session, api_key, company_name)

            if not place_data:
                logging.warning("Nenhum resultado encontrado.")
                continue

            place_id = place_data["place_id"]
            details = get_place_details(session, api_key, place_id)

            if not details:
                logging.warning("Sem detalhes.")
                continue

            website = details.get("website", "")
            formatted_address = details.get("formatted_address", "")
            returned_name = details.get("name", "")

            confidence = calculate_confidence(company_name, returned_name, website)

            writer.writerow({
                "company_name": company_name,
                "company_website": website,
                "place_id": place_id,
                "formatted_address": formatted_address,
                "confidence_score": confidence,
                "segment": row.get("segment", ""),
                "source": row.get("source", "linkedin")
            })

            enriched_count += 1
            processed_companies.add(normalize_name(company_name))

            logging.info(f"Website: {website} | Score: {confidence}")

            time.sleep(args.sleep)

    logging.info("Processo concluído com sucesso.")
    logging.info(f"Empresas enriquecidas nesta execução: {enriched_count}")


if __name__ == "__main__":
    main()
