#!/usr/bin/env python3
"""Fill missing sitio_web / stream_url in radios_fm_cordoba.csv.

Uses hardcoded overrides (official / verified directories) plus optional
Radio Browser matches for Córdoba-tagged stations.
"""

from __future__ import annotations

import csv
import json
import re
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CSV_PATH = ROOT / "radios_fm_cordoba.csv"
REVISADO = "2026-11-06"
UA = "radios-cordoba-fill/1.0"

# frecuencia -> {sitio_web, stream_url, notas_extra, contrast_add, bump_confianza}
OVERRIDES: dict[str, dict] = {
    "87.7": {
        # No stream oficial estable encontrado; solo contacto
        "sitio_web": "",
        "stream_url": "",
        "notas_extra": "Sin stream público estable encontrado (City One); contacto comercial.cityone@gmail.com",
    },
    "88.5": {
        "sitio_web": "https://www.cba24n.com.ar/",
        "stream_url": "https://radios.solumedia.com:10976/stream",
        "notas_extra": "Stream Universidad AM580 vía Solumedia/RadioBrowser; puede ser dúplex AM",
        "contrast_add": "radiobrowser",
    },
    "89.7": {
        "sitio_web": "https://x.qualityradio.com.ar/",
        "stream_url": "https://stream.qualityradio.com.ar/qualityx",
        "notas_extra": "Sitio y stream oficiales Quality X",
        "contrast_add": "oficial",
        "bump_confianza": "alta",
    },
    "89.9": {
        "notas_extra": "Sin sitio/stream verificable para Radio Génesis Córdoba en esta pasada",
    },
    "90.3": {
        "sitio_web": "https://notify.com.ar/sonidera/",
        "stream_url": "",
        "notas_extra": "Sitio Sonidera vía notify.com.ar; stream directo no hallado; conflicto Cosquín Rock en otras fuentes",
        "contrast_add": "sitio",
    },
    "90.5": {
        "sitio_web": "https://www.qualityradio.com.ar/",
        "stream_url": "https://streaming01.shockmedia.com.ar:10603/",
        "notas_extra": "Sitio oficial Quality 90.5; stream vía Shockmedia/RadioBrowser",
        "contrast_add": "oficial;radiobrowser",
        "bump_confianza": "alta",
    },
    "91.3": {
        "notas_extra": "Sin stream verificable para Más Radio 91.3 en esta pasada",
    },
    "92.7": {
        "sitio_web": "https://www.radiolibre927.com.ar/",
        "stream_url": "https://www.radiolibre927.com.ar/",
        "notas_extra": "Sitio oficial FM Libre; streaming LocucionAR en la web",
        "contrast_add": "oficial",
        "bump_confianza": "alta",
    },
    "92.9": {
        "sitio_web": "https://nuevotiemporadio.com.ar/",
        "stream_url": "https://www.nuevotiempo.org/radio/",
        "notas_extra": "Cadena Nuevo Tiempo; player en red / sitio Córdoba",
        "contrast_add": "oficial",
    },
    "93.1": {
        "sitio_web": "https://dalefm.ar/",
        "stream_url": "https://streaming01.shockmedia.com.ar:10891/;",
        "notas_extra": "Sitio oficial Dale FM; stream Shockmedia",
        "contrast_add": "oficial;radiobrowser",
        "bump_confianza": "alta",
    },
    "93.3": {
        "sitio_web": "https://www.gruposhopping.com/cnn.html",
        "stream_url": "https://player.cnnradio.com.ar/Cordoba/",
        "notas_extra": "Player CNN Radio Córdoba (grupo Shopping)",
        "contrast_add": "oficial",
    },
    "93.5": {
        "sitio_web": "https://rivadavia.com.ar/",
        "stream_url": "https://playerservices.streamtheworld.com/api/livestream-redirect/RIVADAVIAAAC_SC",
        "notas_extra": "Posible feed red Rivadavia BA / no local Córdoba",
        "contrast_add": "radiobrowser",
    },
    "93.7": {
        "sitio_web": "https://vitalmedios.com/",
        "stream_url": "https://vitalmedios.com/",
        "notas_extra": "Sitio Vital Medios; player en página",
        "contrast_add": "oficial",
    },
    "93.9": {
        "notas_extra": "Sin sitio/stream verificable para Radio CIEC en esta pasada",
    },
    "94.3": {
        "sitio_web": "https://www.frc.utn.edu.ar/",
        "stream_url": "https://01.solumedia.com.ar:8200/stream",
        "notas_extra": "Stream UTN FRC vía Solumedia/mammoli",
        "contrast_add": "radiobrowser",
    },
    "95.1": {
        "sitio_web": "https://lvdos.com/",
        "stream_url": "https://lvdos.com/",
        "notas_extra": "Web LV2/Grupo 2; stream específico Vida no separado hallado",
        "contrast_add": "oficial",
    },
    "95.5": {
        "sitio_web": "https://cosquinrock.net/cosquin-rock-radio/",
        "stream_url": "https://playerservices.streamtheworld.com/api/livestream-redirect/cosquinrock.mp3",
        "notas_extra": "Stream StreamTheWorld Cosquín Rock; sitio cosquinrock.net",
        "contrast_add": "oficial;radiobrowser",
        "bump_confianza": "alta",
    },
    "95.7": {
        "notas_extra": "Sin sitio/stream verificable para Impacto Musical en esta pasada",
    },
    "95.9": {
        "notas_extra": "Sin stream verificable para Play 95.9 Córdoba (otros Play FM son de otras ciudades)",
    },
    "96.9": {
        "notas_extra": "Sin stream verificable Día & Noche Multimedia; ENACOM/WRM citan Amistad",
    },
    "97.1": {
        "sitio_web": "https://redaleluya.com.ar/",
        "stream_url": "https://redaleluya.com.ar/",
        "notas_extra": "Sitio red Aleluya; player de red (puede no ser feed local Córdoba)",
        "contrast_add": "oficial",
    },
    "97.5": {
        "notas_extra": "Repetidora Más Radio; sin stream propio hallado",
    },
    "98.9": {
        "sitio_web": "https://www.laradio.com.ar/",
        "stream_url": "https://playerservices.streamtheworld.com/api/livestream-redirect/LA_RED_AM910AAC_SC",
        "notas_extra": "Posible feed La Red nacional; conflicto con Suquía Plus en WRM",
        "contrast_add": "radiobrowser",
    },
    "99.3": {
        "sitio_web": "http://www.radioimpacto993.esenvivo.com.ar/",
        "stream_url": "http://stream.shockmedia.com.ar:1935/radioimpacto993/default.stream/playlist.m3u8",
        "notas_extra": "Player Shockmedia Impacto 99.3",
        "contrast_add": "oficial",
        "bump_confianza": "alta",
    },
    "101.1": {
        "notas_extra": "Presencia FM: sin stream HTTP estable hallado (solo directorios)",
    },
    "101.3": {
        "sitio_web": "https://showsportradio.com.ar/",
        "stream_url": "https://showsportradio.com.ar/",
        "notas_extra": "Sitio oficial Showsport; player embebido en home",
        "contrast_add": "oficial",
        "bump_confianza": "alta",
    },
    "101.7": {
        "notas_extra": "REMAR: sin stream verificable en esta pasada",
    },
    "101.9": {
        "sitio_web": "https://cadena102.com.ar/",
        "stream_url": "https://sslstream.online:7106/",
        "notas_extra": "Cadena 102 / FM Visión; stream vía RadioBrowser/sslstream",
        "contrast_add": "oficial;radiobrowser",
        "bump_confianza": "alta",
    },
    "103.5": {
        "sitio_web": "https://www.continental.com.ar/",
        "stream_url": "https://playerservices.streamtheworld.com/api/livestream-redirect/CONTINENTALAAC_SC",
        "notas_extra": "Posible feed Continental BA / no local Córdoba",
        "contrast_add": "radiobrowser",
        "radiocut_url": "https://radiocut.fm/radiostation/continental-cordoba/",
    },
    "104.5": {
        "notas_extra": "FM Providencia: sin stream verificable en esta pasada",
    },
    "104.7": {
        "sitio_web": "https://www.radiosucesos.com.ar/",
        "stream_url": "https://www.radiosucesos.com.ar/",
        "notas_extra": "Sitio oficial Radio Sucesos; player en home",
        "contrast_add": "oficial",
        "bump_confianza": "alta",
    },
    "105.3": {
        "notas_extra": "Radio Jaja: sin stream HTTP estable hallado",
    },
    "105.5": {
        "sitio_web": "https://www.lasrosas.com.ar/portal/las-rosas-radio-live/",
        "stream_url": "http://streaming01.shockmedia.com.ar:9676/stream",
        "notas_extra": "Stream Las Rosas vía Shockmedia (sitio grupo)",
        "contrast_add": "oficial",
        "bump_confianza": "alta",
    },
    "106.9": {
        "sitio_web": "http://www.modoradio.esenvivo.com.ar/",
        "stream_url": "http://stream.shockmedia.com.ar:1935/modoradio/default.stream/playlist.m3u8",
        "notas_extra": "Player Shockmedia Modo Radio",
        "contrast_add": "oficial",
        "bump_confianza": "alta",
    },
    "107.3": {
        "stream_url": "https://server6.hostradios.com/8556/stream",
        "notas_extra": "Candidato Ranquel vía HostRadios/mammoli — verificar si es capital o otra plaza",
        "contrast_add": "mammoli",
    },
    "107.5": {
        "sitio_web": "http://www.genfm.com.ar/",
        "stream_url": "https://radiocut.fm/radiostation/gen/listen/",
        "radiocut_url": "https://radiocut.fm/radiostation/gen/",
        "notas_extra": "Sitio Gen FM; escucha vía RadioCut",
        "contrast_add": "radiocut",
    },
    "107.9": {
        "sitio_web": "https://bbn1.bbnradio.org/spanish/",
        "stream_url": "https://streams.radiomast.io/475ebed1-595e-4717-b888-64fe8fc6b09f",
        "notas_extra": "Stream oficial BBN español (red); feed nacional",
        "contrast_add": "oficial",
        "bump_confianza": "alta",
    },
}


