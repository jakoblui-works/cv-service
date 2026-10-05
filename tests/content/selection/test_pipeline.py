from app.content.models import Content
from app.content.selection.models import Selection
from app.content.selection.pipeline import select
from app.content.selection.request import SelectionRequest
from tests.content.builder import Builder


def _content(build: Builder) -> Content:
    highlighted = build.variant("Built it in Python.", highlights=[build.highlight("Python", tags=["python"])])
    return build.content(
        skills=[
            build.category("languages", [build.skill("danish")], pinned=True),
            build.category("programming", [build.skill("python"), build.skill("rust")]),
        ],
        concepts=[build.concept("backend", implies=["python"])],
        titles=[build.title("lead", emphasis=["backend"])],
        jobs=[
            build.job(
                "newer",
                bullets=[build.bullet("n1", tags=["python"], variants=[highlighted]), build.bullet("n2")],
            ),
            build.job("older", bullets=[build.bullet("o1")]),
        ],
        layout={"max_bullets_total": 20, "min_bullets_per_job": 1, "max_skill_lines": 20, "max_highlights": 1},
    )


def _select(build: Builder, **request: object) -> Selection:
    content = _content(build)
    return select(content, SelectionRequest.model_validate(request, context={"content": content}))


def test_pipeline_uses_requested_title(build: Builder) -> None:
    selection = _select(build, title_id="lead")

    assert selection.title.id == "lead"


def test_pipeline_keeps_job_order(build: Builder) -> None:
    selection = _select(build, title_id="lead")

    assert [job.job.id for job in selection.jobs] == ["newer", "older"]


def test_pipeline_attaches_highlight_to_its_bullet(build: Builder) -> None:
    selection = _select(build, title_id="lead", skill_ids=["python"])

    highlights = {bullet.bullet_id: bullet.highlight for bullet in selection.jobs[0].bullets}

    assert highlights == {"n1": "Python", "n2": None}


def test_pipeline_puts_pinned_skill_line_first(build: Builder) -> None:
    selection = _select(build, title_id="lead", skill_ids=["rust"])

    assert selection.skill_lines[0].label == "Languages"
