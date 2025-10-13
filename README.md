# 📨 Extrator de E-mails de Sites via Python + Apify

Este projeto automatiza a extração de e-mails públicos a partir de sites coletados previamente via Google Maps, utilizando a plataforma [Apify](https://apify.com/) e um script em Python. Ideal para curadoria de contatos institucionais, prospecção ou base de dados.

---

## ⚙️ Como funciona

1. O usuário coleta URLs de sites através de scrapers do Apify (ex: Google Maps Scraper).
2. Essas URLs são salvas no arquivo `urls.txt`, uma por linha.
3. O script `extrator.py` lê o arquivo, acessa os sites e percorre todos os links internos em busca de e-mails.
4. Os e-mails encontrados são salvos no arquivo `emails_extraidos.txt`, sem duplicações.

---

## 📁 Estrutura do projeto

```
extrator_de_emails/
├── extrator.py              # Script principal de extração
├── urls.txt                 # Lista de URLs de entrada (uma por linha)
├── emails_extraidos.txt     # Resultado acumulado da extração
└── README.md                # Este arquivo
```

---

## 🚀 Executando

1. Instale as dependências:
```bash
pip install -r requirements.txt
```

2. Insira as URLs em `urls.txt` (uma por linha).

3. Execute o script:
```bash
python3 extrator.py
```

Os e-mails encontrados serão salvos no arquivo `emails_extraidos.txt`.

---

## 🧠 Observações

- O script evita e-mails duplicados, tanto por link quanto por histórico.
- Sites com bloqueios para bots podem impedir extração direta.
- O arquivo de saída é acumulativo, ideal para execuções recorrentes.

---

## ✉️ Contato

Desenvolvido por Rafael Marques Lins — Ad Rock Digital Mkt  
📧 rafael@adrock.com.br  
📲 WhatsApp: [Clique aqui para conversar](https://wa.me/5541991255859)  
🌐 https://adrock.com.br

---
