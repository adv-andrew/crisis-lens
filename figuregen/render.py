"""
Kroki API integration — diagram code -> rendered SVG / PDF / PNG.

Kroki (https://kroki.io) is a free, open-source diagram rendering service.
It supports Mermaid, Graphviz, D2, PlantUML, Excalidraw, Vega, and more.
"""

import requests
from pathlib import Path

KROKI_BASE_URL = "https://kroki.io"

# Map local type names -> Kroki path segment (mostly identical)
KROKI_TYPE_MAP = {
    "mermaid": "mermaid",
    "graphviz": "graphviz",
    "d2": "d2",
    "plantuml": "plantuml",
}


class KrokiError(RuntimeError):
    pass


def render_diagram(
    code: str,
    diagram_type: str,
    output_format: str,
    out_path: str,
    timeout: int = 30,
) -> bytes:
    """
    POST diagram source to Kroki and write the rendered output to out_path.

    Args:
        code:          Raw diagram source code.
        diagram_type:  One of mermaid, graphviz, d2, plantuml.
        output_format: One of svg, pdf, png.
        out_path:      Destination file path (parent dirs are created if needed).
        timeout:       Request timeout in seconds.

    Returns:
        The raw bytes written to out_path.

    Raises:
        KrokiError: On network failure or non-200 response from Kroki.
    """
    kroki_type = KROKI_TYPE_MAP.get(diagram_type, diagram_type)
    url = f"{KROKI_BASE_URL}/{kroki_type}/{output_format}"

    try:
        resp = requests.post(
            url,
            data=code.encode("utf-8"),
            headers={"Content-Type": "text/plain"},
            timeout=timeout,
        )
    except requests.exceptions.Timeout:
        raise KrokiError(
            f"Kroki request timed out after {timeout}s. Check your internet connection."
        )
    except requests.exceptions.ConnectionError as e:
        raise KrokiError(
            f"Could not connect to kroki.io: {e}"
        )

    if resp.status_code != 200:
        raise KrokiError(
            f"Kroki returned HTTP {resp.status_code}:\n{resp.text[:500]}"
        )

    dest = Path(out_path)
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_bytes(resp.content)

    return resp.content
