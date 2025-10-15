
# 📨 Ad Rock Email Extractor via Apify

## 🧾 Description (EN)

This project automates the extraction of public email addresses from websites using the [Apify](https://apify.com/) platform and a Python script. Ideal for outreach, lead generation, and data collection.

## ⚙️ How It Works

1. The user enters one or more URLs in the Apify interface.
2. The Actor visits each provided website and crawls internal links.
3. All valid email addresses found are automatically saved to the run's Dataset.
4. The emails are saved to the Apify Dataset and grouped into ranges (0–50, 51–100, 101–200, etc.).

## 📁 Project Structure

```
extrator_de_emails/
├── extrator.py              # Main extraction script (used on Apify)
├── input_schema.json        # Defines the visual interface for Apify input
├── apify.json               # Actor configuration for Apify
├── requirements.txt         # Python dependencies
├── Dockerfile               # Container for running on Apify
├── ray-so-export.png        # Project illustration image
├── LICENSE                  # License file
├── CONTRIBUTING.md          # Contribution guide
└── README.md                # This file
```

## 🚀 Running on Apify

1. Go to [Apify Console](https://console.apify.com/).
2. Create or clone the Actor with the code from this repository.
3. Paste one or more URLs into the "List of URLs" field.
4. Click "Start" and the system will extract valid emails.
5. Access the results in "Dataset" > "default" and export to CSV, JSON, etc.

## 🧠 Notes

- The system avoids duplicate email addresses.
- Sites that block bots or require authentication may return no results.
- Apify Dataset keeps the full history of previous runs.

## ✉️ Contact

Developed by Rafael Marques Lins — Ad Rock Digital Mkt  
📧 rafael@adrock.com.br  
📲 WhatsApp: [Chat on WhatsApp](https://wa.me/5541991255859)  
🌐 https://adrock.com.br

# 📨 Ad Rock Extrator de E-mails via Apify

Este projeto automatiza a extração de e-mails públicos a partir de sites coletados previamente via Google Maps, utilizando a plataforma [Apify](https://apify.com/) e um script em Python. Ideal para curadoria de contatos institucionais, prospecção ou base de dados.

---

## ⚙️ Como funciona

1. O usuário insere uma ou mais URLs diretamente na interface do Apify.
2. O Actor acessa cada site informado e percorre seus links internos.
3. Todos os e-mails válidos encontrados são salvos automaticamente no Dataset da execução.
4. Os e-mails são organizados em faixas de quantidade (0–50, 51–100, 101–200 etc.) dentro do Dataset do Apify.

---

## 📁 Estrutura do projeto

```
extrator_de_emails/
├── extrator.py              # Script principal de extração (usado no Apify)
├── input_schema.json        # Define a interface visual para entrada via Apify
├── apify.json               # Configuração do Actor no Apify
├── requirements.txt         # Dependências Python
├── Dockerfile               # Containerização para execução no Apify
├── ray-so-export.png        # Imagem ilustrativa do projeto
├── LICENSE                  # Licença de uso
├── CONTRIBUTING.md          # Guia de contribuição
└── README.md                # Este arquivo
```

---

## 🚀 Executando via Apify

1. Acesse o [Apify Console](https://console.apify.com/).
2. Crie ou clone o Actor com o código deste repositório.
3. Insira as URLs no campo "Lista de URLs" da interface visual.
4. Clique em "Start". O sistema fará a varredura e extrairá os e-mails.
5. Acesse os resultados em "Dataset" > "default" e exporte em CSV, JSON, etc.

---

## 🧠 Observações

- O sistema evita e-mails duplicados.
- Sites que bloqueiam bots ou exigem autenticação podem não retornar resultados.
- O Apify Dataset mantém o histórico de execuções anteriores.

---

## ✉️ Contato

Desenvolvido por Rafael Marques Lins — Ad Rock Digital Mkt  
📧 rafael@adrock.com.br  
📲 WhatsApp: [Clique aqui para conversar](https://wa.me/5541991255859)  
🌐 https://adrock.com.br

---
