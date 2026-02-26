import logging
import re
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import argparse

import pandas as pd

import subprocess
import sys

import json
from datetime import datetime

import os
import shutil
import hashlib
import atexit

# ===============================
# STATE MANAGER
# ===============================
from state_manager import StateManager

# ===============================
# RUN MANAGEMENT (INDUSTRIAL MODE)
# ===============================

def init_run_directory() -> Path:
    runs_dir = OUTPUT_DIR / "runs"
    runs_dir.mkdir(exist_ok=True)

    run_id = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    run_dir = runs_dir / run_id
    run_dir.mkdir(parents=True, exist_ok=True)

    (run_dir / "logs").mkdir(exist_ok=True)
    (run_dir / "enriched").mkdir(exist_ok=True)
    (run_dir / "extracted").mkdir(exist_ok=True)

    # File logger per run
    log_file = run_dir / "logs" / "pipeline.log"
    file_handler = logging.FileHandler(log_file, encoding="utf-8")
    file_handler.setFormatter(logging.Formatter("%(asctime)s | %(levelname)s | %(message)s"))
    logger.addHandler(file_handler)

    return run_dir


def load_pipeline_state(run_dir: Path) -> dict:
    state_file = run_dir / "pipeline_state.json"
    if state_file.exists():
        with open(state_file, "r", encoding="utf-8") as f:
            return json.load(f)
    return {
        "created_at": datetime.now().isoformat(),
        "segments": {}
    }


# ===============================
# LOCK MANAGEMENT
# ===============================

def acquire_lock() -> Path:
    lock_path = OUTPUT_DIR / ".pipeline.lock"
    if lock_path.exists():
        raise RuntimeError("Pipeline já está em execução (lock ativo).")
    lock_path.write_text(str(os.getpid()), encoding="utf-8")
    return lock_path


def release_lock(lock_path: Path) -> None:
    if lock_path.exists():
        lock_path.unlink()


# ===============================
# SNAPSHOT + HASH
# ===============================

def file_sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def snapshot_input_files(run_dir: Path, state: dict) -> None:
    snapshot_dir = run_dir / "input_snapshot"
    snapshot_dir.mkdir(exist_ok=True)

    inputs = {
        "Connections.csv": CONNECTIONS_FILE,
        "Company_Follows.csv": COMPANY_FOLLOWS_FILE,
        "ImportedContacts.csv": IMPORTED_CONTACTS_FILE,
    }

    state["input_hashes"] = {}

    for name, path in inputs.items():
        if path.exists():
            dest = snapshot_dir / name
            shutil.copy2(path, dest)
            state["input_hashes"][name] = file_sha256(path)

    save_pipeline_state(run_dir, state)


def save_pipeline_state(run_dir: Path, state: dict) -> None:
    state_file = run_dir / "pipeline_state.json"
    with open(state_file, "w", encoding="utf-8") as f:
        json.dump(state, f, indent=2)

# ===============================
# CONFIG
# ===============================

BASE_DIR = Path(__file__).resolve().parent
LINKEDIN_DIR = BASE_DIR / "linkedin_raw"
OUTPUT_DIR = BASE_DIR / "linkedin_processed"

LINKEDIN_DIR.mkdir(exist_ok=True)
OUTPUT_DIR.mkdir(exist_ok=True)

CONNECTIONS_FILE = LINKEDIN_DIR / "Connections.csv"
COMPANY_FOLLOWS_FILE = LINKEDIN_DIR / "Company_Follows.csv"
IMPORTED_CONTACTS_FILE = LINKEDIN_DIR / "ImportedContacts.csv"

# ===============================
# LOGGING
# ===============================

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
)
logger = logging.getLogger("linkedin_processor")

# ===============================
# NORMALIZATION / HELPERS
# ===============================

_EMAIL_RE = re.compile(r"[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}", re.I)

_FREE_EMAIL_DOMAINS = {
    "gmail.com",
    "googlemail.com",
    "hotmail.com",
    "outlook.com",
    "live.com",
    "icloud.com",
    "me.com",
    "yahoo.com",
    "yahoo.com.br",
    "uol.com.br",
    "bol.com.br",
    "terra.com.br",
    "proton.me",
    "protonmail.com",
}

