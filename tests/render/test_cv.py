import pytest

from app.content.loader import load_content
from app.content.models import Job, Static, Title
from app.content.selection.models import SelectedBullet, SelectedJob, Selection, SkillLine
from app.content.selection.pipeline import select
from app.content.selection.request import SelectionRequest
from app.core.config import ContactSettings
from app.render.cv import render_cv

CONTACT = ContactSettings.model_validate(
    {"email": "jane_doe@example.com", "phone": "+45 00 00 00 00", "linkedin": "https://www.example.com/in/jane-doe"}
)


def _job() -> Job:
    return Job.model_validate(
        {
            "id": "rnd",
            "company": "R&D Labs",
            "employment": "Full Time",
            "location": "Testville",
            "descriptions": [{"text": "Made things."}],
            "roles": [{"title": "Developer", "start": "2020-01-01"}],
            "bullets": [
                {"id": "shown", "variants": [{"text": "Shipped the shown thing 2× faster."}]},
                {"id": "plain", "variants": [{"text": "Wrote the plain thing."}]},
                {"id": "hidden", "variants": [{"text": "Did the hidden thing."}]},
            ],
        }
    )


@pytest.fixture
def selection() -> Selection:
    return Selection(
        title=Title(id="engineer", label="Engineer", profile="Writes code."),
        static=Static(name="Test Person", city="Testville", projects=[], education=[]),
        jobs=[
            SelectedJob(
                job=_job(),
                description="Made things.",
                bullets=[
                    SelectedBullet(bullet_id="shown", text="Shipped the shown thing 2× faster.", highlight="2× faster"),
                    SelectedBullet(bullet_id="plain", text="Wrote the plain thing."),
                ],
            )
        ],
        skill_lines=[SkillLine(label="Programming", skills=["Python", "C#"])],
    )


def test_contact_details_are_unwrapped_and_escaped(selection: Selection) -> None:
    source = render_cv(selection, CONTACT)

    assert r"jane\_doe@example.com" in source
    assert "+45 00 00 00 00" in source
    assert "*****" not in source


def test_content_text_is_escaped(selection: Selection) -> None:
    source = render_cv(selection, CONTACT)

    assert r"R\&D Labs" in source
    assert r"C\#" in source


def test_highlight_is_wrapped_in_metric(selection: Selection) -> None:
    source = render_cv(selection, CONTACT)

    assert r"Shipped the shown thing \metric{2× faster}." in source


def test_only_selected_bullets_are_rendered(selection: Selection) -> None:
    source = render_cv(selection, CONTACT)

    assert "Wrote the plain thing." in source
    assert "Did the hidden thing." not in source


@pytest.mark.parametrize("title_id", [title.id for title in load_content().titles])
def test_real_content_renders_for_every_title(title_id: str) -> None:
    content = load_content()
    request = SelectionRequest.model_validate(
        {"title_id": title_id, "concept_ids": [], "skill_ids": []}, context={"content": content}
    )

    source = render_cv(select(content, request), CONTACT)

    assert source.startswith(r"\documentclass")
    assert source.rstrip().endswith(r"\end{document}")
