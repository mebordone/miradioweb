#!/usr/bin/env python3
"""Build VLC M3U playlist from radios_fm_cordoba.csv (audio URLs only, dial order)."""

from __future__ import annotations

import csv
import re
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CSV_PATH = ROOT / "radios_fm_cordoba.csv"
OUT_PATH = ROOT / "playlists" / "cordoba_fm_dial.m3u"
UA = "radios-cordoba-vlc/1.0"

# Curated direct audio overrides (HTML players / status pages → Icecast/STW/etc.)
DIRECT_BY_FREQ: dict[str, str] = {
    "90.1": "https://streaming.dainusradio.com:9848/stream",
    "90.5": "https://streaming01.shockmedia.com.ar:10603/stream",
    "90.7": "https://streaming01.shockmedia.com.ar:10714/stream",
    "91.9": "https://playerservices.streamtheworld.com/api/livestream-redirect/CADENAHEAT_SC",
    "92.3": "https://liveradio.mediainbox.net/popular.mp3",
    "92.7": "https://streaming6.locucionar.com:24404/stream",
    "95.5": "https://playerservices.streamtheworld.com/api/livestream-redirect/cosquinrock.mp3",
    "96.5": "https://streaming01.shockmedia.com.ar:10945/stream",
    "97.1": "https://nl.digitalrm.pt:8050/stream",
    "97.9": "https://playerservices.streamtheworld.com/api/livestream-redirect/AM790_56_SC",
    "99.3": "https://sonic.cloudstreaming.eu/9992/stream",
    "100.1": "https://sa.mp3.icecast.magma.edge-access.net/sc_rad7",
    "100.5": "https://playerservices.streamtheworld.com/api/livestream-redirect/RADIO3_SC",
    "101.1": "https://01.solumedia.com.ar:8516/stream",
    "101.3": "https://streaming.gostreaming.com.ar:10929/stream",
    "101.5": "https://dreamsiteradiocp2.com/proxy/rmargentina2?mp=%2Fstream",
    "101.9": "https://sslstream.online:7106/stream",
    "102.3": "https://radios.solumedia.com:6276/stream",
    "102.9": "https://playerservices.streamtheworld.com/api/livestream-redirect/FM999_56AAC_SC",
    "103.5": "https://frontend.radiohdvivo.com/continental/live",
    "103.9": "https://server.laradio.online/proxy/javier_diaz01?mp=/stream",
    "104.1": "https://playerservices.streamtheworld.com/api/livestream-redirect/MIA_SC",
    "104.5": "https://radios.solumedia.com:10998/stream",
    "104.7": "https://streaming.dainusradio.com:2341/stream",
    "105.5": "https://streaming01.shockmedia.com.ar/9676/stream",
    "105.9": "https://streaming.radiosenlinea.com.ar/9574/stream",
    "106.9": "https://streaming01.shockmedia.com.ar/9060/stream",
    "107.5": "https://sonic.host-live.com/8250/stream",
}

DIRECT_BY_NAME: dict[str, str] = {
    "La Quinta Pata": "http://server3.veemesoft.com.ar:26429/;",
}

# Status-page hosts that need an explicit mount (/stream, /;, .mp3, etc.)
STATUS_HOST = re.compile(
    r"(shockmedia|sslstream\.online|solumedia|hostradios|radiosenlinea|"
    r"gostreaming|locucionar|xcast|ohradio)",
    re.I,
)
HAS_MOUNT = re.compile(
    r"/stream(\.mp4)?(/|\?|$)|/;|(\.mp3|\.aac|\.m3u8|\.pls)(\?|$)|"
    r"livestream-redirect|/proxy/|playlist\.m3u8|\?mp=|/sc_rad",
    re.I,
)

AUDIO_HINT = re.compile(
    r"(\.mp3|\.aac|\.m3u8|\.pls|\.mp4)(\?|$)|"
    r"/;|/stream|livestream-redirect|playlist\.m3u8|"
    r"streamtheworld|mediainbox|suenas\.net|icecast|magma\.edge|"
    r"radiohdvivo|laradio\.online|host-live|dainus|veemesoft|"
    r"digitalrm|radiomast|dreamsiteradiocp|/proxy/",
    re.I,
)

HTML_HINT = re.compile(
    r"(/player/|page_id=|/en-vivo|/vivo\.html|\.html($|\?)|\.asp|"
    r"cienradios\.com/player|cadena3\.com/radio|lvdos\.com|"
    r"radiocut\.fm/.*/listen|listen2myshow|kick\.com|"
    r"radioarg\.com|masradio\.fm|nuevotiempo|"
    r"laranchada\.com\.ar/?$|radiosucesos\.com\.ar/?$|"
    r"showsportradio\.com\.ar/?$|cba24n\.com\.ar/?$|"
    r"puntoapunto\.com\.ar/radio|redaleluya\.com\.ar/?$|"
    r"cnnradio\.com\.ar|fmactiva\.com/vivo|radiopresencia|"
    r"radiolibre927\.com\.ar/?$|esenvivo\.com\.ar/listen\.pls)",
    re.I,
)