_BAD_LOCALPART_PREFIXES = (
    "no-reply",
    "noreply",
    "donotreply",
    "do-not-reply",
    "mailer-daemon",
)


def normalize_string(value) -> str:
    if pd.isna(value) or value is None:
        return ""
    return str(value).strip().lower()


def make_match_key(first: str, last: str) -> str:
    # Mantém simples (sem libs externas). Se quiser evoluir depois: remover acentos.
    f = normalize_string(first)
    l = normalize_string(last)
    return f"{f}_{l}" if f or l else ""


def extract_emails(raw: str) -> List[str]:
    if pd.isna(raw) or raw is None:
        return []
    text = str(raw)
    found = _EMAIL_RE.findall(text)
    # normaliza / dedup mantendo ordem
    seen = set()
    cleaned = []
    for e in found:
        e2 = e.strip().lower()
        if e2 and e2 not in seen:
            seen.add(e2)
            cleaned.append(e2)
    return cleaned


def email_score(email: str) -> float:
    """Score simples para escolher 'melhor' e-mail quando houver múltiplos.

    Prioriza corporativo vs free, e evita no-reply.
    """
    if not email or "@" not in email:
        return -1.0

    local, domain = email.split("@", 1)
    local = local.strip().lower()
    domain = domain.strip().lower()

    score = 0.0

    # penaliza endereços ruins
    if local.startswith(_BAD_LOCALPART_PREFIXES):
        score -= 10.0

    # corporativo vs free
    if domain in _FREE_EMAIL_DOMAINS:
        score += 0.5
    else:
        score += 5.0

    # prioridade por caixas comuns de contato
    if local.startswith("contato"):
        score += 2.5
    elif local.startswith("geral"):
        score += 2.0
    elif local.startswith("info"):
        score += 1.5
    elif local.startswith("comercial"):
        score += 1.25
    elif local.startswith("marketing"):
        score += 1.0

    # e-mail nominal (ex: nome.sobrenome) — leve boost
    if "." in local or "_" in local:
        score += 0.5

    return score


def choose_best_email(emails: List[str]) -> Optional[str]:
    if not emails:
        return None
    ranked = sorted(emails, key=email_score, reverse=True)
    # filtra explicitamente no-reply se houver alternativa
    best = ranked[0]
    if best.split("@", 1)[0].startswith(_BAD_LOCALPART_PREFIXES) and len(ranked) > 1:
        return ranked[1]
    return best


# ===============================
# LOADERS
# ===============================

def clean_connections_file(path: Path) -> pd.DataFrame:
    """Remove linhas iniciais do export do LinkedIn (Notes:) até encontrar header real."""
    logger.info("Limpando arquivo Connections.csv")

    with open(path, "r", encoding="utf-8") as f:
        lines = f.readlines()

    header_index = None
    for i, line in enumerate(lines):
        # O LinkedIn usa exatamente "First Name" como header real
        if line.startswith("First Name"):
            header_index = i
            break

    if header_index is None:
        raise ValueError("Header real não encontrado no Connections.csv (esperado iniciar com 'First Name').")

    cleaned_path = OUTPUT_DIR / "Connections_clean.csv"
    with open(cleaned_path, "w", encoding="utf-8") as f:
        f.writelines(lines[header_index:])

    df = pd.read_csv(cleaned_path)
    logger.info(f"{len(df)} conexões carregadas (raw).")

    # Dedup por URL (se houver repetição)
    if "URL" in df.columns:
        before = len(df)
        df = df.drop_duplicates(subset=["URL"], keep="first").copy()
        if len(df) != before:
            logger.warning(f"Connections: removidos {before - len(df)} duplicados por URL.")

    logger.info(f"{len(df)} conexões após deduplicação por URL.")
    return df


