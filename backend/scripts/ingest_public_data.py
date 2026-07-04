import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.services.bigquery_ingestion_service import PUBLIC_DATA_SPECS, PublicDataIngestionService


def main() -> None:
    parser = argparse.ArgumentParser(description="Load normalized government/public data CSV into BigQuery.")
    parser.add_argument("source_key", choices=sorted(PUBLIC_DATA_SPECS))
    parser.add_argument("csv_path")
    parser.add_argument("--source-name", required=True)
    parser.add_argument("--source-url")
    parser.add_argument("--source-file-uri")
    args = parser.parse_args()

    result = PublicDataIngestionService().ingest_csv(
        source_key=args.source_key,
        csv_path=args.csv_path,
        source_name=args.source_name,
        source_url=args.source_url,
        source_file_uri=args.source_file_uri,
    )
    print(
        f"{result.status}: loaded {result.records_loaded} rows into {result.table_id} "
        f"(run_id={result.run_id})"
    )


if __name__ == "__main__":
    main()
