#!/usr/bin/env python3
"""Enrich radios_fm_cordoba.csv with contrast fields (no stream probe)."""

from __future__ import annotations

import csv
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CSV_PATH = ROOT / "radios_fm_cordoba.csv"
REVISADO = "2026-11-06"

# Overlay by frecuencia_mhz (string with one decimal as in CSV)
OVERLAY: dict[str, dict] = {
    "87.7": {
        "genero": "music",
        "confianza": "media",
        "contrastado_en": "wikipedia;totalmedios",
        "notas_extra": "TotalMedios listó Urbana Classic en 87.7; Wikipedia City One",
    },
    "88.5": {
        "genero": "universitaria",
        "direccion": "Fray Miguel de Mojica 1600",
        "confianza": "media",
        "contrastado_en": "worldradiomap;srt",
        "sitio_web": "https://www.cba24n.com.ar/",
    },
    "88.7": {
        "genero": "universitaria",
        "direccion": "Ciudad Universitaria, FCC UNC",
        "radiocut_url": "https://radiocut.fm/radiostation/reves/",
        "confianza": "alta",
        "contrastado_en": "wikipedia;oficial;radiocut",
        "sitio_web": "https://radioreves.fcc.unc.edu.ar/",
    },
    "88.9": {
        "genero": "music",
        "direccion": "Av. Duarte Quirós 1400",
        "nombre_legal": "",
        "radiocut_url": "https://radiocut.fm/radiostation/pobre-johnny/",
        "confianza": "alta",
        "contrastado_en": "wikipedia;oficial;radiocut;worldradiomap;totalmedios",
        "sitio_web": "https://www.gruposhopping.com/",
    },
    "89.3": {
        "genero": "music",
        "direccion": "Av. Maipú 355",
        "confianza": "media",
        "contrastado_en": "wikipedia;worldradiomap",
    },
    "89.7": {
        "genero": "music",
        "direccion": "Cruz Roja Argentina 200 (Quality / zona UNC)",
        "confianza": "media",
        "contrastado_en": "wikipedia;worldradiomap;totalmedios",
        "notas_extra": "ENACOM/listados viejos citaron Urbana 89.7; marca actual Quality X",
    },
    "89.9": {
        "genero": "music",
        "direccion": "Aristóteles 3100, Zumarán",
        "confianza": "media",
        "contrastado_en": "wikipedia;worldradiomap",
    },
    "90.1": {
        "genero": "comunitaria",
        "direccion": "Barranquilla 5320, Villa El Libertador",
        "nombre_legal": "RADIO SUR",
        "radiocut_url": "https://radiocut.fm/radiostation/radio-sur-901-fm/",
        "confianza": "alta",
        "contrastado_en": "wikipedia;enacom;worldradiomap;radiocut;oficial",
        "sitio_web": "http://www.radiosur901.com.ar/",
    },
    "90.3": {
        "genero": "music",
        "direccion": "La Rioja 1150",
        "confianza": "baja",
        "contrastado_en": "wikipedia;worldradiomap",
        "notas_extra": "Conflicto: Wikipedia Sonidera; WRM Cosquín Rock en 90.3",
    },
    "90.5": {
        "genero": "music",
        "direccion": "Cruz Roja Argentina 200, Ciudad Universitaria",
        "confianza": "media",
        "contrastado_en": "wikipedia;worldradiomap;totalmedios",
    },
    "90.7": {
        "genero": "news",
        "direccion": "Av. Rafael Núñez 4504 / José Roque Funes 1145",
        "confianza": "alta",
        "contrastado_en": "wikipedia;oficial;worldradiomap;totalmedios",
        "sitio_web": "https://puntoapunto.com.ar/",
    },
    "91.1": {
        "genero": "music",
        "direccion": "Buenos Aires 570",
        "confianza": "media",
        "contrastado_en": "wikipedia;worldradiomap",
    },
    "91.3": {
        "genero": "music",
        "nombre_legal": "FM SAN FRANCISCO DE ASIS (histórico)",
        "direccion": "Juan Bautista Daniel 1995 (histórico ENACOM)",
        "confianza": "baja",
        "contrastado_en": "wikipedia;enacom",
        "notas_extra": "ENACOM histórico San Francisco de Asís; Wikipedia Más Radio; agregadores Kuarteto",
    },
    "91.9": {
        "genero": "music",
        "nombre_legal": "FM CORDOBA",
        "direccion": "Av. Gral. Alvear 139",
        "confianza": "alta",
        "contrastado_en": "wikipedia;oficial;enacom;worldradiomap;totalmedios",
        "sitio_web": "https://www.cadena3.com/",
    },
    "92.3": {
        "genero": "music",
        "nombre_legal": "RADIO POPULAR",
        "direccion": "Av. Gral. Alvear 139",
        "confianza": "alta",
        "contrastado_en": "wikipedia;oficial;enacom;worldradiomap;totalmedios",
        "sitio_web": "https://www.cadena3.com/",
    },
    "92.7": {
        "genero": "music",
        "direccion": "Av. Enfermera Clermont 205",
        "nombre_legal": "RADIO LIBRE (LRJ415)",
        "confianza": "media",
        "contrastado_en": "wikipedia;worldradiomap",
    },
    "92.9": {
        "genero": "religiosa",
        "nombre_legal": "RADIO NUEVO TIEMPO CORDOBA",
        "direccion": "Av. Gdor. Amadeo Sabattini 1662",
        "confianza": "alta",
        "contrastado_en": "wikipedia;enacom;worldradiomap",
    },
    "93.1": {
        "genero": "music",
        "confianza": "media",
        "contrastado_en": "wikipedia;worldradiomap",
    },
    "93.3": {
        "genero": "news",
        "direccion": "Av. Duarte Quirós 1400 (Grupo Shopping)",
        "confianza": "alta",
        "contrastado_en": "wikipedia;oficial;totalmedios",
        "sitio_web": "https://www.gruposhopping.com/cnn.html",
        "notas_extra": "TotalMedios a veces lista Urbana Play; marca actual CNN Radio Córdoba",
    },
    "93.5": {
        "genero": "news",
        "direccion": "Juan de Garay 954",
        "confianza": "media",
        "contrastado_en": "wikipedia;worldradiomap;totalmedios",
    },
    "93.7": {
        "genero": "music",
        "sitio_web": "https://vitalmedios.com/",
        "confianza": "media",
        "contrastado_en": "wikipedia;oficial",
    },
    "93.9": {
        # Nota: el CSV puede tener DOS filas (Quinta Pata + CIEC). Este overlay
        # solo aplica si enrich se re-corre sobre una fila CIEC residual.
        "genero": "comunitaria",
        "confianza": "baja",
        "contrastado_en": "wikipedia;farco",
        "notas_extra": "Superposición 93.9: La Quinta Pata (FARCO) vs CIEC/Nostalgie; no unificar",
    },
    "94.3": {
        "genero": "universitaria",
        "nombre_legal": "LRJ 405 RADIO UTN FRC",
        "direccion": "Maestro Marcelo López, UTN Facultad Regional Córdoba",
        "confianza": "alta",
        "contrastado_en": "wikipedia;worldradiomap",
    },
    "94.7": {
        "genero": "music",
        "nombre_legal": "FM LOCA SUELTA",
        "direccion": "Av. Duarte Quirós 1400",
        "confianza": "alta",
        "contrastado_en": "wikipedia;oficial;enacom;worldradiomap;totalmedios",
        "sitio_web": "https://www.gruposhopping.com/loca.html",
    },
    "95.1": {
        "genero": "music",
        "nombre_legal": "RADIO CULTURA (histórico ENACOM)",
        "direccion": "Av. Fuerza Aérea 1711 (histórico) / Marcos Sastre 1769 (LV2)",
        "radiocut_url": "https://radiocut.fm/radiostation/pulxo/",
        "confianza": "baja",
        "contrastado_en": "wikipedia;radiocut;enacom;lvdos",
        "sitio_web": "https://lvdos.com/",
        "notas_extra": "Conflicto fuerte: Wikipedia/LV2=Vida Córdoba; RadioCut=Pulxo; ENACOM histórico=Cultura",
    },
    "95.5": {
        "genero": "music",
        "nombre_legal": "FM SONIDERA (histórico en otra freq)",
        "confianza": "baja",
        "contrastado_en": "wikipedia;worldradiomap",
        "notas_extra": "Wikipedia Cosquín Rock 95.5; WRM Cosquín Rock en 90.3 y Sonidera en 95.5 en otras fuentes",
    },
    "95.7": {
        "genero": "music",
        "confianza": "baja",
        "contrastado_en": "wikipedia",
    },
    "95.9": {
        "genero": "music",
        "confianza": "media",
        "contrastado_en": "wikipedia",
    },
    "96.1": {
        "genero": "music",
        "nombre_legal": "RADIO SHOPPING",
        "direccion": "Av. Duarte Quirós 1400",
        "confianza": "alta",
        "contrastado_en": "wikipedia;oficial;enacom;worldradiomap;totalmedios",
        "sitio_web": "https://www.gruposhopping.com/",
    },
    "96.5": {
        "genero": "news",
        "direccion": "Catamarca 342",
        "radiocut_url": "https://radiocut.fm/radiostation/suquia/",
        "sitio_web": "http://www.suquia.com.ar/",
        "confianza": "alta",
        "contrastado_en": "wikipedia;radiocut;worldradiomap;totalmedios",
    },
    "96.7": {
        "genero": "music",
        "direccion": "Santa Rosa 954",
        "confianza": "media",
        "contrastado_en": "wikipedia;worldradiomap",
    },
    "96.9": {
        "genero": "religiosa",
        "nombre_legal": "RADIO AMISTAD",
        "direccion": "Buchardo 865",
        "confianza": "baja",
        "contrastado_en": "wikipedia;enacom;worldradiomap",
        "notas_extra": "Wikipedia Día & Noche; ENACOM/WRM Amistad — posible cambio de marca",
    },
    "97.1": {
        "genero": "religiosa",
        "nombre_legal": "RADIO PRIMERO DE MAYO / LATINA (histórico)",
        "direccion": "Constituyente Salguero 428",
        "confianza": "baja",
        "contrastado_en": "wikipedia;enacom",
        "notas_extra": "Wikipedia Red Aleluya; ENACOM histórico Primero de Mayo/Latina",
    },
    "97.5": {
        "genero": "music",
        "confianza": "baja",
        "contrastado_en": "wikipedia",
        "notas_extra": "Repetidora Más Radio Jesús María según Wikipedia",
    },
    "97.7": {
        "genero": "music",
        "confianza": "media",
        "contrastado_en": "wikipedia;totalmedios",
        "notas_extra": "Listados previos Guapa; Aspen stream puede ser red BA",
    },
    "97.9": {
        "genero": "news",
        "nombre_legal": "RADIO MITRE CORDOBA",
        "direccion": "Av. Fernando Fader 3469",
        "confianza": "alta",
        "contrastado_en": "wikipedia;oficial;enacom;worldradiomap",
        "sitio_web": "https://radiomitre.cienradios.com/",
    },
    "98.5": {
        "genero": "music",
        "direccion": "Av. Manuel Cardeñosa 3450",
        "radiocut_url": "https://radiocut.fm/radiostation/orfeo/",
        "sitio_web": "http://radioorfeo.com/",
        "confianza": "alta",
        "contrastado_en": "wikipedia;radiocut;worldradiomap;totalmedios",
    },
    "98.7": {
        "genero": "news",
        "confianza": "media",
        "contrastado_en": "wikipedia;totalmedios",
        "notas_extra": "Stream Radio 10 suele ser feed de red; confirmar local",
    },
    "98.9": {
        "genero": "news",
        "direccion": "Catamarca 346 (Suquía Plus histórico)",
        "confianza": "baja",
        "contrastado_en": "wikipedia;worldradiomap;totalmedios",
        "notas_extra": "Conflicto: Wikipedia La Red; WRM Suquía Plus; TotalMedios La Red",
    },
    "99.3": {
        "genero": "news",
        "direccion": "Av. 25 de Mayo 147",
        "confianza": "media",
        "contrastado_en": "wikipedia;worldradiomap",
    },
    "99.7": {
        "genero": "news",
        "direccion": "Marcos Sastre 1769",
        "confianza": "alta",
        "contrastado_en": "wikipedia;oficial",
        "sitio_web": "https://lvdos.com/",
    },
    "100.1": {
        "genero": "news",
        "nombre_legal": "LRA7 RADIO NACIONAL CORDOBA",
        "radiocut_url": "https://radiocut.fm/radiostation/nacional-cordoba/",
        "confianza": "alta",
        "contrastado_en": "wikipedia;oficial;radiocut",
        "sitio_web": "https://www.radionacional.com.ar/category/lra-7-cordoba/",
        "notas_extra": "Slug RadioCut a verificar; stream Icecast RTA",
    },
    "100.5": {
        "genero": "news",
        "nombre_legal": "LV3 / CADENA 3",
        "direccion": "Av. Gral. Alvear 139",
        "confianza": "alta",
        "contrastado_en": "wikipedia;oficial;worldradiomap;totalmedios",
        "sitio_web": "https://www.cadena3.com/",
    },
    "101.1": {
        "genero": "religiosa",
        "nombre_legal": "RADIO PRESENCIA (LRJ77)",
        "direccion": "Av. Deán Funes 266",
        "confianza": "alta",
        "contrastado_en": "wikipedia;enacom;worldradiomap",
    },
    "101.3": {
        "genero": "news",
        "direccion": "Juan de Garay 954",
        "confianza": "media",
        "contrastado_en": "wikipedia;totalmedios",
        "notas_extra": "Showsport; antes asociada a La Red en listados viejos",
    },
    "101.5": {
        "genero": "religiosa",
        "nombre_legal": "RADIO MARIA (LRJ428)",
        "direccion": "Av. Vélez Sarsfield 51",
        "confianza": "alta",
        "contrastado_en": "wikipedia;oficial;worldradiomap",
        "sitio_web": "https://www.radiomaria.org.ar/",
    },
    "101.7": {
        "genero": "religiosa",
        "confianza": "media",
        "contrastado_en": "wikipedia;enacom",
    },
    "101.9": {
        "genero": "music",
        "direccion": "Carlos López Buchardo 4341",
        "confianza": "media",
        "contrastado_en": "wikipedia;worldradiomap",
    },
    "102.3": {
        "genero": "universitaria",
        "direccion": "Fray Miguel de Mojica 1600",
        "confianza": "alta",
        "contrastado_en": "wikipedia;oficial;worldradiomap;srt",
        "sitio_web": "https://www.cba24n.com.ar/",
    },
    "102.9": {
        "genero": "music",
        "nombre_legal": "LA 100 CORDOBA (LRJ771)",
        "direccion": "Av. Fernando Fader 3469",
        "confianza": "alta",
        "contrastado_en": "wikipedia;oficial;worldradiomap;totalmedios",
        "sitio_web": "https://la100.cienradios.com/",
    },
    "103.1": {
        "genero": "music",
        "nombre_legal": "RADIO MANSA (LRJ940)",
        "direccion": "Av. Duarte Quirós 1400",
        "confianza": "alta",
        "contrastado_en": "wikipedia;oficial;worldradiomap;totalmedios",
        "sitio_web": "https://www.gruposhopping.com/",
    },
    "103.5": {
        "genero": "news",
        "nombre_legal": "CONTINENTAL CORDOBA (LRJ943)",
        "direccion": "Av. Deán Funes 266",
        "radiocut_url": "https://radiocut.fm/radiostation/continental-cordoba/",
        "confianza": "alta",
        "contrastado_en": "wikipedia;worldradiomap;radiocut",
        "notas_extra": "Slug RadioCut a verificar",
    },
    "103.9": {
        "genero": "comunitaria",
        "direccion": "Av. Julio A. Roca 584, Güemes",
        "radiocut_url": "https://radiocut.fm/radiostation/la-ranchada/",
        "confianza": "alta",
        "contrastado_en": "wikipedia;oficial;radiocut;worldradiomap",
        "sitio_web": "https://laranchada.com.ar/",
    },
    "104.1": {
        "genero": "music",
        "direccion": "Av. Fernando Fader 3469",
        "confianza": "alta",
        "contrastado_en": "wikipedia;oficial;worldradiomap;totalmedios",
        "sitio_web": "https://miafm.cienradios.com/",
    },
    "104.5": {
        "genero": "religiosa",
        "direccion": "Av. Armada Argentina 2440",
        "confianza": "media",
        "contrastado_en": "wikipedia;worldradiomap",
    },
    "104.7": {
        "genero": "news",
        "nombre_legal": "RADIO SUCESOS (LRJ747)",
        "direccion": "Av. Concepción Arenal 1174",
        "confianza": "alta",
        "contrastado_en": "wikipedia;enacom;worldradiomap",
    },
    "105.3": {
        "genero": "music",
        "confianza": "baja",
        "contrastado_en": "wikipedia",
        "notas_extra": "Algunos listados la ubicaban en 105.1",
    },
    "105.5": {
        "genero": "music",
        "direccion": "Cerro de las Rosas (Juan Batlle Planas / Tristán Malbrán)",
        "confianza": "media",
        "contrastado_en": "wikipedia;worldradiomap;totalmedios",
    },
    "105.9": {
        "genero": "music",
        "nombre_legal": "FM ACTIVA",
        "direccion": "Tomás de Archondo 3153, Yofre Norte",
        "confianza": "alta",
        "contrastado_en": "wikipedia;oficial;enacom;worldradiomap",
        "sitio_web": "https://www.fmactiva.com/",
    },
    "106.3": {
        "genero": "music",
        "nombre_legal": "GAMBA",
        "direccion": "Obispo Oro 156",
        "radiocut_url": "https://radiocut.fm/radiostation/gamba/",
        "sitio_web": "http://www.gamba.fm/",
        "confianza": "alta",
        "contrastado_en": "wikipedia;enacom;radiocut;worldradiomap;totalmedios",
    },
    "106.9": {
        "genero": "music",
        "confianza": "media",
        "contrastado_en": "wikipedia",
        "notas_extra": "ENACOM también listó Bandera Nacional 106.9 Córdoba",
    },
    "107.3": {
        "genero": "music",
        "nombre_legal": "MUJER FM / URBANA (histórico)",
        "direccion": "Juan Bautista Daniel 1995",
        "confianza": "baja",
        "contrastado_en": "wikipedia;enacom;worldradiomap;totalmedios",
        "notas_extra": "Conflicto: Wikipedia Ranquel; WRM/TotalMedios Mujer FM; ENACOM Urbana",
    },
    "107.5": {
        "genero": "music",
        "direccion": "Av. San Martín 70",
        "confianza": "media",
        "contrastado_en": "wikipedia;worldradiomap",
        "notas_extra": "TotalMedios citó Radio con Vos en 107.5",
    },
    "107.7": {
        "genero": "religiosa",
        "direccion": "Haedo 1094",
        "confianza": "media",
        "contrastado_en": "wikipedia;worldradiomap",
    },
    "107.9": {
        "genero": "religiosa",
        "confianza": "media",
        "contrastado_en": "wikipedia",
    },
}

