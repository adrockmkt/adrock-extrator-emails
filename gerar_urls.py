import csv
from urllib.parse import urlparse

INPUT_CSV = "csv_enriquecido/empresas_ong_terceiro_setor_enriquecido.csv"
OUTPUT_FILE = "urls.txt"
MIN_SCORE = 0.4


def normalize_url(url):
    if not url:
        return None

    parsed = urlparse(url)

    if not parsed.scheme:
        url = "https://" + url
        parsed = urlparse(url)

    domain = parsed.netloc.lower()

    # Remove www
    if domain.startswith("www."):
        domain = domain[4:]

    return f"https://{domain}"


urls = set()

with open(INPUT_CSV, newline="", encoding="utf-8") as infile:
    reader = csv.DictReader(infile)

    for row in reader:
        website = row.get("company_website", "")
        score = float(row.get("confidence_score", 0))

        if website and score >= MIN_SCORE:
            normalized = normalize_url(website)
            if normalized:
                urls.add(normalized)

with open(OUTPUT_FILE, "w", encoding="utf-8") as outfile:
    for url in sorted(urls):
        outfile.write(url + "\n")

print(f"\n{len(urls)} URLs geradas em {OUTPUT_FILE}")