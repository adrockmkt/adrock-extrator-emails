import asyncio
import requests
from requests.adapters import HTTPAdapter, Retry
from bs4 import BeautifulSoup
import re
import time
from collections import defaultdict
from apify import Actor
from urllib.parse import urljoin, urlparse

EMAIL_REGEX = re.compile(r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+")

def extract_emails_from_url(url: str) -> set:
    """Baixa uma URL e extrai e-mails do texto renderizado (sem JS)."""
    emails = set()
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "pt-BR,pt;q=0.9,en;q=0.8",
        }
        response = session.get(url, headers=headers, timeout=15, allow_redirects=True)
        status = getattr(response, "status_code", None)
        if status != 200:
            Actor.log.warning(f"Erro ao acessar {url}: Status {status}")
            return emails

        soup = BeautifulSoup(response.text, "html.parser")

        # Remove scripts/styles para reduzir ruído
        for tag in soup(["script", "style", "noscript"]):
            tag.decompose()

        text = soup.get_text(" ", strip=True)
        found_emails = EMAIL_REGEX.findall(text)
        emails.update(found_emails)

    except Exception as e:
        try:
            Actor.log.warning(f"Exceção ao processar {url}: {e}")
        except Exception:
            print(f"Exceção ao processar {url}: {e}")

    return emails

async def main() -> None:
    # Apify Python SDK uses async APIs; use the Actor context manager
    async with Actor:
        input_data = await Actor.get_input() or {}

        # Debug: ajuda a entender como o Apify está entregando o INPUT
        try:
            Actor.log.info(f"INPUT keys recebidas: {list(input_data.keys())}")
        except Exception:
            pass

        def _coerce_urls(value):
            """Converte possíveis formatos de entrada em uma lista de strings URLs."""
            if value is None:
                return []

            # Caso 1: lista de strings
            if isinstance(value, list):
                urls = []
                for item in value:
                    if isinstance(item, str):
                        urls.append(item)
                    # Caso 2: lista de objetos no formato startUrls do Apify
                    elif isinstance(item, dict) and isinstance(item.get('url'), str):
                        urls.append(item['url'])
                return urls

            # Caso 3: string única (permitir)
            if isinstance(value, str):
                return [value]

            # Caso 4: objeto com chave 'url'
            if isinstance(value, dict) and isinstance(value.get('url'), str):
                return [value['url']]

            return []

        # Aceita múltiplas chaves (para evitar mismatch entre schema e código)
        candidate_keys = [
            'urls',
            'url',
            'startUrls',
            'start_urls',
            'listaDeUrls',
            'lista_de_urls',
            'listaDeURLs',
            'lista_de_URLs',
        ]

        base_urls = []
        for k in candidate_keys:
            if k in input_data:
                base_urls = _coerce_urls(input_data.get(k))
                if base_urls:
                    break

        if not base_urls:
            Actor.log.error(
                "Erro: campo obrigatório de URLs não informado. "
                "Preencha a lista de URLs no input (ex.: {'urls': ['https://exemplo.com/']})."
            )
            await Actor.exit(exit_code=1)
            return

        # Normaliza / deduplica URLs
        base_urls = [u.strip() for u in base_urls if isinstance(u, str) and u.strip()]
        base_urls = list(dict.fromkeys(base_urls))

        if not base_urls:
            Actor.log.error("Erro: lista de URLs está vazia após normalização.")
            await Actor.exit(exit_code=1)
            return

        Actor.log.info(f"{len(base_urls)} URL(s) recebida(s) como entrada via Apify.")

        def _normalize_link(base: str, href: str) -> str | None:
            if not href:
                return None
            href = href.strip()
            if href.startswith("mailto:") or href.startswith("tel:"):
                return None
            if href.startswith("#"):
                return None
            abs_url = urljoin(base, href)
            # Remove fragment
            parsed = urlparse(abs_url)
            if not parsed.scheme.startswith("http"):
                return None
            return parsed._replace(fragment="").geturl()

        def _same_site(u1: str, u2: str) -> bool:
            try:
                h1 = urlparse(u1).netloc.lower()
                h2 = urlparse(u2).netloc.lower()
                # Trata www.
                h1 = h1[4:] if h1.startswith("www.") else h1
                h2 = h2[4:] if h2.startswith("www.") else h2
                return h1 == h2
            except Exception:
                return False

        emails_by_company = {}
        total_emails = 0

        for base_url in base_urls:
            # Sempre tenta extrair e-mails da URL base também
            base_emails = extract_emails_from_url(base_url)
            if base_emails:
                emails_by_company[base_url] = set(base_emails)

            try:
                headers = {
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
                    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                    "Accept-Language": "pt-BR,pt;q=0.9,en;q=0.8",
                }
                response = session.get(base_url, headers=headers, timeout=15, allow_redirects=True)
            except Exception as e:
                Actor.log.warning(f"Não foi possível acessar a página principal: {base_url} -> {e}")
                continue

            if response.status_code != 200:
                Actor.log.warning(f"Falha ao acessar a página principal: {base_url} (Status {response.status_code})")
                continue

            soup = BeautifulSoup(response.text, "html.parser")

            # Coleta links internos (mesmo domínio). Isso funciona tanto para links absolutos quanto relativos.
            internal_links = set()
            for a in soup.find_all("a", href=True):
                normalized = _normalize_link(base_url, a.get("href"))
                if not normalized:
                    continue
                if _same_site(base_url, normalized):
                    # Evita assets comuns
                    if any(normalized.lower().endswith(ext) for ext in (".jpg", ".jpeg", ".png", ".gif", ".svg", ".webp", ".pdf", ".zip")):
                        continue
                    internal_links.add(normalized)

            # Se não achou nada interno, ao menos mantém a própria URL base
            if not internal_links:
                internal_links.add(base_url)

            Actor.log.info(f"[{base_url}] Encontrados {len(internal_links)} link(s) internos para varrer.")

            for link in sorted(internal_links):
                Actor.log.info(f"Processando: {link}")
                emails = extract_emails_from_url(link)
                if emails:
                    if link not in emails_by_company:
                        emails_by_company[link] = set()
                    emails_by_company[link].update(emails)
                time.sleep(0.5)

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
            Actor.log.info("Nenhum e-mail encontrado para as URLs informadas.")
            return

        # Envia tudo para o dataset (push em lote para melhor performance)
        await Actor.push_data(results)

        # Exporta CSV para facilitar download (Key-Value Store)
        try:
            import pandas as pd
            df = pd.DataFrame(results)
            csv_text = df.to_csv(index=False)
            await Actor.set_value("emails.csv", csv_text, content_type="text/csv")
            Actor.log.info("CSV gerado e salvo como Key-Value Store item: emails.csv")
        except Exception as e:
            Actor.log.warning(f"Não foi possível gerar CSV: {e}")

        Actor.log.info(f"Emails extraídos foram enviados para o dataset do Apify. Total: {total_emails}")

if __name__ == "__main__":
    asyncio.run(main())