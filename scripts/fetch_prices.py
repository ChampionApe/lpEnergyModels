"""Utility functions and CLI tool to fetch Danish day-ahead electricity prices
from Energi Data Service (https://www.energidataservice.dk/).

Focus: Elspot (day-ahead) prices for DK1 / DK2 with conversion to €/GJ so they
can be compared directly to model marginal prices produced by MBasicInt.

Features:
- Fetch and paginate Elspotprices dataset via public API.
- Filter for selected PriceArea list (default: DK1, DK2).
- Convert SpotPriceEUR (€/MWh) to SpotPriceGJ (€/GJ).
- Handle DST duplication (8784 hours) by collapsing duplicate local hours.
- Provide helpers to: pivot wide, assign model hour index (h0001..hXXXX),
  compute quantiles, normalize to mean = 1 shape.
- Optional CLI to save raw long format and a wide pivot CSV.

No external dependency beyond pandas & (optional) requests. Falls back to
urllib if requests not installed.

Example (Python):
    from scripts.fetch_prices import fetch_elspot_prices, prepare_model_hours
    df = fetch_elspot_prices('2024-01-01','2024-12-31', areas=('DK1',))
    df_h = prepare_model_hours(df, area='DK1')
    print(df_h.head())

CLI Example:
    python scripts/fetch_prices.py --start 2024-01-01 --end 2024-12-31 --areas DK1 DK2 \
        --out-long data/elspot_2024_long.csv --out-wide data/elspot_2024_wide.csv

"""
from __future__ import annotations

import json
import math
import sys
import argparse
from dataclasses import dataclass
from typing import Iterable, List, Optional, Sequence
from urllib.parse import quote
from urllib.request import urlopen
from urllib.error import URLError, HTTPError

try:  # optional
    import requests  # type: ignore
except ImportError:  # pragma: no cover
    requests = None  # fall back to urllib

import pandas as pd

API_BASE = "https://api.energidataservice.dk/dataset/Elspotprices"


@dataclass
class FetchResult:
    df: pd.DataFrame
    url_examples: List[str]


def _http_get(url: str, timeout: int = 60) -> dict:
    """Return JSON dict for url using requests if available, else urllib."""
    if requests is not None:
        r = requests.get(url, timeout=timeout)
        r.raise_for_status()
        return r.json()
    with urlopen(url, timeout=timeout) as resp:  # pragma: no cover (fallback)
        data = resp.read().decode("utf-8")
    return json.loads(data)


def fetch_elspot_prices(
    start: str,
    end: str,
    areas: Sequence[str] = ("DK1", "DK2"),
    limit: int = 100_000,
    include_local: bool = True,
    to_gj: bool = True,
    verbose: bool = True,
) -> pd.DataFrame:
    """Fetch hourly day-ahead spot prices.

    Parameters
    ----------
    start, end : str
        Date strings (YYYY-MM-DD). 'end' inclusive (API semantics).
    areas : sequence
        List/tuple of PriceArea values (e.g. ("DK1","DK2")).
    limit : int
        Rows per request page (API default 100k). One year * 2 areas ~ 17.5k rows.
    include_local : bool
        Include HourDK column (local time) if present.
    to_gj : bool
        Add SpotPriceGJ = SpotPriceEUR / 3.6.
    verbose : bool
        Print progress info.

    Returns
    -------
    DataFrame long format with columns:
      HourUTC (UTC tz-aware Timestamp), HourDK (local naive or tz-aware),
      PriceArea, SpotPriceEUR, SpotPriceGJ (optional)
    """
    filt = {"PriceArea": list(areas)}
    filter_str = quote(json.dumps(filt, separators=(",", ":")))
    params_common = f"start={start}&end={end}&filter={filter_str}&sort=HourUTC&limit={limit}"
    url0 = f"{API_BASE}?{params_common}&offset=0"
    data = _http_get(url0)
    records = data.get("records", [])
    total = data.get("total", len(records))
    if verbose:
        print(f"Fetched {len(records)}/{total} initial records")
    fetched = len(records)
    while fetched < total:
        url_page = f"{API_BASE}?{params_common}&offset={fetched}"
        page = _http_get(url_page)
        rec_page = page.get("records", [])
        if not rec_page:
            break
        records.extend(rec_page)
        fetched += len(rec_page)
        if verbose:
            print(f"Fetched {fetched}/{total} records")

    if not records:
        raise RuntimeError("No records returned from API; check date range or network connectivity.")

    df = pd.DataFrame(records)
    keep = [c for c in ["HourUTC", "HourDK", "PriceArea", "SpotPriceEUR"] if c in df.columns]
    df = df[keep].copy()
    # Parse timestamps
    if "HourUTC" in df.columns:
        df["HourUTC"] = pd.to_datetime(df["HourUTC"], utc=True, errors="coerce")
    if include_local and "HourDK" in df.columns:
        # API returns local time; parse but may not include tz info
        df["HourDK"] = pd.to_datetime(df["HourDK"], errors="coerce")
    else:
        if "HourDK" in df.columns:
            df = df.drop(columns=["HourDK"])  # remove if not desired

    if to_gj and "SpotPriceEUR" in df.columns:
        df["SpotPriceGJ"] = df["SpotPriceEUR"] / 3.6

    df = df.dropna(subset=["HourUTC"]).sort_values(["PriceArea", "HourUTC"]).reset_index(drop=True)
    return df