def load_company_follows(path: Path) -> pd.DataFrame:
    logger.info("Carregando Company Follows")
    df = pd.read_csv(path)
    logger.info(f"{len(df)} empresas seguidas carregadas.")
    return df


def load_imported_contacts(path: Path) -> pd.DataFrame:
    logger.info("Carregando Imported Contacts")
    df = pd.read_csv(path)
    logger.info(f"{len(df)} contatos importados carregados.")
    return df


# ===============================
# PROCESSAMENTO
# ===============================

def build_imported_email_index(imported_df: pd.DataFrame) -> Tuple[Dict[str, Optional[str]], Dict[str, int]]:
    """Constrói um índice 1:1: match_key -> melhor email

    Importante: isso evita explosão de linhas no merge.
    Também retorna contagem de candidatos por match_key (para auditoria).
    """
    required = {"FirstName", "LastName", "Emails"}
    missing = required - set(imported_df.columns)
    if missing:
        raise ValueError(f"ImportedContacts.csv sem colunas esperadas: {missing}")

    logger.info("Indexando Imported Contacts (deduplicação por nome)")

    email_by_key: Dict[str, Optional[str]] = {}
    candidates_count: Dict[str, int] = {}

    # itertuples é bem mais rápido
    for row in imported_df[["FirstName", "LastName", "Emails"]].itertuples(index=False):
        first, last, emails_raw = row
        key = make_match_key(first, last)
        if not key:
            continue

        emails = extract_emails(emails_raw)
        if not emails:
            # ainda assim conta ocorrência do nome
            candidates_count[key] = candidates_count.get(key, 0) + 1
            continue

        candidates_count[key] = candidates_count.get(key, 0) + 1

        best = choose_best_email(emails)
        if not best:
            continue

        # Se já existe e-mail para esse key, mantém o melhor pelo score
        if key not in email_by_key or email_score(best) > email_score(email_by_key[key] or ""):
            email_by_key[key] = best

    logger.info(f"Index gerado: {len(email_by_key)} nomes com email selecionado.")
    return email_by_key, candidates_count


def cruzar_connections_imported(connections_df: pd.DataFrame, imported_df: pd.DataFrame) -> pd.DataFrame:
    logger.info("Cruzando Connections com Imported Contacts (merge 1:1)")

    required = {"First Name", "Last Name"}
    missing = required - set(connections_df.columns)
    if missing:
        raise ValueError(f"Connections_clean.csv sem colunas esperadas: {missing}")

    # cria match_key em connections
    connections_df = connections_df.copy()
    connections_df["match_key"] = connections_df.apply(
        lambda r: make_match_key(r.get("First Name", ""), r.get("Last Name", "")), axis=1
    )

    email_index, candidates_count = build_imported_email_index(imported_df)

    connections_df["Imported_Email"] = connections_df["match_key"].map(email_index)
    connections_df["Imported_Email_Candidates"] = connections_df["match_key"].map(lambda k: candidates_count.get(k, 0))

    # Métricas reais
    total = len(connections_df)
    unique_urls = connections_df["URL"].nunique() if "URL" in connections_df.columns else None
    matched = connections_df["Imported_Email"].notna().sum()

    logger.info(f"Conexões (linhas): {total}")
    if unique_urls is not None:
        logger.info(f"Conexões únicas (URL): {unique_urls}")
    logger.info(f"Conexões com email importado: {matched} ({round((matched/total)*100, 2)}%)")

    # integridade: não pode explodir linhas
    if unique_urls is not None and unique_urls != total:
        logger.warning(
            "Integridade: número de URLs únicas diferente do total de linhas. "
            "Isso pode indicar duplicidade no Connections export."
        )

    output_path = OUTPUT_DIR / "connections_com_email.csv"
    connections_df.to_csv(output_path, index=False)
    logger.info(f"Arquivo gerado: {output_path}")

    return connections_df


