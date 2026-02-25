# 🏭 Ad Rock Prospect Engine — Pipeline Industrial de Prospecção B2B

Este projeto é um **pipeline industrial de prospecção B2B**, estruturado para operar com:

- Segmentação empresarial
- Enriquecimento via Google Maps API
- Extração inteligente de e-mails
- Classificação e priorização de empresas
- Controle incremental por hash
- Versionamento por execução (runs)
- Snapshot automático de inputs
- Lock file contra execução simultânea
- Relatório consolidado por run

O sistema opera exclusivamente sobre **fontes públicas (sites institucionais)**.
Não realiza scraping autenticado.
Não coleta dados privados.

---

# 🧠 Arquitetura do Pipeline Atual

```
linkedin_raw/                 → Dados exportados do LinkedIn
        ↓
linkedin_processor.py         → Limpeza, consolidação e segmentação
        ↓
linkedin_processed/segmentos/ → Segmentos organizados
        ↓
pipeline_extracao.py          → Engine principal industrial
        ↓
   ├── Enriquecimento (Google Maps)
   ├── Geração de URLs
   ├── Extração multi-thread
   ├── Classificação por score
   └── Consolidação final
```

---

# 📂 Estrutura Real do Projeto

```
simple_extrator_de_emails/
├── linkedin_raw/
│   ├── Company_Follows.csv
│   ├── Connections.csv
│   └── ImportedContacts.csv
│
├── linkedin_processed/
│   ├── segmentos/
│   ├── runs/
│   ├── empresas_segmentadas.csv
│   ├── empresas_consolidadas.csv
│   ├── empresas_priorizadas.csv
│   └── ...
│
├── csv_por_segmento/
├── csv_enriquecido/
├── output/
│
├── linkedin_processor.py
├── pipeline_extracao.py
├── extrator.py
├── enriquecer_sites_google_maps.py
├── gerar_urls.py
├── segmentar_empresas.py
│
├── Connections.csv
├── urls.txt
├── emails_extraidos.txt
│
├── requirements.txt
├── CHANGELOG.md
├── CONTRIBUTING.md
├── LICENSE
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
Cada execução cria uma pasta em:

```
linkedin_processed/runs/<run_id>/
```

Inclui:
- Logs estruturados
- Snapshot dos CSV de entrada
- Hash de integridade
- Relatório consolidado

---

## 3️⃣ Snapshot Automático
Antes de processar, o sistema salva cópia dos CSV utilizados na pasta da run.

Garante:
- Reprodutibilidade
- Auditoria
- Versionamento histórico

---

## 4️⃣ Controle Incremental por Hash
Cada CSV recebe hash SHA256.

O pipeline:
- Detecta alterações reais
- Processa apenas segmentos modificados
- Evita retrabalho

---

# ⚙️ Execução

Ativar ambiente virtual:

```bash
source venv/bin/activate
```

Instalar dependências:

```bash
pip3 install -r requirements.txt
```

Execução padrão:

```bash
python3 linkedin_processor.py
```

---

# 🧩 CLI Flags Disponíveis

Processar apenas um segmento:

```bash
python3 linkedin_processor.py --only-segment ONG
```

Ignorar enriquecimento:

```bash
python3 linkedin_processor.py --no-enrich
```

Modo simulação (sem executar extração):

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

# 🎯 Estratégia

O pipeline foi projetado para:

- Prospecção B2B segmentada
- Construção de base própria versionada
- Processamento incremental seguro
- Escalabilidade industrial
- Integração futura com CRM / automações

---

# 🚀 Próximas Evoluções

- Banco SQLite para controle persistente
- API interna REST
- Dashboard comercial
- Cache inteligente de enriquecimento
- Integração com sistema de outbound

---

# 👤 Autor

Rafael Marques Lins  
Ad Rock Digital Mkt  

🌐 https://adrock.com.br