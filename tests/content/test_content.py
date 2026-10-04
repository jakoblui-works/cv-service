import pytest
from pydantic import ValidationError

from app.content.loader import load_content
from app.content.models import Content


def _content(**overrides: object) -> dict[str, object]:
    data: dict[str, object] = {
        "static": {"name": "Test Person", "city": "Testville", "projects": [], "education": []},
        "skills": [{"id": "programming", "label": "Programming", "skills": [{"id": "python", "label": "Python"}]}],
        "concepts": [{"id": "backend", "label": "Backend", "implies": ["python"]}],
        "titles": [{"id": "engineer", "label": "Engineer", "profile": "Writes code.", "emphasis": ["backend"]}],
        "experience": [
            {
                "id": "acme",
                "company": "Acme",
                "employment": "Full Time",
                "location": "Testville",
                "description": "Made things.",
                "roles": [{"title": "Developer", "start": "2020-01-01"}],
                "bullets": [{"text": "Built a thing.", "tags": ["python", "backend"]}],
            }
        ],
        "layout": {"max_bullets_total": 10, "min_bullets_per_job": 1, "max_skill_lines": 5},
    }
    return data | overrides


def test_real_content_loads() -> None:
    content = load_content()

    assert content.skills[0].pinned
    assert [job.id for job in content.experience] == ["acembee", "confect", "confect-ml"]


def test_minimal_content_is_valid() -> None:
    Content.model_validate(_content())


def test_unknown_bullet_tag() -> None:
    experience = [
        {
            "id": "acme",
            "company": "Acme",
            "employment": "Full Time",
            "location": "Testville",
            "description": "Made things.",
            "roles": [{"title": "Developer", "start": "2020-01-01"}],
            "bullets": [{"text": "Built a thing.", "tags": ["cobol"]}],
        }
    ]

    with pytest.raises(ValidationError, match="unknown id 'cobol' in tags of bullet 0 in job 'acme'"):
        Content.model_validate(_content(experience=experience))


def test_unknown_implies_entry() -> None:
    concepts = [{"id": "backend", "label": "Backend", "implies": ["cobol"]}]

    with pytest.raises(ValidationError, match="unknown id 'cobol' in implies of concept 'backend'"):
        Content.model_validate(_content(concepts=concepts))


def test_implies_must_be_a_skill() -> None:
    concepts = [
        {"id": "backend", "label": "Backend", "implies": ["python"]},
        {"id": "devops", "label": "DevOps", "implies": ["backend"]},
    ]

    with pytest.raises(ValidationError, match="unknown id 'backend' in implies of concept 'devops'"):
        Content.model_validate(_content(concepts=concepts))


def test_duplicate_id_across_skills_and_concepts() -> None:
    concepts = [{"id": "python", "label": "Python", "implies": []}]

    with pytest.raises(ValidationError, match="duplicate skill/concept id 'python'"):
        Content.model_validate(_content(concepts=concepts))


def test_invalid_bullet_limits() -> None:
    layout = {"max_bullets_total": 4, "min_bullets_per_job": 5, "max_skill_lines": 5}

    with pytest.raises(ValidationError, match="exceeds max_bullets_total"):
        Content.model_validate(_content(layout=layout))