def merge_notas(base: str, extra: str) -> str:
    parts = [p.strip() for p in (base or "").split(";") if p.strip()]
    if extra and extra not in parts:
        parts.append(extra)
    return "; ".join(parts)


def merge_contrast(base: str, add: str) -> str:
    parts = [p.strip() for p in (base or "").split(";") if p.strip()]
    for p in (add or "").split(";"):
        p = p.strip()
        if p and p not in parts:
            parts.append(p)
    return ";".join(parts)


def fetch_radio_browser_cordoba() -> list[dict]:
    url = (
        "https://de1.api.radio-browser.info/json/stations/search"
        "?countrycode=AR&limit=1000&hidebroken=true"
    )
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=90) as resp:
        return json.loads(resp.read().decode())


def norm(s: str) -> str:
    s = (s or "").lower()
    s = (
        s.replace("á", "a")
        .replace("é", "e")
        .replace("í", "i")
        .replace("ó", "o")
        .replace("ú", "u")
        .replace("ñ", "n")
    )
    return re.sub(r"[^a-z0-9]+", " ", s).strip()


def auto_match(nombre: str, stations: list[dict]) -> dict | None:
    n = norm(nombre)
    if len(n) < 4:
        return None
    # Prefer stations that mention cordoba in name/state/tags
    cord = [
        s
        for s in stations
        if "cordob" in norm(
            " ".join(
                [
                    s.get("name") or "",
                    s.get("state") or "",
                    s.get("tags") or "",
                    s.get("homepage") or "",
                ]
            )
        )
    ]
    pool = cord or stations
    best = None
    best_score = 0
    for s in pool:
        sn = norm(s.get("name") or "")
        score = 0
        if n == sn:
            score = 100
        elif n in sn or sn in n:
            score = 80
        else:
            # token overlap
            ta, tb = set(n.split()), set(sn.split())
            if ta and tb:
                score = int(100 * len(ta & tb) / len(ta | tb))
        if score > best_score and score >= 70:
            best_score = score
            best = s
    if not best:
        return None
    return {
        "stream_url": best.get("url_resolved") or best.get("url") or "",
        "sitio_web": best.get("homepage") or "",
        "notas_extra": f"Match RadioBrowser '{best.get('name')}' score={best_score}",
        "contrast_add": "radiobrowser",
    }