def is_audio_url(url: str) -> bool:
    if not url or not url.strip():
        return False
    u = url.strip()
    if HTML_HINT.search(u) and not AUDIO_HINT.search(u):
        return False
    # Icecast/Shoutcast status pages (bare :port/) are HTML, not audio
    if STATUS_HOST.search(u) and not HAS_MOUNT.search(u):
        return False
    if AUDIO_HINT.search(u) or HAS_MOUNT.search(u):
        return True
    if STATUS_HOST.search(u) and HAS_MOUNT.search(u):
        return True
    if re.search(r"\.(com|com\.ar|ar|org)/?$", u.rstrip("/")):
        return False
    return False


def resolve_url(row: dict) -> str:
    name = row.get("nombre") or ""
    freq = row.get("frecuencia_mhz") or ""
    if name in DIRECT_BY_NAME:
        return DIRECT_BY_NAME[name]
    if freq in DIRECT_BY_FREQ:
        return DIRECT_BY_FREQ[freq]
    return (row.get("stream_url") or "").strip()


def probe_audio(url: str, timeout: float = 8.0) -> bool:
    req = urllib.request.Request(
        url,
        headers={"User-Agent": UA, "Icy-MetaData": "1", "Range": "bytes=0-2047"},
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            ct = (resp.headers.get("Content-Type") or "").lower()
            chunk = resp.read(512)
            if resp.getcode() and int(resp.getcode()) >= 400:
                return False
            if "html" in ct or chunk.lstrip()[:15].lower().startswith(b"<!doctype") or chunk.lstrip()[:6].lower().startswith(b"<html"):
                return False
            if any(x in ct for x in ("audio", "mpegurl", "octet-stream", "icy", "mpeg", "aac", "scpls", "pls")):
                return True
            return bool(chunk) and not chunk.lstrip().startswith(b"<")
    except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, OSError):
        return False


def update_csv_direct_streams() -> int:
    with CSV_PATH.open(encoding="utf-8", newline="") as f:
        rows = list(csv.DictReader(f))
        fields = list(rows[0].keys())

    updated = 0
    for row in rows:
        current = (row.get("stream_url") or "").strip()
        resolved = resolve_url(row)
        if not resolved or not is_audio_url(resolved):
            continue
        if resolved == current:
            continue
        # Replace missing / HTML / status-page / curated override
        if (not current) or (not is_audio_url(current)) or (
            row.get("nombre") in DIRECT_BY_NAME or row.get("frecuencia_mhz") in DIRECT_BY_FREQ
        ):
            row["stream_url"] = resolved
            row["stream_estado"] = "no_probado"
            notas = row.get("notas") or ""
            note = "stream_url directo para VLC"
            if note not in notas:
                row["notas"] = (notas + "; " + note).strip("; ")
            row["revisado"] = "2026-11-06"
            updated += 1

    with CSV_PATH.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        w.writerows(rows)
    return updated


def build_playlist(verify: bool = True) -> tuple[int, int, list[str]]:
    with CSV_PATH.open(encoding="utf-8", newline="") as f:
        rows = list(csv.DictReader(f))

    candidates = []
    for row in rows:
        url = resolve_url(row)
        if not is_audio_url(url):
            continue
        candidates.append((float(row["frecuencia_mhz"]), row["nombre"], url, row))

    candidates.sort(key=lambda x: (x[0], x[1].lower()))

    included = []
    skipped_probe = []
    for freq, name, url, row in candidates:
        if verify:
            if not probe_audio(url):
                skipped_probe.append(f"{freq} {name}")
                continue
        included.append((freq, name, url))

    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    lines = ["#EXTM3U", "# Playlist FM Ciudad de Córdoba — orden de dial", ""]
    for freq, name, url in included:
        title = f"{freq:.1f} {name}"
        lines.append(f"#EXTINF:-1,{title}")
        lines.append(url)
        lines.append("")

    OUT_PATH.write_text("\n".join(lines), encoding="utf-8")
    return len(included), len(candidates), skipped_probe


def main() -> None:
    n = update_csv_direct_streams()
    print(f"CSV stream_url updates: {n}")
    included, candidates, skipped = build_playlist(verify=True)
    print(f"Playlist: {included}/{candidates} audio URLs -> {OUT_PATH}")
    if skipped:
        print(f"Skipped (probe fail): {len(skipped)}")
        for s in skipped:
            print(f"  - {s}")


if __name__ == "__main__":
    main()
