#!/usr/bin/env python3
"""
figuregen — Natural language -> diagram code (Gemini) -> rendered figure (Kroki)

Usage:
    python figuregen/generate.py "description" [options]

Examples:
    python figuregen/generate.py "flowchart of OCI computation from raw data to score"
    python figuregen/generate.py "system architecture" --type d2 --out figures/arch.svg
    python figuregen/generate.py "funding flow diagram" --type graphviz --format pdf
    python figuregen/generate.py "sequence diagram of API calls" --show-code
    python figuregen/generate.py --from-code my_diagram.mmd --type mermaid --format pdf
"""

import argparse
import sys
from pathlib import Path

# Allow sibling imports regardless of working directory
sys.path.insert(0, str(Path(__file__).parent))

from llm import generate_diagram_code
from render import render_diagram, KrokiError

DIAGRAM_TYPES = ["mermaid", "graphviz", "d2", "plantuml"]
OUTPUT_FORMATS = ["svg", "pdf", "png"]


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Generate academic figures from natural language via Claude + Kroki",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument(
        "description",
        nargs="?",
        help="Natural language description of the figure",
    )
    parser.add_argument(
        "--type", "-t",
        choices=DIAGRAM_TYPES,
        default="mermaid",
        help="Diagram syntax to use (default: mermaid)",
    )
    parser.add_argument(
        "--format", "-f",
        choices=OUTPUT_FORMATS,
        default="svg",
        help="Output format (default: svg)",
    )
    parser.add_argument(
        "--out", "-o",
        help="Output file path (default: figure.<format>)",
    )
    parser.add_argument(
        "--show-code",
        action="store_true",
        help="Print the generated diagram code before rendering",
    )
    parser.add_argument(
        "--code-only",
        action="store_true",
        help="Only generate and print diagram code, skip Kroki rendering",
    )
    parser.add_argument(
        "--from-code",
        metavar="FILE",
        help="Render an existing diagram code file (skips LLM step)",
    )
    parser.add_argument(
        "--model",
        default="gemini-2.0-flash",
        help="Gemini model to use (default: gemini-2.0-flash)",
    )

    args = parser.parse_args()

    if not args.description and not args.from_code:
        parser.print_help()
        return 1

    out_path = args.out or f"figure.{args.format}"

    # Step 1: Get diagram code
    if args.from_code:
        code = Path(args.from_code).read_text()
        print(f"Using code from: {args.from_code}")
    else:
        print(f"[1/2] Generating {args.type} code via Claude...")
        try:
            code = generate_diagram_code(args.description, args.type, args.model)
        except (ImportError, EnvironmentError) as e:
            print(f"Error: {e}", file=sys.stderr)
            return 1

    if args.show_code or args.code_only:
        print(f"\n{'─' * 60}")
        print(f"  {args.type.upper()}")
        print(f"{'─' * 60}")
        print(code)
        print(f"{'─' * 60}\n")

    if args.code_only:
        return 0

    # Step 2: Render via Kroki
    print(f"[2/2] Rendering via Kroki ({args.format.upper()})...")
    try:
        render_diagram(code, args.type, args.format, out_path)
        print(f"Saved: {out_path}")
    except KrokiError as e:
        print(f"Render failed: {e}", file=sys.stderr)
        print("Tip: re-run with --show-code to inspect the generated code.", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
