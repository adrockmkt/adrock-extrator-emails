# 📨 Ad Rock Extrator de E-mails via Apify

Este projeto automatiza a extração de e-mails públicos a partir de sites coletados previamente via Google Maps, utilizando a plataforma [Apify](https://apify.com/) e um script em Python. Ideal para curadoria de contatos institucionais, prospecção ou base de dados.

---

## ⚙️ Como funciona

1. O usuário insere uma ou mais URLs diretamente na interface do Apify.
2. O Actor acessa cada site informado e percorre seus links internos.
3. Todos os e-mails válidos encontrados são salvos automaticamente no Dataset da execução.

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
