# 📨 Ad Rock Prospect Engine — Extrator e Enriquecedor de Empresas

Este projeto é um **pipeline estruturado de prospecção B2B**, combinando:

- Segmentação de empresas
- Enriquecimento via Google Maps API
- Geração automática de URLs
- Crawl inteligente multi-thread
- Classificação de e-mails por score
- Exportação consolidada em CSV

O sistema opera exclusivamente sobre **fontes públicas** (sites institucionais).
Não realiza scraping autenticado.
Não coleta dados privados.

---

# 🧠 Arquitetura do Pipeline

```
Connections.csv / Base de Empresas
        ↓
segmentar_empresas.py
        ↓
csv_por_segmento/
        ↓
enriquecer_sites_google_maps.py
        ↓
csv_enriquecido/
        ↓
gerar_urls.py
        ↓
urls.txt
        ↓
extrator.py (v3)
        ↓
output/emails_consolidado.csv
```

---

# 📂 Estrutura do Projeto

```
simple_extrator_de_emails/
├── segmentar_empresas.py
├── enriquecer_sites_google_maps.py
├── gerar_urls.py
├── extrator.py
├── Connections.csv
├── csv_por_segmento/
├── csv_enriquecido/
├── output/
├── urls.txt
├── requirements.txt
└── README.md
```

---

# 🔎 Módulos

## 1️⃣ segmentar_empresas.py
Classifica empresas por segmento a partir de um CSV base.

Saída:
```
csv_por_segmento/*.csv
```

---

## 2️⃣ enriquecer_sites_google_maps.py
Utiliza Google Maps API (Places) para:

- Descobrir website institucional
- Validar correspondência
- Gerar CSV enriquecido

Requer variável de ambiente:

```
GOOGLE_MAPS_API_KEY
```

Saída:
```
csv_enriquecido/*.csv
```

---

## 3️⃣ gerar_urls.py
Extrai os domínios válidos dos CSVs enriquecidos e gera:

```
urls.txt
```

---

## 4️⃣ extrator.py (v3 — versão profissional)
Crawler multi-thread com:

- Retry automático
- Controle de profundidade
- Filtro de domínios irrelevantes
- Priorização de páginas estratégicas
- Score de qualidade de e-mail
- Logging estruturado
- CSV consolidado final

Saída:
```
output/emails_consolidado.csv
```

Colunas do CSV final:

- domain
- email
- score
- source_url
- depth

---

# ⚙️ Execução Completa

Instalar dependências:

```bash
pip install -r requirements.txt
```

Pipeline padrão:

```bash
python3 segmentar_empresas.py
python3 enriquecer_sites_google_maps.py
python3 gerar_urls.py
python3 extrator.py
```

---

# 📊 Estratégia de Uso

Este projeto foi estruturado para:

- Prospecção B2B segmentada
- Construção de base própria
- Enriquecimento automatizado
- Organização por segmento
- Geração de lista pronta para outbound

---

# 🚀 Roadmap Interno

- CLI unificado (engine único)
- Persistência incremental
- Modo headless (Playwright) para sites JS
- API interna para integração com outros bots Ad Rock
- Dashboard de priorização comercial

---

# 👤 Autor

Rafael Marques Lins  
Ad Rock Digital Mkt  

🌐 https://adrock.com.br