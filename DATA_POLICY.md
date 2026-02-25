

# 🔐 DATA POLICY — Ad Rock Prospect Engine

## 1. Objetivo

Este documento define as diretrizes de governança, proteção e uso de dados do projeto **Ad Rock Prospect Engine**.

O objetivo é garantir:

- Segurança das informações
- Conformidade com boas práticas de privacidade
- Separação clara entre código e dados
- Uso ético de dados públicos

---

## 2. Natureza dos Dados Processados

O pipeline trabalha exclusivamente com:

- Dados exportados manualmente pelo próprio usuário
- Informações públicas de websites institucionais
- Emails disponibilizados publicamente em páginas oficiais

O sistema **não realiza:**

- Scraping autenticado
- Coleta de dados privados
- Quebra de login ou automação contra plataformas fechadas
- Coleta de dados sensíveis (CPF, telefone pessoal, etc.)

---

## 3. Classificação dos Dados

| Tipo de Dado | Classificação | Versionado no Git | Observação |
|--------------|---------------|------------------|------------|
| Código-fonte | Público       | ✅ Sim           | Estrutura do pipeline |
| Documentação | Público       | ✅ Sim           | README, CHANGELOG |
| linkedin_raw | Sensível      | ❌ Não           | Exportação LinkedIn |
| linkedin_processed | Sensível | ❌ Não           | Dados segmentados |
| csv_enriquecido | Sensível   | ❌ Não           | Sites e scoring |
| runs/        | Sensível      | ❌ Não           | Logs e snapshots |

---

## 4. Proteção via Git

Os seguintes diretórios são explicitamente ignorados no `.gitignore`:

- `linkedin_raw/`
- `linkedin_processed/`
- `csv_por_segmento/`
- `csv_enriquecido/`
- `runs/`

Isso garante que:

- Nenhum dado real é enviado ao GitHub
- O repositório contém apenas código e arquitetura
- Não há exposição acidental de base comercial

---

## 5. Armazenamento Local

Os dados são armazenados exclusivamente:

- Na máquina local do operador
- Em ambiente controlado
- Sem sincronização automática em nuvem pública

Caso seja utilizado servidor remoto:

- Acesso deve ser protegido por SSH
- Backup deve ser criptografado
- Logs não devem conter informações sensíveis completas

---

## 6. Controle de Execução

O sistema possui mecanismos para reduzir risco operacional:

- Lock file contra execução simultânea
- Snapshot versionado por execução
- Hash SHA256 para controle incremental
- Logs estruturados por run

Esses mecanismos não são apenas técnicos — são também parte da política de governança.

---

## 7. Responsabilidade de Uso

Este projeto é uma ferramenta interna da Ad Rock Digital Mkt.

O uso deve respeitar:

- LGPD
- Termos de uso das plataformas envolvidas
- Boas práticas de prospecção B2B

O operador é responsável por:

- Garantir que os dados exportados possuem autorização adequada
- Não utilizar a ferramenta para spam indiscriminado
- Não comercializar bases coletadas sem consentimento

---

## 8. Princípios Éticos

O pipeline foi projetado sob os seguintes princípios:

- Minimalismo de coleta
- Transparência de origem
- Separação entre código e dados
- Segurança por padrão
- Não exposição pública de ativos comerciais

---

## 9. Evolução Futura

Possíveis melhorias de governança:

- Criptografia local automática de CSV sensíveis
- Controle de acesso por usuário
- Banco de dados com permissão granular
- Auditoria automatizada de uso

---

## 10. Conclusão

Este projeto não é apenas um extrator de emails.

É uma infraestrutura controlada de prospecção B2B com governança de dados definida.

A separação clara entre código e dados é obrigatória.

Qualquer alteração nesta política deve ser versionada.

---

**Autor:** Rafael Marques Lins  
Ad Rock Digital Mkt  
https://adrock.com.br
