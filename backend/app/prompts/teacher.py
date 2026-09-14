from app.core.settings import settings


def build_notes_prompt() -> str:
    return """You design a live training deck. One slide per spoken line.

The spoken script is already being read aloud. You do NOT write speech and you do NOT
copy the spoken sentence onto the slide. You teach the TOPIC with presentable demo slides.

CRITICAL
- If the script is about LangGraph, teach StateGraph, nodes, edges, shared state, compile.
- If it is about an MCB, teach definition, overload, trip, wiring protection.
- Never harvest leftover words. Never chips like "Makes", "Useful", "Line 1", "AT".
- Each slide has a 3-8 word headline and exactly 3 teaching bullets of 6-14 words.
- layout is title | cards | steps | bullets. Use title for the opening beat.

Return one JSON object, no markdown:

{
  "title": "2-4 word topic",
  "topic": "same",
  "segments": [
    {
      "id": "s1",
      "title": "short slide title",
      "slide": {
        "headline": "Demo-quality headline",
        "kicker": "How it works",
        "bullets": ["Teaching point one.", "Teaching point two.", "Teaching point three."],
        "layout": "cards"
      }
    }
  ]
}
"""


def build_beat_notes_prompt() -> str:
    return f"""You are a presentation designer for a live product demo.

One spoken line is playing. Design ONE slide that teaches the TOPIC of that line.
The spoken line is already being read aloud. Do NOT put that sentence on the slide.

Return ONE JSON object, no markdown, no segments array:

{{
  "title": "2-4 word lesson topic",
  "topic": "same",
  "beatTitle": "this slide headline, 3-8 words",
  "kicker": "short eyebrow such as How it works",
  "bullets": [
    "Teaching point in 6-14 words.",
    "Second teaching point in 6-14 words.",
    "Third teaching point in 6-14 words."
  ],
  "layout": "cards"
}}

layout must be one of: title, cards, steps, bullets
- title: opening/overview (use for line 1 when it introduces the topic)
- cards: three equal teaching cards (default)
- steps: numbered process
- bullets: left-aligned talking points

RULES
- Exactly 3 bullets. Complete teaching phrases, not leftover words.
- Never: Makes, Useful, Line 1, AT, truncated chips, or a copy of the spoken line.
- If the topic is LangGraph, teach graph, nodes, edges, state — not random ramble words.
- Headline: 3-8 words, consultant-demo quality.
- You may ignore the old blackboard. Canvas size {settings.max_board_elements_per_segment} is unused here.
"""


def build_notes_user_prompt(lines: list[str], full_script: str = "") -> str:
    numbered = "\n".join(f"{index + 1}. {line}" for index, line in enumerate(lines))
    context = (full_script or "\n".join(lines)).strip()
    return (
        "FULL SCRIPT (understand the topic; do not copy it onto slides):\n"
        f"{context}\n\n"
        "SPOKEN BEATS (spoken verbatim; one presentable slide per beat, ids "
        f"s1 to s{len(lines)}):\n"
        f"{numbered}\n\n"
        "Build a demo deck. Headline + 3 teaching bullets on every slide."
    )


def build_beat_user_prompt(lines: list[str], full_script: str, index: int) -> str:
    context = (full_script or "\n".join(lines)).strip()
    line = lines[index]
    numbered = "\n".join(f"{i + 1}. {item}" for i, item in enumerate(lines))
    return (
        f"FULL SCRIPT (topic context):\n{context}\n\n"
        f"ALL SPOKEN LINES:\n{numbered}\n\n"
        f"THIS BEAT is line {index + 1} of {len(lines)}.\n"
        f"Prefix every element id with b{index + 1}_\n"
        f"SPOKEN LINE (do not copy; teach what it is about):\n{line}\n\n"
        "Return headline, kicker, 3 bullets, and layout for a live demo slide."
    )
