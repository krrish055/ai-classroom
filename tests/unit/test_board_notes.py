from app.prompts.teacher import build_beat_user_prompt
from app.services.board_notes import board_is_dense, build_local_notes
from app.services.lesson import normalize_lesson


def test_mcb_demo_is_diagram_not_transcript():
    lines = [
        "An MCB is a miniature circuit breaker.",
        "It protects wiring from overload and short circuit.",
        "When current is too high, it trips and cuts the power.",
    ]
    notes = build_local_notes(lines)
    assert "MCB" in notes["title"]
    assert len(notes["segments"]) == 3
    types = {
        el["type"]
        for seg in notes["segments"]
        for el in seg["board"]["elements"]
    }
    assert "ellipse" in types
    assert "diamond" in types
    assert "arrow" in types
    labels = [
        (el.get("label") or {}).get("text") or el.get("text") or ""
        for seg in notes["segments"]
        for el in seg["board"]["elements"]
    ]
    assert not any(line in labels for line in lines)


def test_rambling_paragraph_uses_real_words_not_two_letters():
    notes = build_local_notes(
        [
            "This is something which is very good in recent and this has been very good "
            "that have been very good and this is something which is product is currently "
            "which is very reliable from me."
        ]
    )
    shape_labels = [
        ((el.get("label") or {}).get("text") or el.get("text") or "")
        for el in notes["segments"][0]["board"]["elements"]
        if el["type"] in {"ellipse", "rectangle", "diamond", "text"}
    ]
    assert shape_labels
    assert all(len(label.replace("…", "")) >= 4 for label in shape_labels if label)


def test_each_line_gets_a_full_board():
    notes = build_local_notes(
        [
            "LangGraph is a library for building stateful agent graphs.",
            "Nodes do work and edges decide the next step.",
        ]
    )
    for seg in notes["segments"]:
        elements = seg["board"]["elements"]
        assert len(elements) >= 8
        assert board_is_dense(elements)
        assert seg["board"]["mode"] == "replace"
    labels = " ".join(
        (el.get("label") or {}).get("text") or el.get("text") or ""
        for el in notes["segments"][0]["board"]["elements"]
    )
    assert "LangGraph" in labels or "Langgraph" in notes["title"]


def test_sparse_llm_board_is_filled():
    line = "LangGraph builds stateful graphs with nodes and edges."
    lesson = normalize_lesson(
        {
            "title": "LangGraph",
            "segments": [
                {
                    "title": "Thin",
                    "speech": "I made this up",
                    "board": {
                        "elements": [
                            {
                                "id": "junk",
                                "type": "ellipse",
                                "x": 10,
                                "y": 10,
                                "label": {"text": "AT"},
                            }
                        ]
                    },
                }
            ],
        },
        [line],
    )
    assert lesson.segments[0].speech == line
    assert lesson.segments[0].board.mode == "replace"
    assert len(lesson.segments[0].board.elements) >= 8
    labels = [
        (el.label or {}).get("text") or el.text or ""
        for el in lesson.segments[0].board.elements
    ]
    assert "AT" not in labels


def test_beat_prompt_sends_that_line_to_the_llm():
    lines = ["LangGraph uses a StateGraph.", "Then you compile and invoke it."]
    prompt = build_beat_user_prompt(lines, "\n".join(lines), 1)
    assert "line 2 of 2" in prompt
    assert "compile and invoke" in prompt
    assert "b2_" in prompt
