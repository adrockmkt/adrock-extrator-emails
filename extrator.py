import requests
from requests.adapters import HTTPAdapter, Retry
from bs4 import BeautifulSoup
import re
import time
import os
import csv
import logging
from urllib.parse import urlparse, urljoin
from collections import deque
from concurrent.futures import ThreadPoolExecutor, as_completed
import argparse

# ==============================
# CONFIGURAÇÕES
# ==============================
MAX_DEPTH = 2
REQUEST_DELAY = 0.5
TIMEOUT = 8
MAX_WORKERS = 5
OUTPUT_DIR = "output"

# Limites de segurança por domínio (evita travar em sites gigantes / protegidos)
MAX_PAGES_PER_DOMAIN = 250            # hard cap de páginas por domínio
MAX_SECONDS_PER_DOMAIN = 180          # hard cap de tempo por domínio
MAX_QUEUE_SIZE = 4000                 # evita fila infinita
MAX_CONSECUTIVE_ERRORS = 8            # aborta domínio após muitos erros seguidos
MAX_CONSECUTIVE_5XX = 5               # aborta domínio após muitos 5xx seguidos

# Paths e padrões comuns de endpoints técnicos (AEM/CQ, admin, etc.) que não ajudam a achar emails
BLOCKED_PATH_SUBSTRINGS = [
    "/_cq_", "/content/_cq_", "/content/", "/etc/", "/system/", "/libs/",
    "/wp-admin", "/wp-json", "/cdn-cgi/", "/login", "/signin", "/sso",
]

# Denylist para domínios muito grandes / que tendem a bloquear crawl
DENYLIST_DOMAINS = [
    "accenture.com",
]

BLOCKED_DOMAINS = [
    "facebook.com", "instagram.com", "linkedin.com",
    "youtube.com", "twitter.com", "x.com", "t.co", "wa.me",
    "mercadopago", "drive.google.com",
    "google.com", "googleusercontent.com", "gstatic.com",
]

PRIORITY_PATHS = [
    "contato", "sobre", "quem-somos",
    "institucional", "transparencia",
    "equipe", "imprensa"
]

EMAIL_REGEX = re.compile(
    r"\b[a-zA-Z0-9._%+-]{2,}@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}\b"
)

os.makedirs(OUTPUT_DIR, exist_ok=True)

# ==============================
# LOGGING ESTRUTURADO
# ==============================
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
)
logger = logging.getLogger(__name__)

# ==============================
# SESSÃO COM RETRY
# ==============================
session = requests.Session()
retries = Retry(
    total=3,
    backoff_factor=1,
    status_forcelist=[502, 503, 504],
    allowed_methods=["GET"]
)
adapter = HTTPAdapter(max_retries=retries)
session.mount("http://", adapter)
session.mount("https://", adapter)

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
}

# ==============================
# FUNÇÕES AUXILIARES
# ==============================

def normalize_domain(url):
    parsed = urlparse(url)
    domain = parsed.netloc.lower()
    if domain.startswith("www."):
        domain = domain[4:]
    return domain


def is_valid_link(link, base_domain):
    parsed = urlparse(link)

    if parsed.scheme not in ["http", "https"]:
        return False

    if any(blocked in parsed.netloc for blocked in BLOCKED_DOMAINS):
        return False

    # bloqueia endpoints técnicos/administrativos que não ajudam na extração de email
    lower = link.lower()
    if any(p in lower for p in BLOCKED_PATH_SUBSTRINGS):
        return False

    return base_domain in parsed.netloc


def score_email(email):
    email = email.lower()
    if email.startswith("contato@"): return 5
    if email.startswith("geral@"): return 4
    if email.startswith("info@"): return 3
    if email.startswith("atendimento@"): return 3
    if email.startswith("admin@"): return 2
    return 1


def extract_emails_from_text(text, source_url, depth):
    results = []
    found = EMAIL_REGEX.findall(text)

    for email in found:
        email = email.lower().strip()

        # Filtros anti‑ruído (PDFs geram muito lixo)
        if len(email) < 6:
            continue

        if email.count("@") != 1:
            continue

        local, domain = email.split("@")

        # evita coisas tipo a@b.c ou sg.@n..
        if len(local) < 2:
            continue

        if ".." in email:
            continue

        if not re.search(r"\.[a-z]{2,}$", domain):
            continue

        if any(bad in email for bad in ["example", "test@", "no-reply"]):
            continue

        results.append({
            "email": email,
            "score": score_email(email),
            "source_url": source_url,
            "depth": depth
        })

    return results

# ==============================
# CRAWLER
# ==============================