def gerar_empresas_consolidadas(connections_df: pd.DataFrame, company_follows_df: pd.DataFrame) -> pd.DataFrame:
    logger.info("Gerando base consolidada de empresas")

    # companies a partir das conexões
    empresas_connections = []
    if "Company" in connections_df.columns:
        empresas_connections = [c for c in connections_df["Company"].dropna().astype(str).tolist() if c.strip()]

    # companies a partir do follows
    if "Organization" not in company_follows_df.columns:
        raise ValueError("Company_Follows.csv sem coluna esperada: 'Organization'")
    empresas_follows = [c for c in company_follows_df["Organization"].dropna().astype(str).tolist() if c.strip()]

    # set + ordenação estável
    empresas_total = sorted(set(empresas_connections) | set(empresas_follows), key=lambda x: x.lower())

    empresas_df = pd.DataFrame({
        "company_name": empresas_total,
        "source_connections": [1 if e in set(empresas_connections) else 0 for e in empresas_total],
        "source_follows": [1 if e in set(empresas_follows) else 0 for e in empresas_total],
    })

    output_path = OUTPUT_DIR / "empresas_consolidadas.csv"
    empresas_df.to_csv(output_path, index=False)

    logger.info(f"{len(empresas_df)} empresas consolidadas.")
    logger.info(f"Arquivo gerado: {output_path}")

    return empresas_df


def gerar_empresas_com_email_direto(connections_df: pd.DataFrame) -> pd.DataFrame:
    """Gera uma lista de empresas que já possuem ao menos 1 contato com email direto."""
    if "Company" not in connections_df.columns:
        logger.warning("Connections não possui coluna 'Company'. Pulando empresas_com_email_direto.")
        return pd.DataFrame()

    df = connections_df.copy()
    df["Company"] = df["Company"].astype(str)

    only = df[df["Imported_Email"].notna() & df["Company"].notna() & (df["Company"].str.strip() != "")]

    grouped = (
        only.groupby("Company")
        .agg(
            contacts_with_email=("Imported_Email", "count"),
            sample_email=("Imported_Email", "first"),
        )
        .reset_index()
        .rename(columns={"Company": "company_name"})
        .sort_values(by="contacts_with_email", ascending=False)
    )

    output_path = OUTPUT_DIR / "empresas_com_email_direto.csv"
    grouped.to_csv(output_path, index=False)
    logger.info(f"Arquivo gerado: {output_path} ({len(grouped)} empresas com email direto)")
    return grouped


def gerar_empresas_sem_email_direto(
    empresas_consolidadas_df: pd.DataFrame,
    empresas_com_email_df: pd.DataFrame,
) -> pd.DataFrame:
    """
    Gera lista de empresas que ainda NÃO possuem email direto via Connections.
    Base = empresas_consolidadas - empresas_com_email_direto
    """
    logger.info("Gerando base de empresas SEM email direto")

    if empresas_consolidadas_df.empty:
        logger.warning("empresas_consolidadas_df vazio. Nada a processar.")
        return pd.DataFrame()

    empresas_com_email_set = set()

    if not empresas_com_email_df.empty and "company_name" in empresas_com_email_df.columns:
        empresas_com_email_set = set(
            empresas_com_email_df["company_name"]
            .dropna()
            .astype(str)
            .str.strip()
            .tolist()
        )

    empresas_sem_email = empresas_consolidadas_df[
        ~empresas_consolidadas_df["company_name"].isin(empresas_com_email_set)
    ].copy()

    output_path = OUTPUT_DIR / "empresas_sem_email_direto.csv"
    empresas_sem_email.to_csv(output_path, index=False)

    logger.info(
        f"{len(empresas_sem_email)} empresas sem email direto. "
        f"Arquivo gerado: {output_path}"
    )

    return empresas_sem_email


# ===============================
# LIMPEZA AVANÇADA + PRIORIZAÇÃO
# ===============================

# ===============================
# SEGMENTAÇÃO POR POSITION
# ===============================

