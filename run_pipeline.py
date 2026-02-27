import argparse
import logging
import sys
from datetime import datetime
from pathlib import Path
import subprocess
import csv
import re

BASE_DIR = Path(__file__).resolve().parent
RUNS_DIR = BASE_DIR / "runs"
OUTPUT_DIR = BASE_DIR / "output"
TMP_DIR = OUTPUT_DIR / "tmp"

VALID_TLDS = {"com", "org", "net", "br", "gov", "edu"}
PERSONAL_PROVIDERS = {"gmail", "hotmail", "outlook", "yahoo", "icloud", "uol"}

SEGMENT_SOURCE_DIR = BASE_DIR / "data" / "segmented"


def choose_segment_interactively():
    if not SEGMENT_SOURCE_DIR.exists():
        logging.error("Diretório data/segmented não encontrado.")
        sys.exit(1)

    segment_files = sorted(SEGMENT_SOURCE_DIR.glob("empresas_*.csv"))

    if not segment_files:
        logging.error("Nenhum segmento encontrado em data/segmented.")
        sys.exit(1)

    print("\nQual segmento você quer executar?\n")

    segments = []
    for idx, file in enumerate(segment_files, start=1):
        name = file.stem.replace("empresas_", "").upper()
        segments.append(name)
        print(f"{idx}) {name}")

    while True:
        choice = input("\nDigite o número do segmento: ").strip()
        if choice.isdigit():
            choice = int(choice)
            if 1 <= choice <= len(segments):
                return segments[choice - 1]
        print("Opção inválida. Tente novamente.")


def setup_logging(run_dir: Path):
    log_file = run_dir / "pipeline.log"
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(message)s",
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler(sys.stdout),
        ],
    )


def create_run_directory() -> Path:
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    run_dir = RUNS_DIR / timestamp
    run_dir.mkdir(parents=True, exist_ok=True)
    return run_dir


def run_script(script_name: str, args: list):
    cmd = ["python", script_name] + args
    logging.info(f"Executando: {' '.join(cmd)}")
    result = subprocess.run(cmd)
    if result.returncode != 0:
        logging.error(f"Erro ao executar {script_name}")
        sys.exit(1)


def finalize_leads(raw_csv: Path, segment: str):
    logging.info("Iniciando consolidação final de leads...")

    valid_emails = set()

    with open(raw_csv, newline="", encoding="utf-8") as f:
        reader = csv.reader(f)
        next(reader, None)

        for row in reader:
            if len(row) < 2:
                continue

            email = row[1].strip().lower()

            if not re.match(r"^[a-z0-9._%+-]+@[a-z0-9.-]+\.[a-z]{2,}$", email):
                continue

            domain = email.split("@")[1]
            tld = domain.split(".")[-1]

            if tld not in VALID_TLDS:
                continue

            provider = domain.split(".")[0]
            if provider in PERSONAL_PROVIDERS:
                continue

            valid_emails.add(email)

    final_csv = OUTPUT_DIR / f"{segment}_leads_final.csv"

    with open(final_csv, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["email", "domain", "segment"])

        for email in sorted(valid_emails):
            domain = email.split("@")[1]
            writer.writerow([email, domain, segment])

    logging.info(f"{len(valid_emails)} emails corporativos salvos em {final_csv}")


def main():
    parser = argparse.ArgumentParser(description="Run Pipeline Profissional - Simple Extrator")
    parser.add_argument("--segment", required=False)
    parser.add_argument("--max-pages", default="10")

    args = parser.parse_args()

    if not args.segment:
        args.segment = choose_segment_interactively()

    RUNS_DIR.mkdir(exist_ok=True)
    OUTPUT_DIR.mkdir(exist_ok=True)
    TMP_DIR.mkdir(exist_ok=True)

    run_dir = create_run_directory()
    setup_logging(run_dir)

    logging.info("==== INICIANDO PIPELINE ====")

    # 1. Segmentação
    run_script("segmentar_empresas.py", ["--segment", args.segment])

    # 2. Enriquecimento
    segmented_input = BASE_DIR / "data" / "segmented" / f"empresas_{args.segment.lower()}.csv"
    enriched_output = run_dir / "enriched.csv"

    run_script(
        "enriquecer_sites_google_maps.py",
        [
            "--input", str(segmented_input),
            "--output", str(enriched_output),
        ],
    )

    # 3. Gerar URLs
    run_script("gerar_urls.py", [str(enriched_output)])

    # 4. Extrair emails
    raw_output = run_dir / "emails_raw.csv"
    run_script(
        "extrator.py",
        [
            "--urls-file",
            "urls.txt",
            "--output",
            str(raw_output),
            "--max-pages",
            args.max_pages,
        ],
    )

    # 5. Consolidar leads finais
    finalize_leads(raw_output, args.segment)

    logging.info("==== PIPELINE FINALIZADO COM SUCESSO ====")


if __name__ == "__main__":
    main()