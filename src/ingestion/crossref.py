from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from core.config import Settings


@dataclass(frozen=True)
class PaperRecord:
    paper_id: str
    title: str
    summary: str
    authors: list[str]
    categories: list[str]
    primary_category: str
    published: str
    updated: str
    abs_url: str
    pdf_url: str
    comment: str


def parse_crossref_payload(payload: dict) -> list[PaperRecord]:
    """TODO(student): parse Crossref payload thanh list PaperRecord.

    Pseudo-code:
    1. Duyet `payload["message"]["items"]`.
    2. Lay DOI, title, abstract, authors, subject, dates, URLs.
    3. Chuan hoa text va bo record khong hop le.
    4. Tra ve list `PaperRecord`.
    """
    import re
    
    def clean_text(text: str) -> str:
        if not text:
            return ""
        text = re.sub(r'<[^>]+>', '', str(text))
        return " ".join(text.split())

    records = []
    items = payload.get("message", {}).get("items", [])
    
    for item in items:
        doi = item.get("DOI")
        title_list = item.get("title", [])
        if not doi or not title_list:
            continue
            
        title = clean_text(title_list[0])
        summary = clean_text(item.get("abstract", ""))
        
        authors = []
        for author in item.get("author", []):
            given = author.get("given", "")
            family = author.get("family", "")
            name = f"{given} {family}".strip()
            if name:
                authors.append(name)
                
        categories = item.get("subject", [])
        if not isinstance(categories, list):
            categories = [categories] if categories else []
        primary_category = categories[0] if categories else ""
        
        published = ""
        if "published-print" in item and "date-parts" in item["published-print"]:
            parts = item["published-print"]["date-parts"][0]
            published = "-".join(f"{p:02d}" for p in parts)
        elif "published-online" in item and "date-parts" in item["published-online"]:
            parts = item["published-online"]["date-parts"][0]
            published = "-".join(f"{p:02d}" for p in parts)
        elif "created" in item and "date-time" in item["created"]:
            published = str(item["created"]["date-time"]).split("T")[0]
            
        updated = ""
        if "deposited" in item and "date-time" in item["deposited"]:
            updated = str(item["deposited"]["date-time"]).split("T")[0]
            
        abs_url = item.get("URL", f"https://doi.org/{doi}")
        pdf_url = ""
        for link in item.get("link", []):
            if link.get("content-type") == "application/pdf":
                pdf_url = link.get("URL", "")
                break
                
        comment = ""
        
        records.append(PaperRecord(
            paper_id=str(doi),
            title=title,
            summary=summary,
            authors=authors,
            categories=categories,
            primary_category=primary_category,
            published=published,
            updated=updated,
            abs_url=abs_url,
            pdf_url=pdf_url,
            comment=comment
        ))
        
    return records


def fetch_source_records(settings: Settings) -> list[PaperRecord]:
    """TODO(student): goi source API, luu raw response, parse thanh records.

    Pseudo-code:
    1. Tao params tu `settings.source_query`, `settings.source_filter`, `settings.max_results`.
    2. Goi API voi retry cho cac status code nhu 429/503.
    3. Luu raw response vao `settings.paths.raw_api_response`.
    4. Parse payload bang `parse_crossref_payload`.
    5. Luu records vao `settings.paths.raw_records_json`.
    """
    import json
    import time
    import requests

    # 1. Build query params
    params = {
        "query": settings.source_query,
        "filter": settings.source_filter,
        "rows": settings.max_results,
    }
    url = "https://api.crossref.org/works"

    # 2. Call API with retry on 429/503
    max_retries = 5
    response = None
    for attempt in range(max_retries):
        response = requests.get(url, params=params, timeout=30)
        if response.status_code in (429, 503):
            wait = 2 ** attempt
            time.sleep(wait)
            continue
        response.raise_for_status()
        break
    else:
        response.raise_for_status()

    payload = response.json()

    # 3. Save raw response
    settings.paths.raw_api_response.parent.mkdir(parents=True, exist_ok=True)
    settings.paths.raw_api_response.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    # 4. Parse payload
    records = parse_crossref_payload(payload)

    # 5. Save records
    from dataclasses import asdict

    settings.paths.raw_records_json.parent.mkdir(parents=True, exist_ok=True)
    settings.paths.raw_records_json.write_text(
        json.dumps([asdict(r) for r in records], ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    return records


def load_raw_records(path: Path) -> list[PaperRecord]:
    """TODO(student): doc JSON snapshot va map thanh `PaperRecord`."""
    import json

    data = json.loads(path.read_text(encoding="utf-8"))
    return [PaperRecord(**record) for record in data]
