"""Renders PlantUML text to SVG via the public plantuml.com server, free, no
account or API key. Only send code structure through this for PUBLIC repos,
for private/proprietary code, run a local PlantUML jar instead, see README.
"""
import zlib
import urllib.request

_ALPHABET = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz-_"


def _encode6(b: int) -> str:
    return _ALPHABET[b & 0x3F]


def _plantuml_encode(text: str) -> str:
    compressor = zlib.compressobj(9, zlib.DEFLATED, -15)
    raw = compressor.compress(text.encode("utf-8")) + compressor.flush()

    out = []
    for i in range(0, len(raw), 3):
        chunk = raw[i:i + 3]
        b1 = chunk[0]
        b2 = chunk[1] if len(chunk) > 1 else 0
        b3 = chunk[2] if len(chunk) > 2 else 0
        out.append(_encode6(b1 >> 2))
        out.append(_encode6(((b1 & 0x3) << 4) | (b2 >> 4)))
        if len(chunk) > 1:
            out.append(_encode6(((b2 & 0xF) << 2) | (b3 >> 6)))
        if len(chunk) > 2:
            out.append(_encode6(b3 & 0x3F))
    return "".join(out)


def render_svg(plantuml_text: str, server: str = "https://www.plantuml.com/plantuml") -> bytes:
    url = f"{server}/svg/{_plantuml_encode(plantuml_text)}"
    req = urllib.request.Request(url, headers={"User-Agent": "specsync/0.1"})
    with urllib.request.urlopen(req, timeout=20) as resp:
        return resp.read()