def collapse_dst(df: pd.DataFrame) -> pd.DataFrame:
    """Handle potential 8784-hour years (DST duplicate) by collapsing duplicates.

    If there are duplicate (PriceArea, HourDK) pairs, average their prices.
    Requires HourDK column. If not present, returns df unchanged.
    """
    if "HourDK" not in df.columns:
        return df
    # Identify duplicates
    dup_mask = df.duplicated(subset=["PriceArea", "HourDK"], keep=False)
    if not dup_mask.any():
        return df
    grouped = (
        df.groupby(["PriceArea", "HourDK"], as_index=False)
        .agg({c: ("mean" if c.startswith("SpotPrice") else "first") for c in df.columns if c not in ["PriceArea", "HourDK"]})
    )
    # Recreate HourUTC ordering by sorting; HourUTC may not collapse exactly; keep earliest mapping if multiple
    if "HourUTC" in df.columns:
        grouped = grouped.sort_values(["PriceArea", "HourDK"]).reset_index(drop=True)
    return grouped


def pivot_wide(df: pd.DataFrame, value_col: str = "SpotPriceGJ") -> pd.DataFrame:
    """Pivot long format to wide (index=HourUTC, columns=PriceArea)."""
    if value_col not in df.columns:
        raise KeyError(f"Column {value_col} not in DataFrame")
    wide = df.pivot(index="HourUTC", columns="PriceArea", values=value_col).sort_index()
    return wide


def prepare_model_hours(df: pd.DataFrame, area: str = "DK1", value_col: str = "SpotPriceGJ") -> pd.Series:
    """Return a Series indexed by modelHour h0001..hNNNN for selected area.

    If duplicate or missing hours exist, attempt simple reconciliation.
    """
    sub = df[df["PriceArea"] == area].copy()
    if "HourUTC" not in sub.columns:
        raise ValueError("HourUTC column required")
    sub = sub.sort_values("HourUTC")
    # Remove any exact duplicate HourUTC
    sub = sub[~sub["HourUTC"].duplicated(keep="first")]
    n = len(sub)
    sub["modelHour"] = [f"h{h:04d}" for h in range(1, n + 1)]
    if value_col not in sub.columns:
        raise KeyError(f"{value_col} not found; available: {list(sub.columns)}")
    return sub.set_index("modelHour")[value_col]


def price_quantiles(series: pd.Series, qs: Sequence[float] = (0.05,0.1,0.25,0.5,0.75,0.9,0.95,0.99)) -> pd.Series:
    return series.quantile(qs)


def shape_factor(series: pd.Series) -> pd.Series:
    return series / series.mean()


def cli(argv: Optional[Sequence[str]] = None) -> int:
    p = argparse.ArgumentParser(description="Fetch Danish Elspot prices and export CSVs")
    p.add_argument("--start", required=True)
    p.add_argument("--end", required=True)
    p.add_argument("--areas", nargs="+", default=["DK1","DK2"], help="Price areas to include")
    p.add_argument("--out-long", dest="out_long", help="Path to save long format CSV")
    p.add_argument("--out-wide", dest="out_wide", help="Path to save wide pivot CSV (€/GJ)")
    p.add_argument("--no-gj", action="store_true", help="Do NOT add €/GJ conversion column")
    p.add_argument("--quiet", action="store_true", help="Reduce logging")
    args = p.parse_args(argv)

    df = fetch_elspot_prices(
        start=args.start,
        end=args.end,
        areas=args.areas,
        to_gj=not args.no_gj,
        verbose=not args.quiet,
    )
    df = collapse_dst(df)

    if args.out_long:
        df.to_csv(args.out_long, index=False)
        if not args.quiet:
            print(f"Saved long format to {args.out_long}")
    if args.out_wide:
        value_col = "SpotPriceGJ" if (not args.no_gj) else "SpotPriceEUR"
        wide = pivot_wide(df, value_col=value_col)
        wide.to_csv(args.out_wide)
        if not args.quiet:
            print(f"Saved wide format to {args.out_wide}")

    # Print quick stats for first area
    first_area = args.areas[0]
    series = prepare_model_hours(df, area=first_area, value_col=("SpotPriceGJ" if (not args.no_gj) else "SpotPriceEUR"))
    q = price_quantiles(series)
    if not args.quiet:
        print("Quantiles (", first_area, "):\n", q)
        print("Mean price", series.mean())
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(cli())
