# 📦 CHANGELOG — Ad Rock Prospect Engine

Todas as alterações relevantes deste projeto serão documentadas neste arquivo.

O formato segue um padrão inspirado em Keep a Changelog.

---

## [v4.4.0] — Financial Governance & Google Maps Cost Control

### 🚀 Added
- Cache persistente em SQLite para enriquecimento via Google Maps (`data/enrichment_cache.db`)
- Flag `--force-refresh` para ignorar cache quando necessário
- Controle de limite de chamadas pagas (`--max-api-calls`)
- Cálculo estimado de custo por execução (USD)
- Breakdown financeiro por segmento
- Log financeiro persistente (`data/finance_log.csv`)

### 🔧 Improved
- Eliminação definitiva de chamadas duplicadas na API do Google Maps
- Redução drástica de risco de sobrecusto em execuções longas
- Execução previsível com governança financeira real
- Pipeline preparado para operação controlada em ambiente de produção

### 💰 Operational Impact
- Visibilidade clara de custo por rodada de execução
- Base para futura limitação por orçamento (`--max-budget`)
- Estrutura pronta para monetização interna como módulo premium

## [v4.3.1] — Pipeline Argument Fix & URL Generator Stabilization

### 🛠 Fixed
- Correção de erro crítico no `gerar_urls.py` que utilizava caminho hardcoded (`csv_enriquecido/...`)
- Ajuste definitivo para uso exclusivo de argumento CLI (`python gerar_urls.py <caminho_csv_enriquecido>`)
- Eliminação de dependência de diretório fixo no estágio de geração de URLs
- Estabilização da integração entre `run_pipeline.py` e `gerar_urls.py`

### 🔧 Improved
- Maior previsibilidade no fluxo por execução versionada (`runs/`)
- Redução de falhas intermitentes em ambientes com múltiplos segmentos
- Pipeline mais consistente para futura execução headless ou server-side

---

## [v4.3.0] — Enterprise Scoring & Segment Intelligence Upgrade

### 🚀 Added
- Score contínuo de porte empresarial (`enterprise_score`) substituindo bloqueio binário
- Threshold configurável por modo (`--mode conservative | aggressive`)
- Log estruturado de bloqueios por execução (`enterprise_blocks.csv`)
- Integração com lista dinâmica `fortune500.json`
- Camada dupla de bloqueio: nome + domínio enriquecido
- Auditoria completa por segmento e score

### 🔧 Improved
- Redução de falsos positivos no filtro de grandes empresas
- Controle mais fino de risco de travamento por big corp
- Governança auditável de decisões de bloqueio
- Execução por segmento mais tolerante (aceita plural e variações simples)
- Base preparada para futura calibração estatística de thresholds

### 🧠 Architectural Impact
- Pipeline evolui de heurística simples para modelo de scoring
- Preparação para futura camada de aprendizado baseado em dados históricos
- Estrutura pronta para produto SaaS interno com regras configuráveis

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