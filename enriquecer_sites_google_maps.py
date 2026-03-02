#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
enriquecer_sites_google_maps.py (v3 - industrial hardened)

Features:
- SQLite persistent cache
- --force-refresh (ignora cache)
- --max-api-calls (controle de custo)
- resume automático
- logging estruturado
"""

import csv
import os
import time
import argparse
import logging
import requests
import sqlite3
from datetime import datetime
from dotenv import load_dotenv
from pathlib import Path

# =========================
# Logging
# =========================
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s"
)

# =========================
# SQLite Cache
# =========================
DB_FILE = "data/enrichment_cache.db"


def init_db():
    Path("data").mkdir(exist_ok=True)
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS enrichment_cache (
            company_name TEXT PRIMARY KEY,
            company_website TEXT,
            place_id TEXT,
            formatted_address TEXT,
            confidence_score REAL,
            segment TEXT,
            source TEXT,
            last_updated TEXT
        )
    """)
    conn.commit()
    return conn


def get_from_cache(conn, company_name):
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM enrichment_cache WHERE company_name=?", (company_name,))
    row = cursor.fetchone()
    if row:
        return {
            "company_name": row[0],
            "company_website": row[1],
            "place_id": row[2],
            "formatted_address": row[3],
            "confidence_score": row[4],
            "segment": row[5],
            "source": row[6]
        }
    return None


def save_to_cache(conn, data):
    cursor = conn.cursor()
    cursor.execute("""
        INSERT OR REPLACE INTO enrichment_cache
        (company_name, company_website, place_id, formatted_address,
         confidence_score, segment, source, last_updated)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        data["company_name"],
        data["company_website"],
        data["place_id"],
        data["formatted_address"],
        data["confidence_score"],
        data["segment"],
        data["source"],
        datetime.utcnow().isoformat()
    ))
    conn.commit()

# =========================
# API URLs
# =========================
TEXT_SEARCH_URL = "https://maps.googleapis.com/maps/api/place/textsearch/json"
PLACE_DETAILS_URL = "https://maps.googleapis.com/maps/api/place/details/json"

# =========================
# Utils
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
# Main
# =========================

def main():

    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--sleep", type=float, default=0.8)
    parser.add_argument("--force-refresh", action="store_true")
    parser.add_argument("--max-api-calls", type=int, default=None)
    args = parser.parse_args()

    validate_input_file(args.input)

    load_dotenv()
    api_key = os.getenv("GOOGLE_MAPS_API_KEY")
    if not api_key:
        raise ValueError("GOOGLE_MAPS_API_KEY não encontrada no .env")

    conn = init_db()
    api_calls = 0

    # =========================
    # Controle Financeiro
    # =========================
    COST_PER_TEXT_SEARCH = 0.017  # ajuste conforme seu billing real
    COST_PER_DETAILS = 0.017      # ajuste conforme seu billing real
    total_cost = 0.0
    segment_costs = {}

    processed_companies = set()

    if os.path.exists(args.output):
        with open(args.output, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                processed_companies.add(normalize_name(row["company_name"]))
        logging.info(f"Resume ativado: {len(processed_companies)} empresas já processadas.")

    session = requests.Session()

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
            normalized = normalize_name(company_name)

            if normalized in processed_companies:
                continue

            if not args.force_refresh:
                cached = get_from_cache(conn, normalized)
                if cached:
                    writer.writerow(cached)
                    processed_companies.add(normalized)
                    enriched_count += 1
                    logging.info(f"[CACHE] {company_name} reutilizado.")
                    continue

            if args.max_api_calls and api_calls >= args.max_api_calls:
                logging.warning("Limite de chamadas API atingido. Encerrando execução.")
                break

            api_calls += 1
            total_cost += COST_PER_TEXT_SEARCH

            logging.info(f"Buscando: {company_name}")

            place_data = get_place_data(session, api_key, company_name)
            if not place_data:
                logging.warning("Nenhum resultado encontrado.")
                continue

            place_id = place_data["place_id"]
            details = get_place_details(session, api_key, place_id)
            total_cost += COST_PER_DETAILS
            if not details:
                logging.warning("Sem detalhes.")
                continue

            website = details.get("website", "")
            formatted_address = details.get("formatted_address", "")
            returned_name = details.get("name", "")

            confidence = calculate_confidence(company_name, returned_name, website)

            row_data = {
                "company_name": company_name,
                "company_website": website,
                "place_id": place_id,
                "formatted_address": formatted_address,
                "confidence_score": confidence,
                "segment": row.get("segment", ""),
                "source": row.get("source", "linkedin")
            }

            writer.writerow(row_data)
            save_to_cache(conn, row_data)

            # Controle financeiro por segmento
            segment = row_data.get("segment", "unknown") or "unknown"
            if segment not in segment_costs:
                segment_costs[segment] = 0.0
            segment_costs[segment] += (COST_PER_TEXT_SEARCH + COST_PER_DETAILS)

            enriched_count += 1
            processed_companies.add(normalized)

            logging.info(f"Website: {website} | Score: {confidence}")

            time.sleep(args.sleep)

    logging.info("===== RESUMO FINANCEIRO =====")
    logging.info(f"Custo estimado total (USD): {round(total_cost, 4)}")

    for seg, cost in segment_costs.items():
        logging.info(f"Segmento: {seg} | Custo estimado (USD): {round(cost, 4)}")

    # Log financeiro persistente
    Path("data").mkdir(exist_ok=True)
    finance_log_file = "data/finance_log.csv"
    write_header = not os.path.exists(finance_log_file)

    with open(finance_log_file, "a", newline="", encoding="utf-8") as fin_log:
        fin_writer = csv.writer(fin_log)
        if write_header:
            fin_writer.writerow(["timestamp", "api_calls", "total_cost_usd"])

        fin_writer.writerow([
            datetime.utcnow().isoformat(),
            api_calls,
            round(total_cost, 4)
        ])

    logging.info(f"Chamadas pagas nesta execução: {api_calls}")
    conn.close()

    logging.info("Processo concluído com sucesso.")
    logging.info(f"Empresas enriquecidas nesta execução: {enriched_count}")


if __name__ == "__main__":
    main()
