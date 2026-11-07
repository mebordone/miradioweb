# Dial FM Córdoba

Player web liviano del dial FM de Córdoba Capital: power, anterior/siguiente y lista de emisoras, con ruido de sintonía al cambiar.

## Probar en local

```bash
cd web && python3 -m http.server 18901 --bind 0.0.0.0
```

Abrí `http://localhost:18901/` (o la IP de la PC en la misma red).

## Repo

- Catálogo: `radios_fm_cordoba.csv`
- Playlist VLC: `playlists/cordoba_fm_dial.m3u`
- Web: `web/`
- Regenerar M3U / streams: `python3 scripts/build_vlc_playlist.py`

Demo: https://mebordone.github.io/miradioweb/
