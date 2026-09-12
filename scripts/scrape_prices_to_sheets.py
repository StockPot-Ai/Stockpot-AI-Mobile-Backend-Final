#!/usr/bin/env python3
"""Fetch today's Cargills and Keells fruit/vegetable prices into Google Sheets.

The script creates/updates two tabs:
  1. Daily Prices      - tidy long-format data for analysis
  2. Daily Comparison  - exact normalized-name matches side by side

Re-running on the same date replaces that date's rows, so it is safe to schedule
daily without creating same-day duplicates.
"""

from __future__ import annotations

import argparse
import base64
import http.cookiejar
import json
import os
import re
import ssl
import sys
import time
import unicodedata
import urllib.parse
import urllib.request
from collections import defaultdict
from datetime import date, datetime
from pathlib import Path
from typing import Any
from datetime import date, datetime, timedelta, timezone

TIMEZONE = timezone(timedelta(hours=5, minutes=30), name="Asia/Colombo")

CARGILLS_BASE_URL = "https://cargillsonline.com"
CARGILLS_PAGE_SIZE = 10000
CARGILLS_TARGET_CATEGORIES = {"fruits", "vegetables"}

KEELLS_LOGIN_URL = "https://zebraliveback.keellssuper.com/1.0/Login/GuestLogin"
KEELLS_ITEMS_URL = "https://zebraliveback.keellssuper.com/2.0/WebV2/GetItemDetails"
KEELLS_DEPARTMENTS = {
    "Fruits": {"department_id": 6, "expected_code": "F"},
    "Vegetables": {"department_id": 16, "expected_code": "V"},
}
KEELLS_ITEMS_PER_PAGE = 100

PRICE_HEADERS = [
    "Snapshot Date",
    "Store",
    "Location / Outlet",
    "Category",
    "Product Name",
    "Match Key",
    "Product Code",
    "Price (LKR)",
    "Regular Price (LKR)",
    "Discount (LKR)",
    "Discount (%)",
    "On Offer",
    "UOM",
    "Unit Size",
    "Stock",
    "Available",
]

COMPARISON_HEADERS = [
    "Snapshot Date",
    "Category",
    "Match Key",
    "Cargills Product",
    "Cargills Price (LKR)",
    "Cargills Discount (%)",
    "Keells Product",
    "Keells Price (LKR)",
    "Keells Discount (%)",
    "Cargills - Keells (LKR)",
    "Cheaper Store",
    "Match Status",
]


def clean_text(value: Any) -> str:
    return re.sub(r"\s+", " ", str(value or "")).strip()


