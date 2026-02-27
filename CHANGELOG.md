# 📦 CHANGELOG — Ad Rock Prospect Engine

Todas as alterações relevantes deste projeto serão documentadas neste arquivo.

O formato segue um padrão inspirado em Keep a Changelog.

---

## [v4.2.0] — Email Extraction Hardening & Noise Control

### 🚀 Added
- Regex de e-mail mais restritiva com validação de TLD mínimo (>=2 caracteres)
- Filtro estrutural contra e-mails inválidos extraídos de PDF
- Validação de local-part mínima (>=2 caracteres)
- Bloqueio de múltiplos `@` no mesmo token
- Filtro contra domínios malformados (ex: `a@b.c`, `sg.@n..`)
- Sanitização adicional (`strip`, controle de tamanho mínimo)

### 🔧 Improved
- Redução drástica de falsos positivos em extrações provenientes de PDFs
- Qualidade significativamente maior no CSV consolidado
- Base pronta para futura camada de validação MX ou SMTP

---
## [v4.1.0] — Industrial Resilience Upgrade

### 🚀 Added
- StateManager persistente com controle diário de uso de API
- Controle de limite por execução (`EXECUTION_API_LIMIT`)
- Modo `--resume` com leitura de estado por segmento
- Modo `--skip-processed` para evitar retrabalho
- Checkpoint granular por segmento (persistência após cada etapa)
- Retry automático (3 tentativas) no enriquecimento
- Retry automático (3 tentativas) na extração
- Controle incremental baseado em hash do arquivo enriquecido
- Estrutura preparada para checkpoint granular por empresa
- Base arquitetural preparada para paralelização controlada por segmento

### 🔧 Improved
- Pipeline agora resiliente a interrupções (CTRL+C safe)
- Execuções longas podem ser retomadas sem retrabalho
- Governança real de custo operacional
- Base preparada para ambiente multi-thread e futura execução distribuída

---

## [v4.0.0] — Pipeline Industrial & Governança Operacional

### 🚀 Added
- Pipeline versionado por execução (`runs/YYYY-MM-DD_HH-MM-SS`)
- Snapshot automático dos CSV de entrada por run
- Hash SHA256 de inputs e outputs (controle de integridade)
- Lock file contra execução simultânea (`.pipeline.lock`)
- Controle incremental por segmento (baseado em hash)
- Execução por segmento via CLI (`--only-segment`)
- Flag `--no-enrich` para pular enriquecimento
- Flag `--dry-run` para simulação completa
- Relatório consolidado automático (`run_summary.csv`)
- Logs persistentes por execução (`logs/pipeline.log`)

### 🔧 Improved
- Resiliência contra schema drift (geração automática de `root_domain`)
- Estrutura modular preparada para execução headless em servidor
- Base arquitetural pronta para evolução SaaS interna

---

## [v3.0.0] — Prospect Engine Profissional

### 🚀 Added
- Crawler multi-thread com ThreadPoolExecutor
- CSV consolidado único (`output/emails_consolidado.csv`)
- Score de qualidade de e-mails (contato@ > geral@ > info@ > etc.)
- Metadados por e-mail (domain, source_url, depth)
- Logging estruturado com módulo logging
- Retry automático com backoff
- Controle de profundidade (MAX_DEPTH)
- Priorização de páginas estratégicas (contato, sobre, transparência)

### 🔧 Improved
- Deduplicação inteligente mantendo maior score
- Performance significativamente melhor com paralelização
- Estrutura preparada para pipeline completo de prospecção

---

## [v2.0.0] — Crawl Estruturado por Domínio

### 🚀 Added
- Crawl limitado ao domínio principal
- Filtro de domínios irrelevantes (redes sociais, drive, etc.)
- Output separado por domínio
- Organização da pasta `output/`

### 🔧 Improved
- Regex de e-mail refinada
- Filtro de e-mails inválidos (example, test, no-reply)
- Controle de timeout e delay entre requisições

---

## [v1.0.0] — Extrator Inicial

### 🚀 Added
- Extração básica de e-mails públicos via requests + BeautifulSoup
- Arquivo `emails_extraidos.txt` como saída
- Segmentação inicial por CSV (`segmentar_empresas.py`)
- Estrutura inicial de pipeline manual

---

## 🔮 Roadmap Futuro

- CLI unificado (engine único)
- Persistência incremental
- Modo headless (Playwright) para sites JS
- API interna para integração com bots da Ad Rock
- Dashboard de priorização comercial

---

Projeto mantido por:
Rafael Marques Lins  
Ad Rock Digital Mkt