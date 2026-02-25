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
# 🏭 Ad Rock Prospect Engine — Pipeline Industrial de Prospecção B2B

Este projeto evoluiu de um extrator simples para um **pipeline industrial de prospecção B2B**, com:

- Segmentação empresarial estruturada
- Enriquecimento via Google Maps API
- Geração automática de URLs
- Crawl multi-thread com scoring
- Controle incremental por hash
- Logs versionados por run
- Snapshot automático de inputs
- Lock file contra execução simultânea
- Relatório consolidado por execução

O sistema opera exclusivamente sobre **fontes públicas (sites institucionais)**.
Não realiza scraping autenticado.
Não coleta dados privados.

---

# 🧠 Arquitetura Industrial

```
Base (Connections / Empresas)
        ↓
linkedin_processor.py  (segmentação + consolidação)
        ↓
pipeline_extracao.py  (engine industrial)
        ↓
   ├── Enriquecimento (Google Maps)
   ├── Geração de URLs
   ├── Extração multi-thread
   ├── Classificação por score
   └── Consolidação final
```

---

# 📂 Estrutura Atual do Projeto

```
simple_extrator_de_emails/
├── linkedin_processor.py
├── pipeline_extracao.py
├── extrator.py
├── enriquecer_sites_google_maps.py
├── gerar_urls.py
├── requirements.txt
├── linkedin_processed/
│   ├── segmentos/
│   └── runs/
├── output/
├── logs/
├── .run.lock
└── README.md
```

---

# 🔒 Controles Industriais Implementados

## 1️⃣ Lock File
Arquivo `.run.lock` impede execução simultânea.

Evita:
- Corrupção de CSV
- Conflito de escrita
- Processamentos duplicados

---

## 2️⃣ Logs por Run
Cada execução gera:

```
linkedin_processed/runs/<run_id>/logs.txt
```

Contém:
- Timestamp
- Segmentos processados
- Quantidade de empresas
- Erros capturados
- Status final

---

## 3️⃣ Snapshot de Inputs
Antes de processar, o sistema salva automaticamente cópia dos CSV de entrada dentro da pasta da run.

Isso garante:
- Reprodutibilidade
- Auditoria
- Versionamento de base

---

## 4️⃣ Hash de Integridade
Cada CSV processado gera hash SHA256.

O pipeline:
- Detecta alterações reais
- Processa apenas segmentos modificados
- Evita retrabalho

---

# ⚙️ Execução via Engine Principal

Instalar dependências:

```bash
pip install -r requirements.txt
```

Execução padrão:

```bash
python3 linkedin_processor.py
```

---

# 🧩 CLI Flags Disponíveis

Processamento seletivo:

```bash
python3 linkedin_processor.py --only-segment ONG
```

Ignorar enriquecimento:

```bash
python3 linkedin_processor.py --no-enrich
```

Modo simulação (não executa extração):

```bash
python3 linkedin_processor.py --dry-run
```

---

# 📊 Relatório Consolidado da Run

Cada execução gera automaticamente:

```
linkedin_processed/runs/<run_id>/run_summary.csv
```

Contém:

- Segmento
- Empresas processadas
- Empresas enriquecidas
- Emails encontrados
- Status
- Hash da base

---

# 🎯 Estratégia de Uso

O pipeline foi projetado para:

- Prospecção B2B segmentada
- Construção de base própria versionada
- Processamento incremental seguro
- Escalabilidade industrial
- Integração futura com CRM / automações

---

# 🚀 Próximas Evoluções Planejadas

- Banco SQLite para controle de estado persistente
- API interna REST
- Dashboard de priorização comercial
- Integração com sistema de outbound
- Cache inteligente de enriquecimento

---

# 👤 Autor

Rafael Marques Lins  
Ad Rock Digital Mkt  

🌐 https://adrock.com.br