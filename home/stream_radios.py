"""
Obtiene y lista las radios disponibles en https://imparg.org/stream/
Parseando la página HTML del servidor Icecast2.
"""

import re
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Optional

# Base relativa para enlaces de reproducción (mismo dominio: impa.ar o imparg.org)
STREAM_PUBLIC_BASE = "/stream"

# URLs para obtener el status (probar interna primero si la VM no alcanza imparg.org)
_STREAM_STATUS_CANDIDATES = [
    "http://192.168.1.40:3000",   # interna: máquina del stream
    "https://imparg.org/stream",  # pública
]


@dataclass
class RadioStream:
    """Representa un punto de emisión de radio del stream Icecast."""

    mount_point: str  # ej: /centro.mp3
    stream_url: str  # URL directa para reproducir (MP3)
    description: str = ""
    bitrate: str = ""
    listeners_current: str = ""
    listeners_peak: str = ""
    currently_playing: str = ""
    genre: str = ""
    stream_started: str = ""

    @property
    def nombre_display(self) -> str:
        """Nombre legible (ej: centro.mp3 → Centro)."""
        base = self.mount_point.strip("/").replace(".mp3", "")
        return base.capitalize()


def obtener_radios_stream(timeout: int = 15) -> list[RadioStream]:
    """
    Consulta la página de status de Icecast y devuelve la lista de radios.
    Prueba primero la URL interna (192.168.1.40) y luego la pública.
    Los enlaces de reproducción usan path relativo /stream/ (mismo dominio que el sitio).

    Returns:
        Lista de RadioStream con los datos de cada punto de emisión.

    Raises:
        urllib.error.URLError: Si no se puede conectar a ninguna URL.
    """
    last_error = None
    for base in _STREAM_STATUS_CANDIDATES:
        url = base.rstrip("/") + "/"
        try:
            req = urllib.request.Request(
                url,
                headers={"User-Agent": "IMPA-Radios-Fetcher/1.0"},
            )
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                html = resp.read().decode("utf-8", errors="replace")
            return _parsear_html_icecast(html, stream_base=STREAM_PUBLIC_BASE)
        except Exception as e:
            last_error = e
            continue
    raise last_error  # type: ignore


def _parsear_html_icecast(html: str, stream_base: str = STREAM_PUBLIC_BASE) -> list[RadioStream]:
    """Extrae los mount points del HTML de Icecast."""
    radios: list[RadioStream] = []

    # Dividir por cada bloque roundbox (cada bloque es una radio)
    parts = html.split('<div class="roundbox">')
    blocks = [p for p in parts[1:]]  # ignorar la parte anterior al primer roundbox

    for block in blocks:
        mount_match = re.search(
            r'<h3\s+class="mount">Mount Point\s+([^<]+)</h3>',
            block,
            re.IGNORECASE,
        )
        if not mount_match:
            continue

        mount_point = mount_match.group(1).strip()
        if not mount_point.startswith("/"):
            mount_point = "/" + mount_point

        # Construir URL del stream MP3 (siempre pública para que el usuario pueda escuchar)
        stream_url = f"{stream_base.rstrip('/')}{mount_point}"

        def _extraer_campo(bloque: str, etiqueta: str) -> str:
            pat = re.compile(
                rf'<td>\s*{re.escape(etiqueta)}\s*</td>\s*<td[^>]*>([^<]*)</td>',
                re.IGNORECASE,
            )
            m = pat.search(bloque)
            return (m.group(1).strip()) if m else ""

        description = _extraer_campo(block, "Stream Description:")
        bitrate = _extraer_campo(block, "Bitrate:")
        listeners_current = _extraer_campo(block, "Listeners (current):")
        listeners_peak = _extraer_campo(block, "Listeners (peak):")
        currently_playing = _extraer_campo(block, "Currently playing:")
        genre = _extraer_campo(block, "Genre:")
        stream_started = _extraer_campo(block, "Stream started:")

        radios.append(
            RadioStream(
                mount_point=mount_point,
                stream_url=stream_url,
                description=description or "Sin descripción",
                bitrate=bitrate,
                listeners_current=listeners_current,
                listeners_peak=listeners_peak,
                currently_playing=currently_playing,
                genre=genre,
                stream_started=stream_started,
            )
        )

    return radios


def main() -> None:
    """Imprime en consola las radios disponibles y sus URLs MP3."""
    print("Consultando status del stream (imparg.org/stream/ o interna)...\n")
    try:
        radios = obtener_radios_stream()
    except urllib.error.URLError as e:
        print(f"Error al conectar: {e}")
        return

    if not radios:
        print("No se encontraron radios en la página.")
        return

    print(f"Radios encontradas: {len(radios)}\n")
    print("-" * 60)
    for r in radios:
        print(f"  {r.nombre_display}")
        print(f"    Mount:   {r.mount_point}")
        print(f"    Stream:  {r.stream_url}")
        if r.currently_playing:
            print(f"    En vivo: {r.currently_playing}")
        if r.bitrate:
            print(f"    Bitrate: {r.bitrate} kbps")
        if r.listeners_current:
            print(f"    Oyentes: {r.listeners_current} (pico: {r.listeners_peak})")
        print()


if __name__ == "__main__":
    main()
