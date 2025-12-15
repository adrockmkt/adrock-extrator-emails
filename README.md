# 📨 Ad Rock Email Extractor via Apify

## 🧾 Description (EN)

**Ad Rock Email Extractor** is an Apify Actor (Python) that crawls one or more websites and extracts **public email addresses** found on the main pages and internal links.

It is designed for **outreach, lead generation, NGO/association research, and contact database building**.

## ✅ Key Features

- Accepts **one or more URLs** as input
- Crawls internal pages (same domain) to discover more emails
- Extracts and validates email patterns
- **Deduplicates** emails
- Saves results to the run’s **Apify Dataset** (ready for **CSV export**)
- Adds a **group** field (1–50, 51–100, …) to help organize large exports

## ⚙️ How It Works

1. You provide one or more URLs in the Actor input.
2. The Actor visits each website and crawls internal links.
3. All discovered emails are pushed to the run Dataset as items:

```json
{
  "email": "contato@exemplo.org",
  "url": "https://exemplo.org/contato",
  "group": "1-50"
}
```

## 📁 Project Structure

```text
extrator_de_emails/
├── extrator.py              # Main extraction script (used on Apify)
├── input_schema.json        # Apify input UI schema
├── output_schema.json       # Output schema (Dataset item shape)
├── requirements.txt         # Python dependencies
├── Dockerfile               # Container for Apify builds
├── apify.json               # Actor metadata
└── README.md
```

## 🚀 Running on Apify

1. Open Apify Console and create an Actor from this repository.
2. Provide your URLs in the input field.
3. Click **Start**.
4. Open **Dataset → default** to see results and export to **CSV/JSON**.

## 🧠 Notes & Limitations

- Websites that block bots, rate-limit heavily, or require authentication may return fewer results.
- The Actor extracts **only publicly available** emails found in HTML/text.
- For large sites, consider limiting crawl depth/links (if you add those parameters in the future).

## ✉️ Contact

Developed by Rafael Marques Lins — Ad Rock Digital Mkt  
📧 rafael@adrock.com.br  
📲 WhatsApp: [Chat on WhatsApp](https://wa.me/5541991255859)  
🌐 https://adrock.com.br

---

# 📨 Ad Rock Extrator de E-mails via Apify

## 🧾 Descrição (PT-BR)

O **Ad Rock Email Extractor** é um Actor do Apify (Python) que varre um ou mais sites e extrai **endereços de e-mail públicos** encontrados na página principal e em links internos.

É ideal para **prospecção, geração de leads, pesquisa de ONGs/associações e construção de base de contatos**.

## ✅ Principais recursos

- Aceita **uma ou mais URLs** como entrada
- Percorre links internos (mesmo domínio) para encontrar mais e-mails
- Extrai e valida padrões de e-mail
- **Remove duplicados** automaticamente
- Salva os resultados no **Dataset do Apify** (pronto para exportar em **CSV**)
- Inclui o campo **group** (1–50, 51–100, …) para facilitar organização no export

## ⚙️ Como funciona

1. Você informa uma ou mais URLs no input do Actor.
2. O Actor acessa os sites e percorre links internos.
3. Os e-mails encontrados são enviados ao Dataset da execução no formato:

```json
{
  "email": "contato@exemplo.org",
  "url": "https://exemplo.org/contato",
  "group": "1-50"
}
```

## 🚀 Executando no Apify

1. Acesse o Apify Console e crie um Actor a partir deste repositório.
2. Informe as URLs no input.
3. Clique em **Start**.
4. Acesse **Dataset → default** para ver os resultados e exportar em **CSV/JSON**.

## 🧠 Observações

- Sites que bloqueiam bots, impõem rate limit, ou exigem login podem retornar menos resultados.
- O Actor extrai apenas e-mails **publicamente disponíveis** no HTML/texto.

## ✉️ Contato

Desenvolvido por Rafael Marques Lins — Ad Rock Digital Mkt  
📧 rafael@adrock.com.br  
📲 WhatsApp: [Clique aqui para conversar](https://wa.me/5541991255859)  
🌐 https://adrock.com.br
