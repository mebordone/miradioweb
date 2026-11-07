#!/usr/bin/env python3
"""Probe stream_url values in radios_fm_cordoba.csv and update stream_estado."""

from __future__ import annotations

import csv
import sys
import urllib.error
import urllib.request
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CSV_PATH = ROOT / "radios_fm_cordoba.csv"
TIMEOUT = 8
UA = "Mozilla/5.0 (compatible; radios-cordoba-check/1.0)"


def probe(url: str) -> str:
    if not url:
        return ""
    req = urllib.request.Request(
        url,
        method="GET",
        headers={
            "User-Agent": UA,
            "Icy-MetaData": "1",
            "Range": "bytes=0-2047",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
            code = getattr(resp, "status", None) or resp.getcode()
            ctype = (resp.headers.get("Content-Type") or "").lower()
            # Read a tiny chunk to confirm body starts
            chunk = resp.read(512)
            if code and int(code) >= 400:
                return "roto"
            if any(
                x in ctype
                for x in (
                    "audio",
                    "mpegurl",
                    "octet-stream",
                    "icy",
                    "application/vnd.apple.mpegurl",
                    "application/x-mpegurl",
                    "text/html",  # official player pages
                )
            ):
                return "ok"
            if chunk:
                return "ok"
            return "roto"
    except Exception:
        # Retry without Range (some Icecast dislike it)
        req2 = urllib.request.Request(
            url,
            method="GET",
            headers={"User-Agent": UA, "Icy-MetaData": "1"},
        )
        try:
            with urllib.request.urlopen(req2, timeout=TIMEOUT) as resp:
                code = getattr(resp, "status", None) or resp.getcode()
                if code and int(code) >= 400:
                    return "roto"
                resp.read(256)
                return "ok"
        except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, OSError):
            return "roto"


def main() -> int:
    path = Path(sys.argv[1]) if len(sys.argv) > 1 else CSV_PATH
    with path.open(encoding="utf-8", newline="") as f:
        rows = list(csv.DictReader(f))
        fieldnames = list(rows[0].keys()) if rows else []

    if "stream_estado" not in fieldnames:
        fieldnames.append("stream_estado")
    if "revisado" not in fieldnames:
        fieldnames.append("revisado")

    today = date.today().isoformat()
    ok = roto = skip = 0

    for row in rows:
        url = (row.get("stream_url") or "").strip()
        if not url:
            row["stream_estado"] = ""
            skip += 1
            continue
        status = probe(url)
        row["stream_estado"] = status
        row["revisado"] = today
        if status == "ok":
            ok += 1
            row["escucha_online"] = "si"
        elif status == "roto":
            roto += 1
            # Keep URL for retry; mark listening unknown
            row["escucha_online"] = "desconocido"
        print(f"{row.get('frecuencia_mhz')} {row.get('nombre')}: {status}")

    with path.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        w.writerows(rows)

    print(f"\nDone: ok={ok} roto={roto} sin_url={skip} -> {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
