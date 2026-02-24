import csv
import os
import time
import requests
from dotenv import load_dotenv

# -----------------------------
# Configurações
# -----------------------------
INPUT_CSV = "csv_por_segmento/empresas_ong_terceiro_setor.csv"
OUTPUT_DIR = "csv_enriquecido"
OUTPUT_FILE = "empresas_ong_terceiro_setor_enriquecido.csv"

TEXT_SEARCH_URL = "https://maps.googleapis.com/maps/api/place/textsearch/json"
PLACE_DETAILS_URL = "https://maps.googleapis.com/maps/api/place/details/json"

load_dotenv()
API_KEY = os.getenv("GOOGLE_MAPS_API_KEY")

if not API_KEY:
    raise ValueError("GOOGLE_MAPS_API_KEY não encontrada no .env")

os.makedirs(OUTPUT_DIR, exist_ok=True)

# -----------------------------
# Funções auxiliares
# -----------------------------
def calculate_confidence(company_name, returned_name, website):
    score = 0.0
    if returned_name and company_name.lower() in returned_name.lower():
        score += 0.5
    if website and company_name.lower().split()[0] in website.lower():
        score += 0.4
    if website:
        score += 0.1
    return round(min(score, 1.0), 2)

def get_place_id(company_name):
    params = {
        "query": f"{company_name} site oficial",
        "key": API_KEY
    }
    response = requests.get(TEXT_SEARCH_URL, params=params)
    data = response.json()

    if data.get("results"):
        return data["results"][0]
    return None

def get_place_details(place_id):
    params = {
        "place_id": place_id,
        "fields": "name,website,formatted_address",
        "key": API_KEY
    }
    response = requests.get(PLACE_DETAILS_URL, params=params)
    return response.json().get("result")

# -----------------------------
# Processamento
# -----------------------------
output_path = os.path.join(OUTPUT_DIR, OUTPUT_FILE)

with open(INPUT_CSV, newline="", encoding="utf-8") as infile, \
     open(output_path, "w", newline="", encoding="utf-8") as outfile:

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
    writer.writeheader()

    for row in reader:
        company_name = row["company_name"]

        print(f"🔎 Buscando: {company_name}")

        place_data = get_place_id(company_name)

        if not place_data:
            print("   ❌ Nenhum resultado encontrado.")
            continue

        place_id = place_data["place_id"]
        details = get_place_details(place_id)

        if not details:
            print("   ❌ Sem detalhes.")
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
            "segment": row["segment"],
            "source": row["source"]
        })

        print(f"   ✅ Website: {website} | Score: {confidence}")

        time.sleep(1)  # rate limit seguro

print("\nProcesso concluído. CSV enriquecido gerado com sucesso.")