# Fuentes y vigencia — radios FM Ciudad de Córdoba

Catálogo: [`radios_fm_cordoba.csv`](radios_fm_cordoba.csv)

## Jerarquía de fuentes

De mayor a menor peso para decidir nombre comercial y frecuencia:

1. **Sitio oficial / player del grupo** (Cadena 3, Cienradios, Grupo Shopping, LV2, SRT/UNC, Radio María, etc.)
2. **ENACOM** — [Registro SCA](https://registros-sca.enacom.gob.ar/licencias-autorizaciones/) y listados de reconocidas/permisos. Sirve para existencia legal y localidad; el `nombre_legal` suele diferir de la marca al aire.
3. **RadioCut** (`radiocut.fm`) — vigencia de audio (si hay capturas recientes, la señal está viva) y URL de escucha. Cobertura incompleta; a veces conserva marcas viejas (ej. Pulxo en 95.1).
4. **Wikipedia** — [Medios de la Ciudad de Córdoba](https://es.wikipedia.org/wiki/Medios_de_comunicaci%C3%B3n_de_la_Ciudad_de_C%C3%B3rdoba_(Argentina)). Buen dial comercial; no siempre al día.
5. **World Radio Map** — [Córdoba](https://worldradiomap.com/ar/cordoba). Útil para domicilio/antena; mezcla capital y alrededores.
6. **TotalMedios** (tarifas Córdoba capital) — dial comercial publicitario; puede atrasarse.
7. **Agregadores** (myTuner, TuneIn, radios-argentinas, etc.) — solo para streams y aliases; mucho ruido.

RadioCut no es padrón oficial: es evidencia de **stream vivo / archivo reciente**.

## Campos de calidad en el CSV

| Campo | Significado |
|---|---|
| `confianza` | `alta` / `media` / `baja` |
| `contrastado_en` | Fuentes que respaldan la fila |
| `nombre_legal` | Nombre ENACOM / permiso si se conoció |
| `radiocut_url` | Ficha RadioCut si existe |
| `stream_estado` | `ok` / `roto` / `no_probado` / vacío |
| `revisado` | Última pasada de contraste o probe |

### Reglas de `confianza`

- **alta**: sitio oficial actual + frecuencia alineada con Wikipedia o ENACOM
- **media**: 2+ catálogos coinciden sin oficial claro
- **baja**: una sola fuente, o conflicto entre fuentes (se documenta en `notas`)

Ante conflicto de **nombre** (misma emisora, marcas distintas en el tiempo) se documenta en `notas` y baja `confianza`.

Ante **superposición de espectro** (dos proyectos distintos en el mismo MHz: permiso comunitario vs usurpación/interferencia, o dos marcas al aire), **no se unifica**: van **dos filas** con la misma `frecuencia_mhz`, cruzadas en `notas`. Ejemplos en el CSV: 93.9 Quinta Pata / CIEC; 99.5 Zumba la Turba / Rivadavia interferencia; 87.9 Rivadavia (ilegal ENACOM) / Rock & Pop.

## Scripts

```bash
# Reaplicar overlays de contraste (no toca el probe)
python3 scripts/enrich_catalog.py

# Completar sitios/streams faltantes (overrides + Radio Browser)
python3 scripts/fill_missing_streams.py

# Probar streams y actualizar stream_estado / escucha_online
python3 scripts/check_streams.py

# Resolver HTML→audio (overrides), actualizar CSV y generar M3U dial
python3 scripts/build_vlc_playlist.py
```

El probe acepta 2xx/3xx, páginas HTML de player oficial y content-types de audio/HLS. Si falla: `stream_estado=roto`, `escucha_online=desconocido` (se conserva `stream_url`).

## Playlist VLC (orden de dial)

- Archivo: [`playlists/cordoba_fm_dial.m3u`](playlists/cordoba_fm_dial.m3u)
- Uso: `vlc playlists/cordoba_fm_dial.m3u` — “siguiente” = siguiente frecuencia.
- Regenerar: `python3 scripts/build_vlc_playlist.py` (actualiza `stream_url` directos en el CSV cuando hay override, y solo incluye URLs que pasan probe de audio).
- Cobertura (2026-11-06): **52** emisoras en el M3U de **70** filas del CSV. Quedan afuera: sin URL, player HTML sin stream directo hallado (Revés, Más Radio/Kick, Nuevo Tiempo DNS muerto, CNN Suenas 404, LV2/Vida edge player, Orfeo RadioCut, Zumba), y Continental (URL conocida pero probe 403 intermitente).

## Cadencia de revisión sugerida

| Qué | Cada |
|---|---|
| Dial / nombres comerciales | 90 días |
| Streams con `stream_estado=ok` | 30 días |
| Filas `confianza=baja` o conflictos | en la próxima pasada o cuando haya fuente oficial nueva |
| ENACOM nombre legal | cuando haya duda legal o cambio de licencia |

## Conflictos conocidos (a seguir)

- **88.1** — Nac&Pop: **fuera_capital** (Darregueira, Bs. As.; Garden mal geolocalizado). Excluida del M3U/web.
- **90.3** — Sonidera (Wikipedia) vs Cosquín Rock (World Radio Map)
- **91.3** — Más Radio; Radio Garden/agregadores como *Kuarteto.com* (alias, no fila dual)
- **95.1** — filas duales: Vida Córdoba (Wikipedia / LV2) vs Pulxo (RadioCut / Radio Garden); ENACOM histórico Cultura
- **95.5** — Cosquín Rock vs Sonidera según fuente
- **95.7** — Impacto Musical: `capital_no_confirmada`
- **96.7** — Folklore (capital) + hacinamiento Garden: Cadena Space **fuera_capital** (Valle de Punilla); Estación Norte / Minuto `capital_no_confirmada`
- **96.9** — filas duales: Día & Noche vs FM Amistad (ENACOM / WRM / Radio Garden)
- **97.5** — Más Radio: **fuera_capital** (repetidora Jesús María). Excluida del M3U/web.
- **98.9** — La Red vs Suquía Plus
- **102.3** — Más que música / CBA24 / FM SRT (alias mismo ecosistema SRT)
- **107.3** — Ranquel: `capital_no_confirmada` (posible Río Cuarto) vs Mujer FM / Urbana en listados

### Marcas de auditoría en `notas`

- `fuera_capital: …` — no es Ciudad de Córdoba; el builder de playlist la omite.
- `capital_no_confirmada: …` — se conserva en CSV/M3U si tiene stream, pendiente de contraste.

## Alcance

Solo **FM** y **Ciudad de Córdoba**. No incluye AM, solo-online sin frecuencia, ni Gran Córdoba salvo nota explícita. Filas `fuera_capital` quedan documentadas en el CSV pero no entran al dial VLC/web.
