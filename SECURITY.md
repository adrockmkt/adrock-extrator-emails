

# 🛡 SECURITY POLICY — Ad Rock Prospect Engine

## 1. Purpose

This document defines the security guidelines for the Ad Rock Prospect Engine project.

The goal is to ensure:

- Protection of commercial data
- Controlled execution of the pipeline
- Prevention of accidental exposure
- Operational integrity

---

## 2. Security Scope

This repository is designed to version:

- Source code
- Documentation
- Architectural decisions

It is explicitly NOT designed to store:

- Raw LinkedIn exports
- Processed prospect databases
- Enriched CSV files
- Execution logs containing business data

All sensitive data must remain outside version control.

---

## 3. Data Exposure Prevention

Security is enforced through:

- `.gitignore` rules blocking sensitive folders
- Separation between code and runtime data
- Per-run folder isolation
- No automatic cloud sync

Protected directories include:

- `linkedin_raw/`
- `linkedin_processed/`
- `csv_por_segmento/`
- `csv_enriquecido/`
- `runs/`

---

## 4. Local Execution Security

Recommended execution practices:

- Use virtual environments (venv)
- Avoid running as root
- Restrict file permissions for data folders
- Do not store API keys in code
- Use environment variables for credentials

Example (macOS/Linux):

```bash
chmod -R 700 linkedin_raw linkedin_processed
```

---

## 5. API Key Protection

If using external APIs (e.g., Google Maps):

- Keys must be stored in environment variables
- Keys must not be committed to Git
- Restrict API keys by IP when possible
- Apply usage quotas

Never hardcode API credentials.

---

## 6. Execution Controls

The pipeline includes built-in safety mechanisms:

- Lock file to prevent concurrent runs
- Hash-based incremental processing
- Snapshot isolation per execution
- Structured logging

These controls reduce risk of:

- Data corruption
- Duplicate processing
- Accidental overwrites

---

## 7. Remote Server Usage

If deployed on a server:

- Use SSH key authentication
- Disable password login
- Restrict inbound ports
- Enable firewall (ufw or equivalent)
- Encrypt backups

Sensitive CSV files should never be publicly accessible.

---

## 8. Responsible Usage

The tool must not be used for:

- Mass unsolicited spam
- Automated abuse of websites
- Violating platform terms of service
- Circumventing authentication systems

This is a B2B intelligence and outreach preparation tool.

---

## 9. Incident Response

If sensitive data is accidentally committed:

1. Immediately remove the file from Git history
2. Rotate API keys if exposed
3. Force push cleaned history if necessary
4. Audit commit logs

Tools recommended:

- `git filter-repo`
- `BFG Repo-Cleaner`

---

## 10. Security Philosophy

Security in this project follows the principle of:

- Secure by default
- Minimal exposure
- Code/data separation
- Operational discipline

This project is structured as an internal strategic asset.

Any security-related change must be documented and versioned.

---

**Author:** Rafael Marques Lins  
Ad Rock Digital Mkt  
https://adrock.com.br