import argparse
import csv
import json
import re
import sys
from datetime import datetime
from html.parser import HTMLParser
from pathlib import Path
from typing import Any
from zipfile import ZipFile
from xml.etree import ElementTree as ET

import requests
from urllib3.exceptions import InsecureRequestWarning
from urllib3 import disable_warnings

DATA_GOV_IMD_SUBDIVISION_URL = "https://api.data.gov.in/resource/d0419b03-b41b-4226-b48b-0bc92bf139f8"
MAHARAIN_DRY_SPELL_URL = (
    "https://maharain.maharashtra.gov.in/test/maharain/"
    "rpt_past_queries_tehsil_wise_dryspell.php"
)
MAHARAIN_HEAVY_RAIN_URL = (
    "https://maharain.maharashtra.gov.in/test/maharain/"
    "rpt_past_queries_tehsil_wise_heavy_rainfall.php"
)
MONTH_COLUMNS = {
    "jan": 1,
    "feb": 2,
    "mar": 3,
    "apr": 4,
    "may": 5,
    "jun": 6,
    "jul": 7,
    "aug": 8,
    "sep": 9,
    "oct": 10,
    "nov": 11,
    "dec": 12,
}


class TableParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.rows: list[list[str]] = []
        self._row: list[str] | None = None
        self._cell: list[str] | None = None

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag == "tr":
            self._row = []
        elif tag in {"td", "th"} and self._row is not None:
            self._cell = []

    def handle_data(self, data: str) -> None:
        if self._cell is not None:
            self._cell.append(data)

    def handle_endtag(self, tag: str) -> None:
        if tag in {"td", "th"} and self._cell is not None and self._row is not None:
            value = " ".join("".join(self._cell).split())
            self._row.append(value)
            self._cell = None
        elif tag == "tr" and self._row is not None:
            if any(cell for cell in self._row):
                self.rows.append(self._row)
            self._row = None


def main() -> None:
    parser = argparse.ArgumentParser(description="Fetch and normalize Kisan AI public datasets.")
    sub = parser.add_subparsers(dest="command", required=True)

    data_gov = sub.add_parser("fetch-data-gov-imd-subdivision")
    data_gov.add_argument("--api-key", required=True)
    data_gov.add_argument("--resource-url", default=DATA_GOV_IMD_SUBDIVISION_URL)
    data_gov.add_argument("--limit", type=int, default=100)
    data_gov.add_argument("--total", type=int, default=641)
    data_gov.add_argument("--out-dir", default="data/raw/data_gov")
    data_gov.add_argument("--normalized-out", default="data/normalized/subdivision_rainfall_history/data_gov_imd_subdivision.csv")

    imd_csv = sub.add_parser("normalize-imd-subdivision")
    imd_csv.add_argument("input_path")
    imd_csv.add_argument("--out", default="data/normalized/subdivision_rainfall_history/imd_subdivision.csv")

    maharain = sub.add_parser("fetch-maharain")
    maharain.add_argument("--start-year", type=int, required=True)
    maharain.add_argument("--end-year", type=int, required=True)
    maharain.add_argument("--out-dir", default="data/raw/maharain")
    maharain.add_argument("--normalized-dir", default="data/normalized")
    maharain.add_argument("--insecure", action="store_true", help="Disable TLS verification for Maharain if local CA validation fails.")

    crop_csv = sub.add_parser("normalize-crop-csv")
    crop_csv.add_argument("input_path")
    crop_csv.add_argument("--out", required=True)
    crop_csv.add_argument("--state-filter")

    des_xlsx = sub.add_parser("normalize-des-district-xlsx")
    des_xlsx.add_argument("input_path")
    des_xlsx.add_argument("--out", default="data/normalized/crop_production_history/des_district_2024_25.csv")
    des_xlsx.add_argument("--state-filter")

    aspirational = sub.add_parser("normalize-aspirational-districts")
    aspirational.add_argument("input_path")
    aspirational.add_argument("--out", default="data/normalized/aspirational_districts/aspirational_districts.csv")

    args = parser.parse_args()
    if args.command == "fetch-data-gov-imd-subdivision":
        records = fetch_data_gov_records(args.resource_url, args.api_key, args.limit, args.total)
        raw_path = write_json(Path(args.out_dir) / "imd_subdivision_records.json", records)
        rows = normalize_imd_subdivision_records(records)
        write_csv(Path(args.normalized_out), rows, ["subdivision", "year", "month", "rainfall_mm"])
        print(f"Fetched {len(records)} data.gov rows -> {raw_path}")
        print(f"Normalized {len(rows)} rainfall rows -> {args.normalized_out}")
    elif args.command == "normalize-imd-subdivision":
        rows = load_imd_subdivision(Path(args.input_path))
        write_csv(Path(args.out), rows, ["subdivision", "year", "month", "rainfall_mm"])
        print(f"Normalized {len(rows)} rainfall rows -> {args.out}")
    elif args.command == "fetch-maharain":
        dry_rows, heavy_rows = fetch_maharain_range(
            args.start_year,
            args.end_year,
            Path(args.out_dir),
            verify_tls=not args.insecure,
        )
        dry_out = Path(args.normalized_dir) / "maharashtra_dryspell_events/maharain_dryspell.csv"
        heavy_out = Path(args.normalized_dir) / "maharashtra_heavy_rainfall_events/maharain_heavy_rainfall.csv"
        write_csv(
            dry_out,
            dry_rows,
            ["state", "district", "taluka", "season_year", "start_date", "end_date", "duration_days"],
        )
        write_csv(
            heavy_out,
            heavy_rows,
            ["state", "district", "taluka", "season_year", "event_date", "rainfall_mm"],
        )
        print(f"Normalized {len(dry_rows)} dry-spell rows -> {dry_out}")
        print(f"Normalized {len(heavy_rows)} heavy-rainfall rows -> {heavy_out}")
    elif args.command == "normalize-crop-csv":
        rows = normalize_crop_csv(Path(args.input_path), state_filter=args.state_filter)
        write_csv(
            Path(args.out),
            rows,
            ["state", "district", "crop", "season", "crop_year", "area_hectare", "production_tonne", "yield_kg_per_hectare"],
        )
        print(f"Normalized {len(rows)} crop-history rows -> {args.out}")
    elif args.command == "normalize-des-district-xlsx":
        rows = normalize_des_district_xlsx(Path(args.input_path), state_filter=args.state_filter)
        write_csv(
            Path(args.out),
            rows,
            ["state", "district", "crop", "season", "crop_year", "area_hectare", "production_tonne", "yield_kg_per_hectare"],
        )
        print(f"Normalized {len(rows)} DES crop-history rows -> {args.out}")
    elif args.command == "normalize-aspirational-districts":
        rows = normalize_aspirational_districts(Path(args.input_path))
        write_csv(Path(args.out), rows, ["state", "district"])
        print(f"Normalized {len(rows)} aspirational district rows -> {args.out}")