SEGMENT_KEYWORDS = {
    "ONG": ["instituto", "fundação", "fundacao", "ong", "nonprofit"],
    "Educação": ["professor", "educação", "educacao", "universidade", "escola", "coordenador"],
    "Marketing": ["marketing", "growth", "publicidade", "ads", "mídia", "midia"],
    "Tecnologia": ["software", "developer", "dev", "ai", "product", "tech", "engenheiro"],
    "Jurídico": ["advogado", "law", "jurídico", "juridico"],
    "Saúde": ["saúde", "saude", "hospital", "clínica", "clinica"],
    "Mídia": ["editor", "jornalista", "redação", "redacao"],
}

_INVALID_COMPANY_PATTERNS = [
    "autônomo",
    "autonomo",
    "buscando recolocação",
    "sabbatical",
    "freelancer",
    "self employed",
    "self-employed",
    "?",
]

def is_valid_company_name(name: str) -> bool:
    if not name:
        return False

    n = name.strip().lower()

    # remove urls
    if n.startswith("http://") or n.startswith("https://"):
        return False

    # muito curto
    if len(n) < 3:
        return False

    for pattern in _INVALID_COMPANY_PATTERNS:
        if pattern in n:
            return False

    return True


def normalizar_nome_empresa(name: str) -> str:
    if not name:
        return ""
    n = name.strip()
    n = re.sub(r"\s+", " ", n)
    return n


def limpar_empresas_sem_email(empresas_df: pd.DataFrame) -> pd.DataFrame:
    logger.info("Aplicando limpeza avançada nas empresas sem email")

    df = empresas_df.copy()

    df["company_name"] = df["company_name"].astype(str).apply(normalizar_nome_empresa)

    df = df[df["company_name"].apply(is_valid_company_name)]

    before = len(df)
    df = df.drop_duplicates(subset=["company_name"])
    logger.info(f"Após limpeza e deduplicação: {len(df)} empresas válidas.")

    output_path = OUTPUT_DIR / "empresas_sem_email_direto_clean.csv"
    df.to_csv(output_path, index=False)

    logger.info(f"Arquivo gerado: {output_path}")

    return df


def gerar_priorizacao_empresas(empresas_df: pd.DataFrame) -> pd.DataFrame:
    logger.info("Gerando priorização estratégica de empresas")

    df = empresas_df.copy()

    # score base
    df["lead_score"] = 0

    # conexões têm prioridade maior que follows
    if "source_connections" in df.columns:
        df["lead_score"] += df["source_connections"] * 5

    if "source_follows" in df.columns:
        df["lead_score"] += df["source_follows"] * 2

    # empresas com ambas fontes ganham bônus
    df.loc[
        (df["source_connections"] == 1) & (df["source_follows"] == 1),
        "lead_score"
    ] += 3

    df = df.sort_values(by="lead_score", ascending=False)

    output_path = OUTPUT_DIR / "empresas_priorizadas.csv"
    df.to_csv(output_path, index=False)

    logger.info(f"Arquivo gerado: {output_path}")

    return df




# ===============================
# SEGMENTAÇÃO EMPRESARIAL (BASEADA NO NOME DA EMPRESA)
# ===============================

EMPRESA_SEGMENT_KEYWORDS = {
    "ONG": ["instituto", "fundação", "fundacao", "associação", "associacao", "ong", "nonprofit"],
    "Educação": ["universidade", "escola", "colégio", "colegio", "educação", "educacao"],
    "Marketing": ["marketing", "publicidade", "comunicação", "comunicacao", "agência", "agencia"],
    "Tecnologia": ["software", "tech", "digital", "ai", "tecnologia", "systems", "solutions"],
    "Jurídico": ["advocacia", "advogados", "law", "jurídico", "juridico"],
    "Saúde": ["hospital", "clínica", "clinica", "saúde", "saude", "med"],
    "Mídia": ["jornal", "media", "mídia", "comunicação", "comunicacao", "editora"],
}


def classificar_segmento_empresa(company_name: str) -> str:
    if not company_name:
        return "Outros"

    nome = company_name.lower()

    for segmento, keywords in EMPRESA_SEGMENT_KEYWORDS.items():
        for palavra in keywords:
            if palavra in nome:
                return segmento

    return "Outros"