def normalize_name(value: Any) -> str:
    """Normalize only formatting differences; do not fuzzy-match different names."""
    text = unicodedata.normalize("NFKC", clean_text(value)).casefold()
    text = text.replace("&", " and ")
    text = re.sub(r"(?<=\d)\s*(kg|g|mg|ml|l)\b", r" \1", text)
    text = re.sub(r"[^a-z0-9]+", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def to_float(value: Any, default: float = 0.0) -> float:
    try:
        if value is None or value == "":
            return default
        return float(str(value).replace(",", "").strip())
    except (TypeError, ValueError):
        return default


def to_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    return str(value).strip().casefold() in {"true", "1", "yes", "y"}


def parse_percent(value: Any) -> float:
    """Return a spreadsheet percentage decimal: '40.00%' -> 0.40."""
    text = clean_text(value).replace("%", "")
    if not text:
        return 0.0
    return to_float(text) / 100.0


def decode_base64(value: Any) -> str:
    text = clean_text(value)
    if not text:
        return ""
    try:
        text += "=" * (-len(text) % 4)
        return base64.b64decode(text).decode("utf-8")
    except Exception:
        return clean_text(value)


class JsonHttpClient:
    def __init__(self, headers: dict[str, str], use_cookies: bool = True):
        self.headers = headers
        self.context = ssl.create_default_context()
        self.cookie_jar = http.cookiejar.CookieJar()
        handlers = [urllib.request.HTTPSHandler(context=self.context)]
        if use_cookies:
            handlers.append(urllib.request.HTTPCookieProcessor(self.cookie_jar))
        self.opener = urllib.request.build_opener(*handlers)

    def request_json(
        self,
        method: str,
        url: str,
        *,
        params: dict[str, Any] | None = None,
        payload: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
        attempts: int = 3,
    ) -> Any:
        if params:
            url = f"{url}?{urllib.parse.urlencode(params)}"
        body = None
        if method.upper() == "POST":
            body = json.dumps(payload).encode("utf-8") if payload is not None else b""
        merged_headers = dict(self.headers)
        merged_headers.update(headers or {})

        last_error: Exception | None = None
        for attempt in range(1, attempts + 1):
            try:
                request = urllib.request.Request(
                    url,
                    data=body,
                    headers=merged_headers,
                    method=method.upper(),
                )
                with self.opener.open(request, timeout=90) as response:
                    raw = response.read().decode("utf-8", errors="replace")
                try:
                    return json.loads(raw)
                except json.JSONDecodeError:
                    cleaned = "".join(char if ord(char) >= 32 else " " for char in raw)
                    return json.loads(cleaned)
            except Exception as exc:
                last_error = exc
                if attempt < attempts:
                    time.sleep(attempt * 2)
        raise RuntimeError(f"Request failed after {attempts} attempts: {url}: {last_error}")


class CargillsClient:
    def __init__(self, location: str):
        self.location = location
        self.http = JsonHttpClient(
            {
                "User-Agent": (
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 Chrome/142.0.0.0 Safari/537.36"
                ),
                "Accept": "application/json, text/plain, */*",
                "Content-Type": "application/json",
                "Origin": CARGILLS_BASE_URL,
                "Referer": f"{CARGILLS_BASE_URL}/",
            }
        )

    @staticmethod
    def category_name(category: dict[str, Any]) -> str:
        return clean_text(
            category.get("MenuCategoryName")
            or decode_base64(category.get("EnMenuCategoryName"))
        )

    def fetch(self, snapshot_date: str) -> list[dict[str, Any]]:
        self.http.request_json(
            "POST",
            f"{CARGILLS_BASE_URL}/Web/CheckDeliveryOptionV1/",
            payload={"PinCode": self.location},
        )
        categories = self.http.request_json(
            "POST",
            f"{CARGILLS_BASE_URL}/Web/GetCategoriesV1/",
            payload={},
        )
        if not isinstance(categories, list):
            raise RuntimeError(f"Unexpected Cargills category response: {categories}")

        selected = [
            category
            for category in categories
            if normalize_name(self.category_name(category)) in CARGILLS_TARGET_CATEGORIES
        ]
        found = {normalize_name(self.category_name(category)) for category in selected}
        missing = CARGILLS_TARGET_CATEGORIES - found
        if missing:
            raise RuntimeError(f"Cargills categories not found: {sorted(missing)}")

        records: list[dict[str, Any]] = []
        seen_codes: set[str] = set()
        for category in selected:
            category_name = self.category_name(category)
            category_id = category.get("EnId") or category.get("Id") or ""
            products = self.http.request_json(
                "POST",
                f"{CARGILLS_BASE_URL}/Web/GetMenuCategoryItemsPagingV3/",
                payload={
                    "CategoryId": category_id,
                    "Search": "",
                    "Filter": "",
                    "PageIndex": 1,
                    "PageSize": CARGILLS_PAGE_SIZE,
                    "BannerId": "",
                    "SectionId": "",
                    "CollectionId": "",
                    "SectionType": "",
                    "DataType": "",
                    "SubCatId": "",
                    "PromoId": "",
                },
            )
            if not isinstance(products, list):
                raise RuntimeError(f"Unexpected Cargills product response for {category_name}")

            for item in products:
                if not isinstance(item, dict):
                    continue
                product_name = clean_text(item.get("ItemName"))
                product_code = clean_text(item.get("SKUCODE"))
                if not product_name or not product_code or product_name == "No Products Found":
                    continue
                if product_code in seen_codes:
                    continue
                seen_codes.add(product_code)

                price = to_float(item.get("Price"))
                mrp = to_float(item.get("Mrp"))
                regular_price = mrp if mrp > price else price
                discount_value = max(regular_price - price, 0.0)
                discount_percent = parse_percent(item.get("DiscountAmount"))
                if not discount_percent and regular_price > 0:
                    discount_percent = discount_value / regular_price
                stock = to_float(item.get("Inventory"))
                available = to_bool(item.get("IsSaleable")) and stock > 0

                records.append(
                    {
                        "snapshot_date": snapshot_date,
                        "store": "Cargills",
                        "location": self.location,
                        "category": category_name,
                        "product_name": product_name,
                        "match_key": normalize_name(product_name),
                        "product_code": product_code,
                        "price": round(price, 2),
                        "regular_price": round(regular_price, 2),
                        "discount_value": round(discount_value, 2),
                        "discount_percent": round(discount_percent, 6),
                        "on_offer": discount_value > 0 or discount_percent > 0,
                        "uom": clean_text(item.get("UOM")),
                        "unit_size": to_float(item.get("UnitSize")),
                        "stock": stock,
                        "available": available,
                    }
                )
            time.sleep(0.4)
        return records


class KeellsClient:
    def __init__(self, outlet_code: str):
        self.outlet_code = outlet_code
        self.http = JsonHttpClient(
            {
                "User-Agent": (
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 Chrome/142.0.0.0 Safari/537.36"
                ),
                "Accept": "application/json, text/plain, */*",
                "Content-Type": "application/json",
            }
        )
        self.user_session_id = ""

    def login(self) -> None:
        data = self.http.request_json("POST", KEELLS_LOGIN_URL)
        if to_float(data.get("statusCode")) != 200:
            raise RuntimeError(f"Keells guest login failed: {data}")
        self.user_session_id = clean_text(data.get("result", {}).get("userSessionID"))
        if not self.user_session_id:
            raise RuntimeError("Keells did not return a userSessionID")

    def fetch_department(
        self,
        category_name: str,
        department_id: int,
        expected_code: str,
        snapshot_date: str,
    ) -> list[dict[str, Any]]:
        base_params = {
            "itemsPerPage": KEELLS_ITEMS_PER_PAGE,
            "outletCode": self.outlet_code,
            "departmentId": department_id,
            "subDepartmentId": "",
            "categoryId": "",
            "itemDescription": "",
            "itemPricefrom": 0,
            "itemPriceTo": 99999999,
            "isFeatured": 0,
            "isPromotionOnly": "false",
            "promotionCategory": "",
            "sortBy": "default",
            "BrandId": "",
            "storeName": "",
            "subDeaprtmentCode": "",
            "isShowOutofStockItems": "true",
            "brandName": "",
        }
        headers = {
            "Accept": "application/json",
            "Origin": "https://www.keellssuper.com",
            "Referer": "https://www.keellssuper.com/",
            "usersessionid": self.user_session_id,
        }

        records: list[dict[str, Any]] = []
        seen_codes: set[str] = set()
        page_number = 1
        page_count = 1
        while page_number <= page_count:
            params = dict(base_params)
            params["pageNo"] = page_number
            data = self.http.request_json(
                "GET", KEELLS_ITEMS_URL, params=params, headers=headers
            )
            if to_float(data.get("statusCode")) != 200:
                raise RuntimeError(f"Keells item request failed: {data}")
            details = data.get("result", {}).get("itemDetailResult", {}) or {}
            page_count = int(to_float(details.get("pageCount")))
            items = details.get("itemDetails") or []

            for item in items:
                returned_code = clean_text(item.get("departmentCode"))
                if returned_code and returned_code != expected_code:
                    raise RuntimeError(
                        f"Keells department {department_id} changed: expected "
                        f"{expected_code}, received {returned_code}"
                    )
                product_name = clean_text(item.get("name"))
                product_code = clean_text(item.get("itemCode"))
                if not product_name or not product_code or product_code in seen_codes:
                    continue
                seen_codes.add(product_code)

                regular_price = to_float(item.get("amount"))
                discount_value = max(
                    to_float(item.get("promotionDiscountValue")),
                    to_float(item.get("discountValue")),
                )
                is_promotion = to_bool(item.get("isPromotionApplied")) or discount_value > 0
                price = max(regular_price - discount_value, 0.0) if is_promotion else regular_price
                discount_percent = (
                    discount_value / regular_price if regular_price > 0 else 0.0
                )
                stock = to_float(item.get("stockInHand"))
                available = (
                    to_bool(item.get("isAvailable"))
                    and to_bool(item.get("isSellingToday"))
                    and stock > 0
                )

                records.append(
                    {
                        "snapshot_date": snapshot_date,
                        "store": "Keells",
                        "location": self.outlet_code,
                        "category": category_name,
                        "product_name": product_name,
                        "match_key": normalize_name(product_name),
                        "product_code": product_code,
                        "price": round(price, 2),
                        "regular_price": round(regular_price, 2),
                        "discount_value": round(discount_value, 2),
                        "discount_percent": round(discount_percent, 6),
                        "on_offer": is_promotion,
                        "uom": clean_text(item.get("uom")),
                        "unit_size": "",
                        "stock": stock,
                        "available": available,
                    }
                )
            page_number += 1
            time.sleep(0.25)
        return records

    def fetch(self, snapshot_date: str) -> list[dict[str, Any]]:
        self.login()
        records: list[dict[str, Any]] = []
        for category_name, config in KEELLS_DEPARTMENTS.items():
            records.extend(
                self.fetch_department(
                    category_name,
                    config["department_id"],
                    config["expected_code"],
                    snapshot_date,
                )
            )
        return records


def record_to_price_row(record: dict[str, Any]) -> list[Any]:
    return [
        record["snapshot_date"],
        record["store"],
        record["location"],
        record["category"],
        record["product_name"],
        record["match_key"],
        record["product_code"],
        record["price"],
        record["regular_price"],
        record["discount_value"],
        record["discount_percent"],
        record["on_offer"],
        record["uom"],
        record["unit_size"],
        record["stock"],
        record["available"],
    ]


def build_comparison_rows(records: list[dict[str, Any]]) -> list[list[Any]]:
    grouped: dict[str, dict[str, list[dict[str, Any]]]] = defaultdict(
        lambda: {"Cargills": [], "Keells": []}
    )
    for record in records:
        grouped[record["match_key"]][record["store"]].append(record)

    rows: list[list[Any]] = []
    for match_key in sorted(grouped):
        stores = grouped[match_key]
        cargills = sorted(stores["Cargills"], key=lambda row: row["product_code"])
        keells = sorted(stores["Keells"], key=lambda row: row["product_code"])
        pair_count = max(len(cargills), len(keells))

        for index in range(pair_count):
            c = cargills[index] if index < len(cargills) else None
            k = keells[index] if index < len(keells) else None
            if c and k:
                difference: Any = round(c["price"] - k["price"], 2)
                if c["price"] < k["price"]:
                    cheaper = "Cargills"
                elif k["price"] < c["price"]:
                    cheaper = "Keells"
                else:
                    cheaper = "Same price"
                status = "Exact normalized-name match"
            elif c:
                difference = ""
                cheaper = ""
                status = "Cargills only"
            else:
                difference = ""
                cheaper = ""
                status = "Keells only"

            chosen = c or k
            rows.append(
                [
                    chosen["snapshot_date"],
                    chosen["category"],
                    match_key,
                    c["product_name"] if c else "",
                    c["price"] if c else "",
                    c["discount_percent"] if c else "",
                    k["product_name"] if k else "",
                    k["price"] if k else "",
                    k["discount_percent"] if k else "",
                    difference,
                    cheaper,
                    status,
                ]
            )
    return rows


def column_letter(column_number: int) -> str:
    result = ""
    while column_number:
        column_number, remainder = divmod(column_number - 1, 26)
        result = chr(65 + remainder) + result
    return result


def format_worksheet(spreadsheet: Any, worksheet: Any, headers: list[str], row_count: int) -> None:
    sheet_id = worksheet.id
    column_count = len(headers)
    requests: list[dict[str, Any]] = [
        {
            "updateSheetProperties": {
                "properties": {
                    "sheetId": sheet_id,
                    "gridProperties": {"frozenRowCount": 1},
                },
                "fields": "gridProperties.frozenRowCount",
            }
        },
        {"clearBasicFilter": {"sheetId": sheet_id}},
        {
            "setBasicFilter": {
                "filter": {
                    "range": {
                        "sheetId": sheet_id,
                        "startRowIndex": 0,
                        "endRowIndex": max(row_count, 1),
                        "startColumnIndex": 0,
                        "endColumnIndex": column_count,
                    }
                }
            }
        },
        {
            "repeatCell": {
                "range": {
                    "sheetId": sheet_id,
                    "startRowIndex": 0,
                    "endRowIndex": 1,
                    "startColumnIndex": 0,
                    "endColumnIndex": column_count,
                },
                "cell": {
                    "userEnteredFormat": {
                        "backgroundColor": {"red": 0.12, "green": 0.38, "blue": 0.24},
                        "textFormat": {
                            "foregroundColor": {"red": 1, "green": 1, "blue": 1},
                            "bold": True,
                        },
                        "horizontalAlignment": "CENTER",
                    }
                },
                "fields": "userEnteredFormat(backgroundColor,textFormat,horizontalAlignment)",
            }
        },
    ]

    currency_columns = [i for i, header in enumerate(headers) if "(LKR)" in header]
    percent_columns = [i for i, header in enumerate(headers) if "(%)" in header]
    for column in currency_columns:
        requests.append(
            {
                "repeatCell": {
                    "range": {
                        "sheetId": sheet_id,
                        "startRowIndex": 1,
                        "endRowIndex": max(row_count, 2),
                        "startColumnIndex": column,
                        "endColumnIndex": column + 1,
                    },
                    "cell": {
                        "userEnteredFormat": {
                            "numberFormat": {"type": "NUMBER", "pattern": "#,##0.00"}
                        }
                    },
                    "fields": "userEnteredFormat.numberFormat",
                }
            }
        )
    for column in percent_columns:
        requests.append(
            {
                "repeatCell": {
                    "range": {
                        "sheetId": sheet_id,
                        "startRowIndex": 1,
                        "endRowIndex": max(row_count, 2),
                        "startColumnIndex": column,
                        "endColumnIndex": column + 1,
                    },
                    "cell": {
                        "userEnteredFormat": {
                            "numberFormat": {"type": "PERCENT", "pattern": "0.00%"}
                        }
                    },
                    "fields": "userEnteredFormat.numberFormat",
                }
            }
        )

    for index, header in enumerate(headers):
        if "Product" in header or header == "Match Key":
            width = 240
        elif header in {"Location / Outlet", "Match Status"}:
            width = 150
        elif header in {"Snapshot Date", "Category", "Cheaper Store"}:
            width = 120
        else:
            width = 105
        requests.append(
            {
                "updateDimensionProperties": {
                    "range": {
                        "sheetId": sheet_id,
                        "dimension": "COLUMNS",
                        "startIndex": index,
                        "endIndex": index + 1,
                    },
                    "properties": {"pixelSize": width},
                    "fields": "pixelSize",
                }
            }
        )
    spreadsheet.batch_update({"requests": requests})


def upsert_date_rows(
    spreadsheet: Any,
    sheet_title: str,
    headers: list[str],
    new_rows: list[list[Any]],
    snapshot_date: str,
) -> Any:
    try:
        worksheet = spreadsheet.worksheet(sheet_title)
    except Exception:
        worksheet = spreadsheet.add_worksheet(
            title=sheet_title,
            rows=max(len(new_rows) + 200, 1000),
            cols=len(headers),
        )

    existing = worksheet.get_all_values()
    retained: list[list[Any]] = []
    if existing and existing[0] == headers:
        retained = [row for row in existing[1:] if row and row[0] != snapshot_date]

    values = [headers] + retained + new_rows
    worksheet.clear()
    worksheet.resize(rows=max(len(values) + 100, 1000), cols=len(headers))
    last_cell = f"{column_letter(len(headers))}{len(values)}"
    worksheet.update(
        values=values,
        range_name=f"A1:{last_cell}",
        value_input_option="USER_ENTERED",
    )
    format_worksheet(spreadsheet, worksheet, headers, len(values))
    return worksheet


def upload_to_google_sheets(
    price_rows: list[list[Any]],
    comparison_rows: list[list[Any]],
    snapshot_date: str,
    credentials_file: Path,
    token_file: Path,
    auth_mode: str,
    spreadsheet_id: str,
    spreadsheet_title: str,
    share_with: str,
) -> str:
    try:
        import gspread
    except ImportError as exc:
        raise RuntimeError(
            "Missing Google dependency. Run: pip install gspread google-auth"
        ) from exc

    if auth_mode == "auto":
        with credentials_file.open("r", encoding="utf-8") as file:
            credential_type = json.load(file).get("type", "")
        auth_mode = "service-account" if credential_type == "service_account" else "oauth"

    if auth_mode == "service-account":
        client = gspread.service_account(filename=str(credentials_file))
    else:
        token_file.parent.mkdir(parents=True, exist_ok=True)
        client = gspread.oauth(
            credentials_filename=str(credentials_file),
            authorized_user_filename=str(token_file),
        )
    created = False
    if spreadsheet_id:
        spreadsheet = client.open_by_key(spreadsheet_id)
    else:
        spreadsheet = client.create(spreadsheet_title)
        created = True
        if share_with:
            spreadsheet.share(share_with, perm_type="user", role="writer", notify=True)

    upsert_date_rows(
        spreadsheet, "Daily Prices", PRICE_HEADERS, price_rows, snapshot_date
    )
    upsert_date_rows(
        spreadsheet,
        "Daily Comparison",
        COMPARISON_HEADERS,
        comparison_rows,
        snapshot_date,
    )

    if created:
        try:
            default_sheet = spreadsheet.worksheet("Sheet1")
            if not default_sheet.get_all_values():
                spreadsheet.del_worksheet(default_sheet)
        except Exception:
            pass
    return spreadsheet.url


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--credentials",
        default=os.getenv("GOOGLE_SERVICE_ACCOUNT_FILE", ""),
        help="Path to a Google service-account or OAuth client JSON file",
    )
    parser.add_argument(
        "--auth",
        choices=["auto", "service-account", "oauth"],
        default="auto",
        help="Google credential type; auto detects service-account vs OAuth client JSON",
    )
    parser.add_argument(
        "--token-file",
        default=os.getenv("GOOGLE_AUTHORIZED_USER_FILE", "google-authorized-user.json"),
        help="OAuth token cache used after the first browser authorization",
    )
    parser.add_argument(
        "--spreadsheet-id",
        default=os.getenv("GOOGLE_SPREADSHEET_ID", ""),
        help="Existing Google Sheet ID; omit to create a new spreadsheet",
    )
    parser.add_argument(
        "--spreadsheet-title",
        default="Sri Lanka Supermarket Fruit and Vegetable Prices",
    )
    parser.add_argument(
        "--share-with",
        default=os.getenv("GOOGLE_SHARE_WITH", ""),
        help="Email to share a newly created spreadsheet with",
    )
    parser.add_argument("--cargills-location", default="Colombo")
    parser.add_argument("--keells-outlet", default="SCDR")
    parser.add_argument(
        "--date",
        default=datetime.now(TIMEZONE).date().isoformat(),
        help="Snapshot date in YYYY-MM-DD format",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Fetch and validate data without writing to Google Sheets",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        date.fromisoformat(args.date)
    except ValueError:
        raise SystemExit("--date must use YYYY-MM-DD")

    print(f"Fetching Cargills ({args.cargills_location})...")
    cargills_records = CargillsClient(args.cargills_location).fetch(args.date)
    print(f"Cargills records: {len(cargills_records)}")

    print(f"Fetching Keells ({args.keells_outlet})...")
    keells_records = KeellsClient(args.keells_outlet).fetch(args.date)
    print(f"Keells records: {len(keells_records)}")

    records = sorted(
        cargills_records + keells_records,
        key=lambda row: (row["category"], row["match_key"], row["store"], row["product_code"]),
    )
    price_rows = [record_to_price_row(record) for record in records]
    comparison_rows = build_comparison_rows(records)
    exact_matches = sum(row[-1] == "Exact normalized-name match" for row in comparison_rows)

    print(f"Daily Prices rows: {len(price_rows)}")
    print(f"Daily Comparison rows: {len(comparison_rows)}")
    print(f"Exact normalized-name matches: {exact_matches}")

    if args.dry_run:
        print("Dry run successful; Google Sheets was not changed.")
        return 0

    if not args.credentials:
        raise SystemExit(
            "Provide --credentials or set GOOGLE_SERVICE_ACCOUNT_FILE. "
            "Use --dry-run to test without Google credentials."
        )
    credentials_file = Path(args.credentials).expanduser().resolve()
    if not credentials_file.is_file():
        raise SystemExit(f"Credentials file not found: {credentials_file}")

    sheet_url = upload_to_google_sheets(
        price_rows,
        comparison_rows,
        args.date,
        credentials_file,
        Path(args.token_file).expanduser().resolve(),
        args.auth,
        args.spreadsheet_id,
        args.spreadsheet_title,
        args.share_with,
    )
    print(f"Google Sheet updated: {sheet_url}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except KeyboardInterrupt:
        print("Cancelled.", file=sys.stderr)
        raise SystemExit(130)