def main() -> None:
    with CSV_PATH.open(encoding="utf-8", newline="") as f:
        rows = list(csv.DictReader(f))
        fieldnames = list(rows[0].keys())

    try:
        rb = fetch_radio_browser_cordoba()
        print(f"RadioBrowser AR stations: {len(rb)}")
    except Exception as e:
        print(f"RadioBrowser unavailable: {e}")
        rb = []

    filled = 0
    for row in rows:
        freq = row["frecuencia_mhz"]
        has_stream = bool((row.get("stream_url") or "").strip())
        ov = dict(OVERRIDES.get(freq, {}))

        # Auto-match only if still missing stream after override
        if not has_stream and not ov.get("stream_url") and rb:
            auto = auto_match(row["nombre"], rb)
            if auto:
                # Don't overwrite empty override notes intent
                for k, v in auto.items():
                    if k not in ov or not ov.get(k):
                        ov[k] = v

        if not ov:
            continue

        if ov.get("sitio_web") and not (row.get("sitio_web") or "").strip():
            row["sitio_web"] = ov["sitio_web"]
        if ov.get("stream_url") and not (row.get("stream_url") or "").strip():
            row["stream_url"] = ov["stream_url"]
            row["stream_estado"] = "no_probado"
            filled += 1
        if ov.get("radiocut_url") and not (row.get("radiocut_url") or "").strip():
            row["radiocut_url"] = ov["radiocut_url"]
        if ov.get("notas_extra"):
            row["notas"] = merge_notas(row.get("notas", ""), ov["notas_extra"])
        if ov.get("contrast_add"):
            row["contrastado_en"] = merge_contrast(
                row.get("contrastado_en", ""), ov["contrast_add"]
            )
        if ov.get("bump_confianza") == "alta" and row.get("confianza") != "alta":
            # Only bump if we also have sitio or stream
            if row.get("sitio_web") or row.get("stream_url"):
                row["confianza"] = "alta"
        row["revisado"] = REVISADO

    with CSV_PATH.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        w.writerows(rows)

    still = sum(1 for r in rows if not (r.get("stream_url") or "").strip())
    print(f"Filled stream_url on {filled} rows; still missing: {still} -> {CSV_PATH}")


if __name__ == "__main__":
    main()
