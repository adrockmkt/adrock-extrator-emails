import asyncio
import requests
from requests.adapters import HTTPAdapter, Retry
from bs4 import BeautifulSoup
import re
import time
from collections import defaultdict
from apify import Actor

# Configura uma sessão com retries
session = requests.Session()
retries = Retry(
    total=3,                # Tenta até 3 vezes
    backoff_factor=1,       # Aguarda 1 segundo entre as tentativas (pode ser incrementado exponencialmente)
    status_forcelist=[502, 503, 504],  # Tenta novamente em certos status HTTP
    allowed_methods=["GET"] # Métodos que receberão retry
)
adapter = HTTPAdapter(max_retries=retries)
session.mount("http://", adapter)
session.mount("https://", adapter)

def extract_emails_from_url(url):
    emails = set()
    try:
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36"}
        # Use a sessão com retry configurado
        response = session.get(url, headers=headers, timeout=10)
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            text = soup.get_text()
            found_emails = re.findall(r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+", text)
            emails.update(found_emails)
        else:
            print(f"Erro ao acessar {url}: Status {response.status_code}")
    except Exception as e:
        print(f"Exceção ao processar {url}: {e}")
    return emails

async def main() -> None:
    # Apify Python SDK uses async APIs; use the Actor context manager
    async with Actor:
        input_data = await Actor.get_input() or {}

        base_urls = input_data.get('urls')
        if not base_urls or not isinstance(base_urls, list):
            await Actor.fail("Erro: campo obrigatório 'urls' não informado (lista de URLs).")
            return

        # Normaliza / deduplica URLs
        base_urls = [u.strip() for u in base_urls if isinstance(u, str) and u.strip()]
        base_urls = list(dict.fromkeys(base_urls))

        if not base_urls:
            await Actor.fail("Erro: campo 'urls' está vazio após normalização.")
            return

        print(f"{len(base_urls)} URLs recebidas como entrada via Apify.")

        emails_by_company = {}
        total_emails = 0

        for base_url in base_urls:
            try:
                headers = {
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36"
                }
                response = session.get(base_url, headers=headers, timeout=10)
            except Exception as e:
                print(f"Não foi possível acessar a página principal: {base_url} -> {e}")
                continue

            if response.status_code != 200:
                print(f"Falha ao acessar a página principal: {base_url} (Status {response.status_code})")
                continue

            soup = BeautifulSoup(response.text, 'html.parser')

            company_links = set()
            for a in soup.find_all('a', href=True):
                href = a['href']
                if href.startswith("http") and "associadas-abong" not in href:
                    company_links.add(href)

            print(f"[{base_url}] Foram encontrados {len(company_links)} links para páginas de empresas.")

            for link in company_links:
                print(f"Processando: {link}")
                emails = extract_emails_from_url(link)
                if emails:
                    emails_by_company[link] = emails
                time.sleep(1)

        def get_group_by_index(index: int, step: int = 50) -> str:
            start = (index // step) * step + 1
            end = start + step - 1
            return f"{start}-{end}"

        results = []
        index = 0

        # Ordena para ter saída estável (ajuda testes / comparações)
        for company_url in sorted(emails_by_company.keys()):
            for email in sorted(emails_by_company[company_url]):
                group = get_group_by_index(index)
                results.append({
                    "url": company_url,
                    "email": email,
                    "group": group,
                })
                total_emails += 1
                index += 1

        if not results:
            print("Nenhum e-mail encontrado para as URLs informadas.")
            return

        # Envia tudo para o dataset (push em lote para melhor performance)
        await Actor.push_data(results)

        print(f"\nEmails extraídos foram enviados para o dataset do Apify. Total: {total_emails}")

if __name__ == "__main__":
    asyncio.run(main())