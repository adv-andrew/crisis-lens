"""
Gemini API integration — natural language description -> diagram code.
"""

import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).parent.parent / ".env")

SYSTEM_PROMPT = """You are an expert at creating academic figures for research papers using diagram markup languages.

Given a natural language description, generate clean, publication-quality diagram code.

Rules:
- Return ONLY the raw diagram code — no markdown fences, no prose, no explanations
- Use minimal, precise labels suited for academic papers
- Prefer left-to-right (LR) layout for process flows; top-to-bottom (TD) for hierarchies
- Use standard shapes: rectangles for processes, diamonds for decisions, rounded/cylinders for data stores
- Rely on structure to convey meaning — avoid decorative colors
- Keep diagrams focused: one concept per figure"""

TYPE_GUIDANCE = {
    "mermaid": """Mermaid syntax. Start with the diagram type declaration.

Valid opening lines:
  graph LR
  graph TD
  flowchart LR
  sequenceDiagram
  classDiagram
  erDiagram

Example:
  graph LR
    A[Data Source] --> B[Processor] --> C[(Database)]""",

    "graphviz": """DOT language (Graphviz). Use digraph for directed, graph for undirected.
Set rankdir=LR for left-to-right layout.

Example:
  digraph G {
    rankdir=LR;
    node [shape=box];
    A -> B -> C;
  }""",

    "d2": """D2 diagram syntax. Minimal and clean.

Use -> for connections. Group nodes in containers with {}.
Use shape: cylinder for databases, shape: oval for external systems.

Example:
  direction: right
  source -> processor -> output
  processor: {shape: rectangle}""",

    "plantuml": """PlantUML syntax. Always start with @startuml and end with @enduml.

Example:
  @startuml
  [A] --> [B] : label
  @enduml""",
}


def generate_diagram_code(
    description: str,
    diagram_type: str,
    model: str = "gemini-2.0-flash",
) -> str:
    """
    Call Gemini to generate diagram code for the given description.
    Returns the raw diagram source string.
    """
    try:
        from google import genai
        from google.genai import types
    except ImportError:
        raise ImportError(
            "google-genai package not installed. Run: pip install google-genai"
        )

    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise EnvironmentError(
            "GEMINI_API_KEY not set. Add it to your .env file or environment."
        )

    client = genai.Client(api_key=api_key)

    user_message = (
        f"Generate {diagram_type} diagram code for this academic figure:\n\n"
        f"{description}\n\n"
        f"{TYPE_GUIDANCE[diagram_type]}\n\n"
        "Return ONLY the diagram code."
    )

    response = client.models.generate_content(
        model=model,
        contents=user_message,
        config=types.GenerateContentConfig(
            system_instruction=SYSTEM_PROMPT,
            max_output_tokens=2048,
        ),
    )

    code = response.text.strip()

    # Strip markdown fences if the model added them despite instructions
    if code.startswith("```"):
        lines = code.split("\n")
        end = len(lines) - 1 if lines[-1].strip() == "```" else len(lines)
        code = "\n".join(lines[1:end]).strip()

    return code