def gerar_empresas_segmentadas(empresas_consolidadas_df: pd.DataFrame) -> pd.DataFrame:
    """
    Segmentação empresarial pura.
    Cada empresa recebe apenas 1 segmento baseado no nome.
    """

    logger.info("Classificando empresas por segmento (EMPRESARIAL)")

    if empresas_consolidadas_df.empty:
        logger.warning("empresas_consolidadas_df vazio.")
        return pd.DataFrame()

    df = empresas_consolidadas_df.copy()

    df["segment"] = df["company_name"].apply(classificar_segmento_empresa)

    output_path = OUTPUT_DIR / "empresas_segmentadas.csv"
    df.to_csv(output_path, index=False)

    logger.info(f"{len(df)} empresas segmentadas (modelo empresarial).")
    logger.info(f"Arquivo gerado: {output_path}")

    return df


def gerar_csv_por_segmento(empresas_segmentadas_df: pd.DataFrame) -> None:
    logger.info("Gerando CSVs por segmento (EMPRESARIAL)")

    if empresas_segmentadas_df.empty:
        logger.warning("DataFrame de segmentação vazio.")
        return

    segmentos_dir = OUTPUT_DIR / "segmentos"
    segmentos_dir.mkdir(exist_ok=True)

    for segmento in empresas_segmentadas_df["segment"].unique():
        df_segmento = empresas_segmentadas_df[
            empresas_segmentadas_df["segment"] == segmento
        ]

        path = segmentos_dir / f"{segmento}.csv"
        df_segmento.to_csv(path, index=False)

        logger.info(f"{segmento}: {len(df_segmento)} empresas -> {path}")

# ===============================
# PIPELINE FULL AUTO POR SEGMENTO
# ===============================