def fetch_data_gov_records(resource_url: str, api_key: str, limit: int, total: int) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    session = requests.Session()
    for offset in range(0, total, limit):
        response = session.get(
            resource_url,
            params={"api-key": api_key, "format": "json", "limit": limit, "offset": offset},
            timeout=60,
        )
        response.raise_for_status()
        payload = response.json()
        batch = payload.get("records") or []
        records.extend(batch)
        if len(batch) < limit:
            break
    return records


def fetch_maharain_range(
    start_year: int,
    end_year: int,
    out_dir: Path,
    *,
    verify_tls: bool = True,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    if not verify_tls:
        disable_warnings(InsecureRequestWarning)
    dry_rows: list[dict[str, Any]] = []
    heavy_rows: list[dict[str, Any]] = []
    for year in range(start_year, end_year + 1):
        dry_html = fetch_maharain_html(MAHARAIN_DRY_SPELL_URL, year, verify_tls=verify_tls)
        heavy_html = fetch_maharain_html(MAHARAIN_HEAVY_RAIN_URL, year, verify_tls=verify_tls)
        write_text(out_dir / f"dryspell_{year}.html", dry_html)
        write_text(out_dir / f"heavy_rainfall_{year}.html", heavy_html)
        dry_rows.extend(parse_dryspell_html(dry_html, year))
        heavy_rows.extend(parse_heavy_rainfall_html(heavy_html, year))
    return dry_rows, heavy_rows


def fetch_maharain_html(url: str, year: int, *, verify_tls: bool = True) -> str:
    response = requests.post(
        url,
        data={"year": str(year)},
        headers={"User-Agent": "KisanAIHackathon/1.0"},
        verify=verify_tls,
        timeout=60,
    )
    response.raise_for_status()
    return response.text


def parse_dryspell_html(html: str, year: int) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    last_district = ""
    for cells in _data_rows(html):
        if len(cells) < 4:
            continue
        district = cells[1] or last_district
        taluka = cells[2]
        if district:
            last_district = district
        for event in cells[3:]:
            match = re.search(r"(\d{2}-\d{2}-\d{4})\s+To\s+(\d{2}-\d{2}-\d{4})\s+\((\d+)\)", event)
            if not match:
                continue
            rows.append(
                {
                    "state": "Maharashtra",
                    "district": district,
                    "taluka": taluka,
                    "season_year": year,
                    "start_date": _date(match.group(1)),
                    "end_date": _date(match.group(2)),
                    "duration_days": match.group(3),
                }
            )
    return rows


def parse_heavy_rainfall_html(html: str, year: int) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    last_district = ""
    for cells in _data_rows(html):
        if len(cells) < 4:
            continue
        district = cells[1] or last_district
        taluka = cells[2]
        if district:
            last_district = district
        for event in cells[3:]:
            match = re.search(r"(\d{2}-\d{2}-\d{4})\s+\(([0-9.]+)\)", event)
            if not match:
                continue
            rows.append(
                {
                    "state": "Maharashtra",
                    "district": district,
                    "taluka": taluka,
                    "season_year": year,
                    "event_date": _date(match.group(1)),
                    "rainfall_mm": match.group(2),
                }
            )
    return rows


def _data_rows(html: str) -> list[list[str]]:
    rows: list[list[str]] = []
    for chunk in re.split(r"<tr[^>]*>", html, flags=re.IGNORECASE):
        cells = re.findall(r"<t[dh][^>]*>(.*?)</t[dh]>", chunk, flags=re.IGNORECASE | re.DOTALL)
        cleaned = [_strip_html(cell) for cell in cells]
        if cleaned and cleaned[0].isdigit():
            rows.append(cleaned)
    if rows:
        return rows
    parser = TableParser()
    parser.feed(html)
    return [row for row in parser.rows if row and row[0].isdigit()]


def _strip_html(value: str) -> str:
    value = re.sub(r"<[^>]+>", "", value)
    return " ".join(value.replace("&nbsp;", " ").split())


def load_imd_subdivision(path: Path) -> list[dict[str, Any]]:
    if path.suffix.lower() == ".json":
        with path.open(encoding="utf-8") as handle:
            payload = json.load(handle)
        records = payload.get("records") if isinstance(payload, dict) else payload
        return normalize_imd_subdivision_records(records or [])
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return normalize_imd_subdivision_records(list(csv.DictReader(handle)))


def normalize_imd_subdivision_records(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for record in records:
        normalized = {_clean_key(key): value for key, value in record.items()}
        subdivision = _pick(normalized, "subdivision", "sub_division", "sub-division")
        year = _pick(normalized, "year")
        if not subdivision or not year:
            continue
        for month_key, month in MONTH_COLUMNS.items():
            rows.append(
                {
                    "subdivision": subdivision,
                    "year": _int_year(str(year)),
                    "month": month,
                    "rainfall_mm": _number(_pick(normalized, month_key)),
                }
            )
    return rows


def normalize_crop_csv(path: Path, *, state_filter: str | None = None) -> list[dict[str, Any]]:
    with path.open(newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle)
        records = list(reader)
        headers = reader.fieldnames or []
    if "Year" in headers:
        return _normalize_year_wise_crop(records, state_filter=state_filter)
    return _normalize_crop_wide(records, headers, state_filter=state_filter)


def _normalize_crop_wide(
    records: list[dict[str, str]],
    headers: list[str],
    *,
    state_filter: str | None,
) -> list[dict[str, Any]]:
    years = sorted(
        {
            match.group(2)
            for header in headers
            if (match := re.match(r"^(Area|Production|Yield)-(\d{4}-\d{2})$", header))
        }
    )
    rows: list[dict[str, Any]] = []
    for record in records:
        state = _clean(record.get("State")) or "All India"
        if state_filter and state.lower() != state_filter.lower():
            continue
        crop = _clean(record.get("Crop"))
        season = _clean(record.get("Season"))
        if not crop or not season:
            continue
        for year_label in years:
            row = _crop_row(
                state=state,
                district=_clean(record.get("District")),
                crop=crop,
                season=season,
                crop_year=_int_year(year_label),
                area=record.get(f"Area-{year_label}"),
                production=record.get(f"Production-{year_label}"),
                yield_value=record.get(f"Yield-{year_label}"),
            )
            if _has_crop_measure(row):
                rows.append(row)
    return rows


def _normalize_year_wise_crop(records: list[dict[str, str]], *, state_filter: str | None) -> list[dict[str, Any]]:
    if state_filter and state_filter.lower() != "all india":
        return []
    rows: list[dict[str, Any]] = []
    for record in records:
        year = _int_year(record.get("Year") or "")
        season = _clean(record.get("Season"))
        for key in record:
            match = re.match(r"(.+)-Area$", key)
            if not match:
                continue
            crop = match.group(1)
            row = _crop_row(
                state="All India",
                district=None,
                crop=crop,
                season=season,
                crop_year=year,
                area=record.get(f"{crop}-Area"),
                production=record.get(f"{crop}-Production"),
                yield_value=record.get(f"{crop}-Yield"),
            )
            if _has_crop_measure(row):
                rows.append(row)
    return rows


def normalize_des_district_xlsx(path: Path, *, state_filter: str | None = None) -> list[dict[str, Any]]:
    rows = _xlsx_rows(path)
    header_index = next(
        index
        for index, row in enumerate(rows)
        if len(row) >= 7 and row[0] == "State" and row[1] == "District" and row[2] == "Crop"
    )
    year_label = _clean(rows[header_index][4]) or "2024-25"
    output: list[dict[str, Any]] = []
    for row in rows[header_index + 1 :]:
        if len(row) < 7:
            continue
        state, district, crop, season = map(_clean, row[:4])
        if not state or not district or not crop or not season:
            continue
        if state_filter and state.lower() != state_filter.lower():
            continue
        crop_row = _crop_row(
            state=state,
            district=district,
            crop=crop,
            season=season,
            crop_year=_int_year(year_label),
            area=row[4],
            production=row[5],
            yield_value=row[6],
        )
        if _has_crop_measure(crop_row):
            output.append(crop_row)
    return output


def normalize_aspirational_districts(path: Path) -> list[dict[str, Any]]:
    with path.open(newline="", encoding="utf-8-sig") as handle:
        rows = []
        for record in csv.DictReader(handle):
            state = _clean(record.get("statename") or record.get("state"))
            district = _clean(record.get("districtname") or record.get("district"))
            if state and district:
                rows.append({"state": state.title(), "district": district.title()})
        return rows


def _xlsx_rows(path: Path) -> list[list[str]]:
    ns = {"a": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}
    with ZipFile(path) as archive:
        names = archive.namelist()
        shared: list[str] = []
        if "xl/sharedStrings.xml" in names:
            root = ET.fromstring(archive.read("xl/sharedStrings.xml"))
            for item in root.findall("a:si", ns):
                shared.append("".join(text.text or "" for text in item.findall(".//a:t", ns)))
        sheet_name = next(name for name in names if name.startswith("xl/worksheets/sheet"))
        root = ET.fromstring(archive.read(sheet_name))
        rows: list[list[str]] = []
        for row in root.findall(".//a:row", ns):
            values_by_index: dict[int, str] = {}
            for cell in row.findall("a:c", ns):
                value = cell.find("a:v", ns)
                text = "" if value is None else value.text or ""
                if cell.get("t") == "s" and text:
                    text = shared[int(text)]
                values_by_index[_column_index(cell.get("r") or "")] = text
            max_index = max(values_by_index, default=-1)
            rows.append([values_by_index.get(index, "") for index in range(max_index + 1)])
        return rows


def _column_index(cell_ref: str) -> int:
    letters = "".join(ch for ch in cell_ref if ch.isalpha())
    index = 0
    for char in letters:
        index = index * 26 + (ord(char.upper()) - ord("A") + 1)
    return max(index - 1, 0)


def _crop_row(
    *,
    state: str,
    district: str | None,
    crop: str,
    season: str | None,
    crop_year: int,
    area: str | None,
    production: str | None,
    yield_value: str | None,
) -> dict[str, Any]:
    return {
        "state": state,
        "district": district,
        "crop": crop,
        "season": season,
        "crop_year": crop_year,
        "area_hectare": _number(area),
        "production_tonne": _number(production),
        "yield_kg_per_hectare": _number(yield_value),
    }


def _has_crop_measure(row: dict[str, Any]) -> bool:
    return any(row.get(key) not in {None, ""} for key in ("area_hectare", "production_tonne", "yield_kg_per_hectare"))


def write_csv(path: Path, rows: list[dict[str, Any]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def write_json(path: Path, payload: Any) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, ensure_ascii=False, indent=2)
    return path


def write_text(path: Path, text: str) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return path


def _pick(record: dict[str, Any], *names: str) -> Any:
    for name in names:
        value = record.get(_clean_key(name))
        if value not in {None, ""}:
            return value
    return None


def _clean_key(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", value.strip().lower()).strip("_")


def _clean(value: Any) -> str | None:
    if value is None:
        return None
    cleaned = " ".join(str(value).strip().split())
    return cleaned or None


def _number(value: Any) -> str | None:
    cleaned = _clean(value)
    if not cleaned:
        return None
    cleaned = cleaned.replace(",", "")
    if cleaned in {"-", "--", "NA", "N/A", "nan"}:
        return None
    float(cleaned)
    return cleaned


def _date(value: str) -> str:
    return datetime.strptime(value, "%d-%m-%Y").date().isoformat()


def _int_year(value: str) -> int:
    match = re.search(r"\d{4}", value)
    if not match:
        raise ValueError(f"Could not parse year from {value!r}")
    return int(match.group(0))


if __name__ == "__main__":
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
    main()
