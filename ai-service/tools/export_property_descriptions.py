import csv
import os
import subprocess
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv


ROOT_DIR = Path(__file__).resolve().parents[1]
EXPORT_DIR = ROOT_DIR / "exports"


def env(name, default=None):
    value = os.getenv(name)
    return value if value not in (None, "") else default


def mysql_executable():
    configured = env("MYSQL_EXE")
    if configured:
        return configured
    return "mysql"


def run_mysql_query(query):
    command = [
        mysql_executable(),
        "--default-character-set=utf8mb4",
        "-h",
        env("MYSQL_HOST", "127.0.0.1"),
        "-P",
        env("MYSQL_PORT", "3306"),
        "-u",
        env("MYSQL_USER", "root"),
        f"--password={env('MYSQL_PASSWORD', '')}",
        "-D",
        env("MYSQL_DATABASE", "booking_system"),
        "--batch",
        "--raw",
        "--skip-column-names",
        "-e",
        query,
    ]
    result = subprocess.run(
        command,
        cwd=ROOT_DIR,
        check=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    return result.stdout


def rows_from_tsv(text):
    if not text.strip():
        return []
    rows = []
    for line in text.splitlines():
        rows.append(["" if value == "NULL" else value for value in line.split("\t")])
    return rows


def main():
    load_dotenv(ROOT_DIR / ".env", override=True)
    EXPORT_DIR.mkdir(exist_ok=True)

    columns = [
        "id",
        "merchant_id",
        "property_name",
        "property_type",
        "province",
        "city",
        "district",
        "address",
        "description",
        "facilities",
        "policies",
        "rating",
        "total_reviews",
        "price_range_min",
        "price_range_max",
        "status",
        "is_featured",
        "updated_at",
    ]
    query = f"""
SELECT
  id,
  merchant_id,
  property_name,
  property_type,
  province,
  city,
  district,
  address,
  description,
  facilities,
  policies,
  rating,
  total_reviews,
  price_range_min,
  price_range_max,
  status,
  is_featured,
  updated_at
FROM properties
ORDER BY id;
""".strip()

    rows = rows_from_tsv(run_mysql_query(query))
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_path = EXPORT_DIR / f"property_descriptions_{timestamp}.csv"

    with output_path.open("w", newline="", encoding="utf-8-sig") as file:
        writer = csv.writer(file)
        writer.writerow(columns)
        writer.writerows(rows)

    print(output_path)
    print(f"rows={len(rows)}")


if __name__ == "__main__":
    main()
