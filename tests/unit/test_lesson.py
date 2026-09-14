from app.services.lesson import normalize_lesson, split_script


def test_split_script_drops_blank_and_caps_lines():
    script = "\nAlpha.\n\nBeta.\n"
    assert split_script(script) == ["Alpha.", "Beta."]


def test_split_sentences_in_a_paragraph():
    script = "Hello there. Second sentence? Third!"
    assert split_script(script) == ["Hello there.", "Second sentence?", "Third!"]


def test_split_does_not_trim_the_end_of_a_paragraph():
    para = (
        "This is something which is very good in recent and this has been very good "
        "that have been very good and this is something which is product is currently "
        "which is very reliable from me."
    )
    joined = " ".join(split_script(para))
    assert "reliable from me" in joined
    assert "This is something" in joined


def test_placeholder_lesson_is_instant_and_verbatim():
    from app.services.lesson import placeholder_lesson

    lines = ["An MCB is a miniature circuit breaker.", "It protects wiring from overload."]
    lesson = placeholder_lesson(lines)
    assert [segment.speech for segment in lesson.segments] == lines
    assert all(segment.board.elements for segment in lesson.segments)


def test_normalize_overwrites_llm_speech():
    lines = ["An MCB is a miniature circuit breaker.", "It protects wiring from overload."]
    raw = {
        "title": "Wrong",
        "topic": "Wrong",
        "segments": [
            {
                "title": "Invented",
                "speech": "I will explain circuit breakers in my own words.",
                "board": {
                    "elements": [
                        {"id": "t", "type": "text", "x": 10, "y": 10, "text": "MCB"}
                    ]
                },
            },
            {
                "title": "Also invented",
                "speech": "Totally new sentence.",
                "board": {
                    "elements": [
                        {"id": "u", "type": "rectangle", "x": 10, "y": 10, "label": {"text": "Protect"}}
                    ]
                },
            },
        ],
    }
    lesson = normalize_lesson(raw, lines)
    assert [seg.speech for seg in lesson.segments] == lines
    assert all(seg.board.mode == "replace" for seg in lesson.segments)
    assert all(len(seg.board.elements) >= 8 for seg in lesson.segments)


def test_normalize_keeps_llm_slide_not_board_chips():
    lines = ["LangGraph is a framework for building stateful multi-actor applications with LLMs."]
    raw = {
        "title": "LangGraph",
        "topic": "LangGraph",
        "segments": [
            {
                "title": "Graph of nodes and edges",
                "speech": "I will invent spoken text.",
                "slide": {
                    "headline": "LangGraph models a workflow as a graph",
                    "kicker": "How the app is structured",
                    "bullets": [
                        "Nodes do work such as LLM calls and tools.",
                        "Edges choose the next step in the run.",
                        "Shared state is passed through the graph.",
                    ],
                    "layout": "cards",
                },
                "board": {
                    "elements": [
                        {"id": "t", "type": "text", "x": 10, "y": 10, "text": "Makes"},
                        {"id": "u", "type": "rectangle", "x": 10, "y": 10, "label": {"text": "Useful"}},
                    ]
                },
            }
        ],
    }
    lesson = normalize_lesson(raw, lines)
    slide = lesson.segments[0].slide
    assert lesson.segments[0].speech == lines[0]
    assert "LangGraph models a workflow" in slide.headline
    assert "Nodes do work" in slide.bullets[0]
    assert "Makes" not in " ".join(slide.bullets)
    assert "Useful" not in " ".join(slide.bullets)


def test_placeholder_lesson_has_presentable_slides():
    from app.services.lesson import placeholder_lesson

    lines = ["An MCB is a miniature circuit breaker.", "It protects wiring from overload."]
    lesson = placeholder_lesson(lines)
    for segment in lesson.segments:
        assert len(segment.slide.bullets) == 3
        assert all(len(bullet.split()) >= 4 for bullet in segment.slide.bullets)