FIELDNAMES = [
    "frecuencia_mhz",
    "nombre",
    "grupo",
    "nombre_legal",
    "genero",
    "direccion",
    "sitio_web",
    "stream_url",
    "escucha_online",
    "stream_estado",
    "radiocut_url",
    "confianza",
    "contrastado_en",
    "fuente",
    "notas",
    "actualizado",
    "revisado",
]


def merge_notas(base: str, extra: str) -> str:
    parts = [p.strip() for p in (base or "").split(";") if p.strip()]
    if extra and extra not in parts:
        parts.append(extra)
    return "; ".join(parts)


def main() -> None:
    with CSV_PATH.open(encoding="utf-8", newline="") as f:
        rows = list(csv.DictReader(f))

    out = []
    for row in rows:
        freq = row["frecuencia_mhz"]
        ov = OVERLAY.get(freq, {})
        notas = merge_notas(row.get("notas", ""), ov.get("notas_extra", ""))
        sitio = ov.get("sitio_web") or row.get("sitio_web", "")
        out.append(
            {
                "frecuencia_mhz": freq,
                "nombre": row["nombre"],
                "grupo": row.get("grupo", ""),
                "nombre_legal": ov.get("nombre_legal", ""),
                "genero": ov.get("genero", ""),
                "direccion": ov.get("direccion", ""),
                "sitio_web": sitio,
                "stream_url": row.get("stream_url", ""),
                "escucha_online": row.get("escucha_online", "desconocido"),
                "stream_estado": "no_probado" if row.get("stream_url") else "",
                "radiocut_url": ov.get("radiocut_url", ""),
                "confianza": ov.get("confianza", "baja"),
                "contrastado_en": ov.get("contrastado_en", row.get("fuente", "")),
                "fuente": row.get("fuente", ""),
                "notas": notas,
                "actualizado": row.get("actualizado", REVISADO),
                "revisado": REVISADO,
            }
        )

    with CSV_PATH.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=FIELDNAMES, quoting=csv.QUOTE_MINIMAL)
        w.writeheader()
        w.writerows(out)

    print(f"Wrote {len(out)} rows -> {CSV_PATH}")


if __name__ == "__main__":
    main()