def executar_pipeline_full_auto_por_segmento(
    run_dir: Path,
    state: dict,
    no_enrich: bool = False,
    only_segment: Optional[str] = None,
    dry_run: bool = False
) -> None:
    """
    Para cada CSV em linkedin_processed/segmentos:
    - Enriquecer via Google Maps
    - Rodar pipeline_extracao.py
    """

    logger.info("==== INICIANDO PIPELINE FULL AUTO POR SEGMENTO ====")

    # =========================
    # API USAGE CONTROL
    # =========================
    state_manager = StateManager()
    DAILY_API_LIMIT = 24000
    EXECUTION_API_LIMIT = 2000
    api_calls_this_run = 0

    segmentos_dir = OUTPUT_DIR / "segmentos"
    enriched_dir = run_dir / "enriched"
    extracted_dir = run_dir / "extracted"

    if not segmentos_dir.exists():
        logger.warning("Diretório de segmentos não encontrado.")
        return

    for arquivo in segmentos_dir.glob("*.csv"):
        segmento_nome = arquivo.stem
        # Normaliza nome do segmento para evitar problemas com acentos no filesystem
        segmento_safe = re.sub(r"[^A-Za-z0-9_]+", "_", segmento_nome)
        logger.info(f"Processando segmento: {segmento_nome}")

        if only_segment and segmento_nome.lower() != only_segment.lower():
            continue

        if segmento_nome not in state["segments"]:
            state["segments"][segmento_nome] = {
                "enriched": False,
                "extracted": False
            }

        segment_state = state["segments"][segmento_nome]

        input_hash = file_sha256(arquivo)
        previous_hash = segment_state.get("input_hash")

        # =========================
        # INDUSTRIAL RESUME LOGIC
        # =========================

        # Se o hash mudou, reseta estado do segmento
        if previous_hash and previous_hash != input_hash:
            logger.info(f"Segmento {segmento_nome} sofreu alteração (hash diferente). Resetando estado.")
            segment_state["enriched"] = False
            segment_state["extracted"] = False

        # Atualiza hash atual
        segment_state["input_hash"] = input_hash

        # Skip processed ativado
        if state.get("skip_processed"):

            # Se já foi extraído e o hash é igual → pula com segurança
            if segment_state.get("extracted") and previous_hash == input_hash:
                logger.info(f"[SKIP_PROCESSED] Segmento {segmento_nome} já processado e sem alterações. Pulando.")
                continue

        else:
            # Modo padrão: se já foi extraído e hash igual → pula
            if segment_state.get("extracted") and previous_hash == input_hash:
                logger.info(f"Segmento {segmento_nome} já extraído anteriormente e sem alterações. Pulando.")
                continue

        enriched_path = enriched_dir / f"{segmento_safe}_enriquecido.csv"

        # Enriquecimento
        if no_enrich:
            logger.info(f"[NO_ENRICH] Pulando enriquecimento do segmento {segmento_nome}.")
        elif enriched_path.exists() and segment_state.get("enriched"):
            logger.info(f"Segmento {segmento_nome} já possui arquivo enriquecido. Pulando enriquecimento.")
        else:
            max_retries = 3
            retry_count = 0
            while retry_count < max_retries:
                try:
                    if dry_run:
                        logger.info(f"[DRY_RUN] Enriqueceria segmento {segmento_nome}")
                        break
                    else:
                        if not state_manager.can_call_api(DAILY_API_LIMIT):
                            logger.warning("Limite diário de API atingido. Encerrando pipeline.")
                            return

                        if api_calls_this_run >= EXECUTION_API_LIMIT:
                            logger.warning("Limite de API por execução atingido. Encerrando pipeline.")
                            return

                        subprocess.run([
                            sys.executable,
                            "enriquecer_sites_google_maps.py",
                            "--input", str(arquivo),
                            "--output", str(enriched_path),
                            "--sleep", "0.6"
                        ], check=True)

                        state_manager.increment_api_calls(1)
                        api_calls_this_run += 1

                        segment_state["enriched"] = True
                        save_pipeline_state(run_dir, state)

                        break

                except subprocess.CalledProcessError as e:
                    retry_count += 1
                    logger.warning(f"Erro no enriquecimento do segmento {segmento_nome}. Tentativa {retry_count}/{max_retries}")
                    if retry_count >= max_retries:
                        logger.error(f"Falha definitiva no enriquecimento do segmento {segmento_nome}")
                        segment_state["enriched"] = False
                        save_pipeline_state(run_dir, state)

        # Validação do arquivo enriquecido antes da extração
        if not enriched_path.exists():
            logger.error(f"Arquivo enriquecido não encontrado para {segmento_nome}. Pulando extração.")
            continue

        try:
            df_enriched = pd.read_csv(enriched_path)
        except Exception as e:
            logger.error(f"Erro ao ler arquivo enriquecido de {segmento_nome}: {e}")
            continue

        if df_enriched.empty:
            logger.warning(f"Arquivo enriquecido de {segmento_nome} está vazio. Pulando extração.")
            continue

        # Extração
        max_retries = 3
        retry_count = 0

        while retry_count < max_retries:
            try:
                if dry_run:
                    logger.info(f"[DRY_RUN] Extrairia emails do segmento {segmento_nome}")
                    break
                else:
                    subprocess.run([
                        sys.executable,
                        "pipeline_extracao.py",
                        "--input", str(enriched_path),
                        "--confidence", "0.65"
                    ], check=True)

                    segment_state["extracted"] = True
                    state["segments"][segmento_nome]["output_hash"] = file_sha256(enriched_path)
                    save_pipeline_state(run_dir, state)

                    break

            except subprocess.CalledProcessError as e:
                retry_count += 1
                logger.warning(f"Erro na extração do segmento {segmento_nome}. Tentativa {retry_count}/{max_retries}")
                if retry_count >= max_retries:
                    logger.error(f"Falha definitiva na extração do segmento {segmento_nome}")
                    segment_state["extracted"] = False
                    save_pipeline_state(run_dir, state)
        logger.info(f"Segmento {segmento_nome} processado com sucesso.")


    logger.info("==== PIPELINE POR SEGMENTO FINALIZADO ====")


# ===============================
# RELATÓRIO FINAL
# ===============================

