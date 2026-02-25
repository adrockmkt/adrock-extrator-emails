

# 🤝 Guia de Contribuição

Obrigado por seu interesse em contribuir com o projeto **Extrator de E-mails**! Este documento tem como objetivo orientar colaboradores sobre como participar de forma eficaz.

---

## 📌 Como contribuir

1. **Fork este repositório**
2. Crie uma branch com sua feature ou correção:
   ```bash
   git checkout -b minha-contribuicao
   ```
3. Faça suas alterações com clareza e mantenha o padrão do projeto.
4. Commit suas mudanças com uma mensagem descritiva:
   ```bash
   git commit -m "fix: corrige tratamento de duplicação"
   ```
5. Envie sua branch:
   ```bash
   git push origin minha-contribuicao
   ```
6. Abra um Pull Request com uma descrição objetiva da mudança.

---

## 🧪 Boas práticas

- Sempre teste o código antes de enviar.
- Descreva o que foi alterado e por quê no seu PR.
- Use comentários apenas quando necessário para explicar lógicas específicas.
- Evite adicionar bibliotecas desnecessárias.

---

## 📂 Estrutura esperada

- `extrator.py`: script principal
- `urls.txt`: entrada de URLs (uma por linha)
- `emails_extraidos.txt`: arquivo gerado (evitar versionar)
- `README.md`, `CONTRIBUTING.md`, `.gitignore`

---

## 📫 Dúvidas?

Entre em contato:

Rafael Marques Lins  
📧 rafael@adrock.com.br  
📲 [WhatsApp](https://wa.me/5541991255859)

---

Obrigado por ajudar a tornar este projeto melhor!
# 🔒 Contribuição & Governança do Projeto

Este projeto evoluiu para um **pipeline industrial interno**, com controle de estado, versionamento por execução e governança operacional.

Atualmente, **não é um projeto open source público para contribuições externas**.

---

## 📌 Modelo de Contribuição

O desenvolvimento segue o seguinte padrão:

- Alterações estruturais devem manter compatibilidade com:
  - Controle incremental por hash
  - Versionamento por run (`runs/YYYY-MM-DD_HH-MM-SS`)
  - Snapshot automático de inputs
  - Lock de execução (`.pipeline.lock`)
  - Relatórios consolidados (`run_summary.csv`)
- Qualquer modificação que altere schema de CSV deve:
  - Preservar compatibilidade com `pipeline_extracao.py`
  - Garantir resiliência contra ausência de colunas
- Mudanças devem manter arquitetura modular e desacoplada.

---

## 🧠 Padrões Arquiteturais

O projeto segue princípios de:

- Pipeline idempotente
- Execução incremental
- Controle de integridade por SHA256
- Logs persistentes por execução
- CLI com flags operacionais (`--only-segment`, `--no-enrich`, `--dry-run`)

---

## 🚫 O que evitar

- Alterar schema sem validação de compatibilidade
- Remover controle de hash
- Remover controle de lock
- Adicionar dependências pesadas desnecessárias
- Inserir lógica acoplada entre enriquecimento e extração

---

## 📦 Fluxo de Versionamento

As mudanças relevantes devem:

1. Atualizar o `CHANGELOG.md`
2. Manter `.gitignore` coerente com arquivos de runtime
3. Garantir que nenhuma pasta de execução (`runs/`) seja versionada

---

## 📫 Contato

Rafael Marques Lins  
📧 rafael@adrock.com.br  
📲 https://wa.me/5541991255859  

---

Este projeto é parte do ecossistema interno da Ad Rock Digital Mkt e segue evolução contínua controlada.