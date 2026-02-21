# figuregen

One-command academic figure generation: natural language → Claude → diagram code → Kroki render → SVG/PDF.

## Pipeline

```
description (text)
      |
      v
  Gemini LLM  ──────────────────────────────────────────────>  diagram code
  (llm.py)    Mermaid | Graphviz | D2 | PlantUML               (text)
                                                                  |
                                                                  v
                                                            Kroki API
                                                            (render.py)
                                                                  |
                                                                  v
                                                         SVG / PDF / PNG
```

## Setup

**1. Install dependencies**

```bash
pip install google-genai requests python-dotenv
```

**2. Set your API key**

Add to your `.env` file at the project root:

```
GEMINI_API_KEY=AIza...
```

Get a key at [aistudio.google.com](https://aistudio.google.com/app/apikey).

## Usage

```bash
# Basic — generates figure.svg in the current directory
python figuregen/generate.py "flowchart of OCI computation pipeline"

# Specify type, format, and output path
python figuregen/generate.py "system architecture with data lake and ML models" \
  --type d2 --format pdf --out figures/architecture.pdf

# See the generated code before rendering
python figuregen/generate.py "sequence diagram of API request flow" --show-code

# Generate code only (no render, useful for editing before rendering)
python figuregen/generate.py "funding gap analysis flow" --code-only

# Render an existing diagram file you already have
python figuregen/generate.py --from-code my_diagram.mmd --type mermaid --format svg
```

## Options

| Flag | Description |
|------|-------------|
| `--type`, `-t` | `mermaid` (default), `graphviz`, `d2`, `plantuml` |
| `--format`, `-f` | `svg` (default), `pdf`, `png` |
| `--out`, `-o` | Output file path (default: `figure.<format>`) |
| `--show-code` | Print generated diagram code before rendering |
| `--code-only` | Only generate and print code, skip rendering |
| `--from-code FILE` | Render an existing diagram file (skip LLM) |
| `--model` | Gemini model (default: `gemini-2.0-flash`) |

## Diagram Types

| Type | Best For |
|------|----------|
| `mermaid` | Flowcharts, sequence diagrams, ER diagrams, class diagrams |
| `graphviz` | Network graphs, dependency trees, complex layouts |
| `d2` | System architecture, component diagrams |
| `plantuml` | UML, activity diagrams, use case diagrams |

Rendering is handled by [Kroki](https://kroki.io) — a free, open-source hosted API that supports all four types. No local installation required.

## CrisisLens Examples

Pre-written descriptions for the paper figures are in `examples/`:

```bash
# OCI data pipeline (full system)
python figuregen/generate.py "$(cat figuregen/examples/oci_pipeline.txt)" \
  --type mermaid --out figures/oci_pipeline.svg

# Humanitarian funding flow
python figuregen/generate.py "$(cat figuregen/examples/funding_flow.txt)" \
  --type graphviz --out figures/funding_flow.svg

# CBPF project recommender system
python figuregen/generate.py "$(cat figuregen/examples/cbpf_recommender.txt)" \
  --type mermaid --out figures/cbpf_recommender.svg
```

## Iterating on a Figure

The recommended workflow for getting a figure exactly right:

```bash
# Step 1: Generate code and inspect it
python figuregen/generate.py "your description" --code-only > my_diagram.mmd

# Step 2: Edit the code manually if needed
# (open my_diagram.mmd in any text editor)

# Step 3: Render from the edited file
python figuregen/generate.py --from-code my_diagram.mmd --type mermaid \
  --format pdf --out figures/my_figure.pdf
```
