import requests
from requests.adapters import HTTPAdapter, Retry
from bs4 import BeautifulSoup
import re
import time
import os

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

def main():
    with open("urls.txt", "r", encoding="utf-8") as file:
        base_urls = [line.strip() for line in file if line.strip()]
    print(f"{len(base_urls)} URLs carregadas de 'urls.txt'")

    emails_by_company = {}

    for base_url in base_urls:
        try:
            headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36"}
            response = session.get(base_url, headers=headers, timeout=10)
        except Exception as e:
            print(f"Não foi possível acessar a página principal: {base_url} -> {e}")
            continue

        if response.status_code != 200:
            print(f"Falha ao acessar a página principal: {base_url}")
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

    # Salvando os resultados em um arquivo de texto
    with open("emails_extraidos.txt", "a", encoding="utf-8") as f:
        if f.tell() == 0:
            f.write("Emails encontrados:\n")

        existing_emails = set()
        if os.path.exists("emails_extraidos.txt"):
            with open("emails_extraidos.txt", "r", encoding="utf-8") as old_file:
                for line in old_file:
                    found = re.findall(r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+", line)
                    existing_emails.update(found)

        for company_url, emails in emails_by_company.items():
            unique_emails = [email for email in emails if email not in existing_emails]
            if unique_emails:
                f.write(f"{company_url} -> {', '.join(unique_emails)}\n")
                existing_emails.update(unique_emails)

    print("\nEmails extraídos foram salvos em 'emails_extraidos.txt'.")

if __name__ == "__main__":
    main()