def gerar_relatorio_final(run_dir: Path, state: dict) -> None:
    rows = []
    for segmento, data in state.get("segments", {}).items():
        rows.append({
            "segmento": segmento,
            "input_hash": data.get("input_hash"),
            "enriched": data.get("enriched"),
            "extracted": data.get("extracted"),
            "output_hash": data.get("output_hash"),
        })

    if not rows:
        return

    df = pd.DataFrame(rows)
    report_path = run_dir / "run_summary.csv"
    df.to_csv(report_path, index=False)
    logger.info(f"Relatório consolidado gerado: {report_path}")
# ===============================
# MAIN
# ===============================

def main() -> None:
    logger.info("==== INICIANDO PROCESSAMENTO LINKEDIN (v2) ====")

    parser = argparse.ArgumentParser()
    parser.add_argument("--no-enrich", action="store_true")
    parser.add_argument("--only-segment", type=str, default=None)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--resume", action="store_true")
    parser.add_argument("--skip-processed", action="store_true")
    args = parser.parse_args()

    lock_path = acquire_lock()
    atexit.register(lambda: release_lock(lock_path))

    if not CONNECTIONS_FILE.exists():
        raise FileNotFoundError("Connections.csv não encontrado em linkedin_raw/.")
    if not COMPANY_FOLLOWS_FILE.exists():
        raise FileNotFoundError("Company_Follows.csv não encontrado em linkedin_raw/.")
    if not IMPORTED_CONTACTS_FILE.exists():
        raise FileNotFoundError("ImportedContacts.csv não encontrado em linkedin_raw/.")

    connections_df = clean_connections_file(CONNECTIONS_FILE)
    company_follows_df = load_company_follows(COMPANY_FOLLOWS_FILE)
    imported_df = load_imported_contacts(IMPORTED_CONTACTS_FILE)

    merged_df = cruzar_connections_imported(connections_df, imported_df)

    # Gera empresas consolidadas
    empresas_consolidadas_df = gerar_empresas_consolidadas(merged_df, company_follows_df)

    # Segmentação empresarial baseada no nome da empresa
    empresas_segmentadas_df = gerar_empresas_segmentadas(empresas_consolidadas_df)
    gerar_csv_por_segmento(empresas_segmentadas_df)

    # outputs principais
    empresas_com_email_df = gerar_empresas_com_email_direto(merged_df)

    # nova saída estratégica
    empresas_sem_email_df = gerar_empresas_sem_email_direto(
        empresas_consolidadas_df,
        empresas_com_email_df
    )

    # etapa 1: limpeza inteligente
    empresas_sem_email_clean_df = limpar_empresas_sem_email(empresas_sem_email_df)

    # etapa 3: priorização estratégica
    empresas_priorizadas_df = gerar_priorizacao_empresas(empresas_sem_email_clean_df)

    # ===============================
    # RUN MODE (NEW / RESUME)
    # ===============================

    runs_root = OUTPUT_DIR / "runs"
    runs_root.mkdir(exist_ok=True)

    if args.resume:
        all_runs = sorted(
            [d for d in runs_root.iterdir() if d.is_dir()],
            key=lambda x: x.name
        )

        if not all_runs:
            raise RuntimeError("Nenhum run anterior encontrado para --resume.")

        run_dir = all_runs[-1]
        logger.info(f"Modo RESUME ativado. Reutilizando run: {run_dir}")

        state = load_pipeline_state(run_dir)
    else:
        run_dir = init_run_directory()
        state = load_pipeline_state(run_dir)
        logger.info(f"Novo run criado: {run_dir}")
        snapshot_input_files(run_dir, state)

    # flag global para skip processed
    if args.skip_processed:
        state["skip_processed"] = True
    else:
        state["skip_processed"] = False

    save_pipeline_state(run_dir, state)
    executar_pipeline_full_auto_por_segmento(
        run_dir,
        state,
        no_enrich=args.no_enrich,
        only_segment=args.only_segment,
        dry_run=args.dry_run
    )
    gerar_relatorio_final(run_dir, state)

    logger.info("==== PROCESSAMENTO FINALIZADO (v2) ====")


if __name__ == "__main__":
    main()