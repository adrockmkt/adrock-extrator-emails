# 🏭 Ad Rock Prospect Engine — Pipeline Industrial de Prospecção B2B

Este projeto é um **pipeline industrial de prospecção B2B**, estruturado para operar com:

- Segmentação empresarial
- Enriquecimento via Google Maps API
- Extração inteligente de e-mails
- Classificação e priorização de empresas
- Controle incremental por hash
- Cache persistente em SQLite para enriquecimento
- Governança financeira por execução
- Log financeiro auditável
- Controle de custo por segmento
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
data/segmented/               → Segmentos organizados
        ↓
run_pipeline.py (orquestrador)
        ↓
   ├── segmentar_empresas.py
   ├── enriquecer_sites_google_maps.py
   ├── gerar_urls.py
   ├── extrator.py
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

## 5️⃣ State Manager Persistente

O pipeline agora mantém estado persistente em arquivo JSON.

Controla:

- Uso diário de API
- Limite por execução
- Status por segmento
- Hash do input processado
- Controle incremental real
- Preparação para checkpoint granular por empresa

Permite retomada segura mesmo após:

- Interrupção manual (CTRL+C)
- Queda de energia
- Timeout de API
- Erro parcial de segmento

---

## 6️⃣ Retry Automático

Enriquecimento e Extração possuem:

- Até 3 tentativas automáticas por segmento
- Persistência de estado em falha definitiva
- Continuidade do pipeline mesmo com erro parcial

O sistema nunca trava a execução inteira por falha isolada.

---

## 7️⃣ Governança de API

Controle industrial implementado:

- `DAILY_API_LIMIT`
- `EXECUTION_API_LIMIT`
- Contador incremental de chamadas
- Bloqueio automático ao atingir limite

---

### 💰 Governança Financeira (Google Maps)

O módulo de enriquecimento agora possui controle financeiro industrial:

- Cache persistente em SQLite (`data/enrichment_cache.db`)
- Flag `--force-refresh` para ignorar cache
- Limite de chamadas pagas por execução (`--max-api-calls`)
- Cálculo estimado de custo em USD por execução
- Breakdown de custo por segmento
- Log financeiro persistente (`data/finance_log.csv`)

O sistema:

- Nunca realiza chamadas duplicadas
- Evita reprocessamento desnecessário
- Permite execução controlada por orçamento
- Garante previsibilidade de custo operacional

Resumo financeiro exibido ao final de cada execução:

- Total de chamadas pagas
- Custo estimado total
- Custo estimado por segmento

---

## 8️⃣ Arquitetura Preparada para Paralelização

A estrutura atual já está preparada para:

- Processamento paralelo por segmento
- Thread pool controlado
- Escalonamento futuro em ambiente distribuído

Atualmente executa de forma sequencial controlada.

---

## 9️⃣ Enterprise Scoring & Segment Intelligence

O pipeline agora utiliza modelo de **score contínuo de porte empresarial** ao invés de bloqueio binário.

### 🔢 Enterprise Score

Cada empresa recebe um `enterprise_score` calculado com base em:

- Nome da empresa
- Palavras-chave corporativas
- Indícios de small business
- Lista dinâmica Fortune 500 (`fortune500.json`)
- Domínio enriquecido (camada 2)

O bloqueio ocorre apenas se o score ultrapassar o threshold do modo escolhido.

---

### 🎛️ Modos Operacionais

O comportamento do filtro pode ser ajustado via CLI:

#### Conservative (default)
Mais restritivo. Bloqueia empresas com score ≥ 6.0

```bash
python3 linkedin_processor.py --mode conservative
```

#### Aggressive
Mais permissivo. Bloqueia apenas empresas com score ≥ 9.0

```bash
python3 linkedin_processor.py --mode aggressive
```

---

### 📄 Log Auditável de Bloqueios

Cada run gera:

```
linkedin_processed/runs/<run_id>/enterprise_blocks.csv
```

Colunas:
- timestamp
- segment
- company_name
- reason (name_score | domain_rule)
- enterprise_score

Permite:
- Auditoria de decisões
- Ajuste fino de threshold
- Análise estatística futura

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

---

## 🚀 Execução Principal (Orquestrador Industrial)

```bash
python run_pipeline.py
```

O sistema perguntará interativamente qual segmento deseja executar.

---

# 🏗️ run_pipeline.py — Orquestrador Industrial

O `run_pipeline.py` é o ponto central de execução do sistema.

Responsabilidades:

- Perguntar interativamente o segmento
- Criar diretório versionado em `runs/`
- Executar cada etapa sequencialmente
- Interromper execução em caso de falha crítica
- Garantir consistência entre etapas

Fluxo interno:

1. Segmentação
2. Enriquecimento
3. Geração de URLs
4. Extração de emails
5. Consolidação final

Cada execução é isolada por timestamp.

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

- Calibração estatística automática de thresholds (baseada em histórico de bloqueios)
- Checkpoint granular por empresa (nível enterprise)
- Paralelização controlada por segmento
- Limitação direta por orçamento (`--max-budget`)
- Dashboard financeiro por segmento
- Monitoramento automático de ROI por campanha de prospecção
- API interna REST
- Dashboard comercial
- Cache inteligente de enriquecimento
- Integração com sistema de outbound

---

# 👤 Autor

Rafael Marques Lins  
Ad Rock Digital Mkt  

🌐 https://adrock.com.br