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
