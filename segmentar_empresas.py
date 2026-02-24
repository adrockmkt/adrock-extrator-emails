import csv
import os
import re
from collections import defaultdict

INPUT_CSV = "Connections.csv"
OUTPUT_DIR = "csv_por_segmento"

os.makedirs(OUTPUT_DIR, exist_ok=True)

# -----------------------------
# Normalização
# -----------------------------
def normalize(text):
    if not text:
        return ""
    return re.sub(r"\s+", " ", text.strip().lower())

# -----------------------------
# Regras de segmentação
# -----------------------------
SEGMENT_RULES = {
    "tecnologia": ["tech", "software", "saas", "systems", "cloud", "it", "digital"],
    "marketing_comunicacao": ["marketing", "comunicação", "advertising", "ads", "branding", "seo", "mídia"],
    "educacao": ["educação", "education", "school", "universidade", "college", "ensino"],
    "saude": ["saúde", "health", "clinic", "hospital", "medical", "med"],
    "juridico": ["jurídico", "legal", "advocacia", "law", "attorney"],
    "ecommerce_varejo": ["ecommerce", "e-commerce", "shop", "store", "varejo", "retail"],
    "industria": ["indústria", "industrial", "manufacturing", "fabrica"],
    "servicos_b2b": ["consultoria", "consulting", "services", "outsourcing"],
    "ong_terceiro_setor": ["ong", "instituto", "associação", "foundation", "nonprofit"]
}

def classify_segment(company_name, website, industry):
    haystack = " ".join([company_name, website, industry]).lower()
    for segment, keywords in SEGMENT_RULES.items():
        for kw in keywords:
            if kw in haystack:
                return segment
    return "outros"

# -----------------------------
# Leitura do CSV
# -----------------------------
companies = defaultdict(list)

with open(INPUT_CSV, newline="", encoding="utf-8") as f:
    # Avança até encontrar o header real do LinkedIn
    while True:
        line = f.readline()
        if not line:
            raise ValueError("Header não encontrado no Connections.csv")
        if line.lower().startswith("first name"):
            header = [h.strip() for h in line.strip().split(",")]
            break

    reader = csv.DictReader(f, fieldnames=header)

    for row in reader:
        company_name = normalize(row.get("Company"))
        website = ""  # Connections.csv não fornece site
        industry = ""

        if not company_name:
            continue

        segment = classify_segment(company_name, website, industry)

        companies[segment].append({
            "company_name": company_name,
            "company_website": website,
            "segment": segment,
            "source": "linkedin_connections"
        })

# -----------------------------
# Escrita dos CSVs por segmento
# -----------------------------
for segment, rows in companies.items():
    output_file = os.path.join(OUTPUT_DIR, f"empresas_{segment}.csv")

    with open(output_file, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=["company_name", "company_website", "segment", "source"]
        )
        writer.writeheader()
        for row in rows:
            writer.writerow(row)

    print(f"[OK] {len(rows)} empresas → {output_file}")

print("\nProcesso concluído. CSVs prontos para uso no extrator.")