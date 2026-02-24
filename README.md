# 📨 Extrator de E-mails de Sites via Python

Este projeto realiza a **extração de e-mails públicos a partir de sites institucionais**, utilizando um script em Python.  
O fluxo foi pensado para **prospecção B2B, curadoria de contatos e geração de bases**, sempre a partir de **fontes públicas**.

O extrator **não coleta dados do LinkedIn** nem realiza scraping autenticado — ele opera exclusivamente sobre **URLs de sites** previamente organizadas.

---

## 🧠 Visão geral do fluxo

O projeto hoje funciona em **duas etapas independentes**:

### 1️⃣ Segmentação e organização das empresas
- A partir de um CSV de empresas (ex.: conexões do LinkedIn exportadas)
- As empresas são **classificadas por segmento**
- São gerados **CSVs separados por setor**
- Esses CSVs servem como base para gerar listas de URLs

Script responsável:
```
segmentar_empresas.py
```

> Esta etapa **não faz scraping**. Apenas trata e organiza dados.

---

### 2️⃣ Extração de e-mails a partir de sites
- O usuário gera um `urls.txt` (uma URL por linha) a partir dos CSVs segmentados
- O script acessa os sites e percorre links internos
- E-mails públicos encontrados são extraídos e deduplicados

Script responsável:
```
extrator.py
```

---

## 📁 Estrutura do projeto

```
simple_extrator_de_emails/
├── extrator.py              # Script principal de extração
├── segmentar_empresas.py    # Segmentação de empresas por setor
├── urls.txt                 # URLs de entrada (gerado pelo usuário)
├── emails_extraidos.txt     # Resultado da extração (runtime)
├── README.md                # Documentação
```

> Arquivos como `emails_extraidos.txt`, CSVs de entrada e pastas de saída são considerados **runtime/local** e podem estar ignorados via `.gitignore`.

---

## 🚀 Execução

### Requisitos
- Python 3.9+
- Dependências listadas em `requirements.txt`

Instalação:
```bash
pip install -r requirements.txt
```

---

### Etapa 1 — Segmentação de empresas
```bash
python3 segmentar_empresas.py
```

Saída:
- CSVs organizados por segmento (uso interno)

---

### Etapa 2 — Extração de e-mails
1. Gere o arquivo `urls.txt` (uma URL por linha)
2. Execute:
```bash
python3 extrator.py
```

Os e-mails encontrados serão registrados em `emails_extraidos.txt`, com controle de duplicação.

---

## 🧠 Observações importantes

- Apenas e-mails **publicamente disponíveis** são coletados
- O script evita duplicações por link e por histórico
- Sites com proteção anti-bot podem bloquear a extração
- O arquivo de saída é acumulativo, ideal para execuções recorrentes
- O uso é voltado para **B2B / contatos institucionais**

---

## ✉️ Autor

Rafael Marques Lins  
Ad Rock Digital Mkt  

📧 rafael@adrock.com.br  
📲 WhatsApp: https://wa.me/5541991255859  
🌐 https://adrock.com.br

# 📨 Ad Rock Prospect Engine — Extrator e Enriquecedor de Empresas

Este projeto evoluiu de um simples extrator de e-mails para um **pipeline estruturado de prospecção B2B**, combinando:

- Segmentação de empresas
- Enriquecimento via Google Maps API
- Geração automática de URLs
- Crawl inteligente multi-thread
- Classificação de e-mails por score
- Exportação consolidada em CSV

O sistema opera exclusivamente sobre **fontes públicas** (sites institucionais).

---

# 🧠 Arquitetura do Pipeline

O fluxo atual funciona em múltiplas etapas encadeadas:

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

# 📂 Estrutura Atual do Projeto

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

Colunas:

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
- Extração apenas de dados públicos
- Organização por segmento

Não realiza scraping autenticado.
Não coleta dados privados.

---

# 🚀 Próximos Evolutivos (Roadmap Interno)

- CLI unificado (engine único)
- Modo headless (Playwright)
- Persistência incremental
- API interna para integração com outros bots Ad Rock
- Dashboard de priorização comercial

---

# 👤 Autor

Rafael Marques Lins  
Ad Rock Digital Mkt  

🌐 https://adrock.com.br