def crawl_domain(base_url):
    base_domain = normalize_domain(base_url)

    # Denylist: evita crawl em domínios grandes/bloqueados
    if any(d == base_domain or base_domain.endswith("." + d) for d in DENYLIST_DOMAINS):
        logger.info(f"[{base_domain}] SKIPPED (denylist)")
        return []

    visited = set()
    queue = deque([(base_url, 0)])
    emails_found = []

    start_ts = time.time()
    pages_processed = 0
    consecutive_errors = 0
    consecutive_5xx = 0

    logger.info(f"[{base_domain}] Iniciando crawl")

    while queue:
        current_url, depth = queue.popleft()

        # hard limits para evitar travar em domínios gigantes
        if (time.time() - start_ts) > MAX_SECONDS_PER_DOMAIN:
            logger.warning(f"[{base_domain}] Abortando por limite de tempo ({MAX_SECONDS_PER_DOMAIN}s)")
            break
        if pages_processed >= MAX_PAGES_PER_DOMAIN:
            logger.warning(f"[{base_domain}] Abortando por limite de páginas ({MAX_PAGES_PER_DOMAIN})")
            break
        if len(queue) > MAX_QUEUE_SIZE:
            logger.warning(f"[{base_domain}] Abortando por fila grande demais (>{MAX_QUEUE_SIZE})")
            break
        if consecutive_errors >= MAX_CONSECUTIVE_ERRORS:
            logger.warning(f"[{base_domain}] Abortando por muitos erros consecutivos ({MAX_CONSECUTIVE_ERRORS})")
            break
        if consecutive_5xx >= MAX_CONSECUTIVE_5XX:
            logger.warning(f"[{base_domain}] Abortando por muitos 5xx consecutivos ({MAX_CONSECUTIVE_5XX})")
            break

        if depth > MAX_DEPTH:
            continue

        if current_url in visited:
            continue

        visited.add(current_url)

        try:
            response = session.get(current_url, headers=HEADERS, timeout=TIMEOUT)
        except Exception as e:
            consecutive_errors += 1
            logger.warning(f"Erro ao acessar {current_url}: {e}")
            continue

        # status handling
        if response.status_code >= 500:
            consecutive_errors += 1
            consecutive_5xx += 1
            continue

        if response.status_code != 200:
            consecutive_errors += 1
            consecutive_5xx = 0
            continue

        # sucesso
        consecutive_errors = 0
        consecutive_5xx = 0
        pages_processed += 1

        soup = BeautifulSoup(response.text, "html.parser")
        text = soup.get_text(" ", strip=True)

        emails_found.extend(
            extract_emails_from_text(text, current_url, depth)
        )

        for a in soup.find_all("a", href=True):
            href = urljoin(current_url, a["href"])

            if not is_valid_link(href, base_domain):
                continue

            if href in visited:
                continue

            next_item = (href, depth + 1)

            if any(path in href.lower() for path in PRIORITY_PATHS):
                queue.appendleft(next_item)
            else:
                queue.append(next_item)

        time.sleep(REQUEST_DELAY)

    return emails_found

# ==============================
# CSV CONSOLIDADO
# ==============================

def save_consolidated_csv(data, output_path):
    # Garante que o diretório exista
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=["domain", "email", "score", "source_url", "depth"]
        )
        writer.writeheader()
        writer.writerows(data)

    logger.info(f"CSV consolidado salvo em {output_path}")

# ==============================
# MAIN
# ==============================

def main():
    parser = argparse.ArgumentParser(description="Extrator de emails por domínio")
    parser.add_argument(
        "--urls-file",
        default="urls.txt",
        help="Arquivo contendo lista de URLs"
    )
    parser.add_argument(
        "--output",
        default=os.path.join(OUTPUT_DIR, "emails_consolidado.csv"),
        help="Arquivo CSV de saída"
    )
    args = parser.parse_args()

    urls_file = args.urls_file
    output_path = args.output

    if not os.path.exists(urls_file):
        logger.error(f"{urls_file} não encontrado.")
        return

    with open(urls_file, "r", encoding="utf-8") as f:
        urls = [line.strip() for line in f if line.strip()]

    logger.info(f"{len(urls)} domínios carregados.")

    all_results = []

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        future_to_url = {executor.submit(crawl_domain, url): url for url in urls}

        for future in as_completed(future_to_url):
            url = future_to_url[future]
            domain = normalize_domain(url)

            try:
                results = future.result()
            except Exception as e:
                logger.error(f"Erro no domínio {domain}: {e}")
                continue

            if not results:
                logger.info(f"[{domain}] Nenhum email encontrado")
                continue

            unique = {}
            for item in results:
                email = item["email"]
                if email not in unique or item["score"] > unique[email]["score"]:
                    unique[email] = item

            for item in unique.values():
                item["domain"] = domain
                all_results.append(item)

            logger.info(f"[{domain}] {len(unique)} emails encontrados")

    # Sempre salva CSV (mesmo vazio) para manter rastreabilidade
    save_consolidated_csv(all_results, output_path)

if __name__ == "__main__":
    main()