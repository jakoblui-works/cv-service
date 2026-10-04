import pytest
from pydantic import ValidationError

from app.content.loader import load_content
from app.content.models import Content


def _job(**overrides: object) -> dict[str, object]:
    job: dict[str, object] = {
        "id": "acme",
        "company": "Acme",
        "employment": "Full Time",
        "location": "Testville",
        "descriptions": [{"text": "Made things.", "tags": ["backend"]}],
        "roles": [{"title": "Developer", "start": "2020-01-01"}],
        "bullets": [
            {
                "id": "built-a-thing",
                "tags": ["python", "backend"],
                "variants": [
                    {"text": "Built a thing 2× faster.", "highlights": [{"text": "2× faster", "tags": ["backend"]}]},
                    {"text": "Built a backend thing 2× faster.", "tags": ["backend"]},
                ],
            }
        ],
    }
    return job | overrides


def _bullet(**variant: object) -> list[dict[str, object]]:
    return [{"id": "built-a-thing", "variants": [{"text": "Built a thing 2× faster."} | variant]}]


def _content(**overrides: object) -> dict[str, object]:
    data: dict[str, object] = {
        "static": {"name": "Test Person", "city": "Testville", "projects": [], "education": []},
        "skills": [{"id": "programming", "label": "Programming", "skills": [{"id": "python", "label": "Python"}]}],
        "concepts": [{"id": "backend", "label": "Backend", "implies": ["python"]}],
        "titles": [{"id": "engineer", "label": "Engineer", "profile": "Writes code.", "emphasis": ["backend"]}],
        "experience": [_job()],
        "layout": {"max_bullets_total": 10, "min_bullets_per_job": 1, "max_skill_lines": 5, "max_highlights": 3},
    }
    return data | overrides


def test_real_content_loads() -> None:
    content = load_content()

    assert content.skills[0].pinned
    assert [job.id for job in content.experience] == ["acembee", "confect", "confect-ml"]


def test_minimal_content_is_valid() -> None:
    Content.model_validate(_content())


def test_unknown_variant_tag() -> None:
    experience = [_job(bullets=_bullet(tags=["cobol"]))]

    with pytest.raises(
        ValidationError, match="unknown id 'cobol' in tags of variant 0 of bullet 'built-a-thing' in job 'acme'"
    ):
        Content.model_validate(_content(experience=experience))


def test_unknown_bullet_level_tag() -> None:
    experience = [_job(bullets=[{"id": "built-a-thing", "tags": ["cobol"], "variants": [{"text": "Built a thing."}]}])]

    with pytest.raises(ValidationError, match="unknown id 'cobol' in tags of bullet 'built-a-thing' in job 'acme'"):
        Content.model_validate(_content(experience=experience))


def test_duplicate_bullet_id_within_job() -> None:
    experience = [_job(bullets=_bullet() + _bullet())]

    with pytest.raises(ValidationError, match="duplicate bullet \\(job 'acme'\\) id 'built-a-thing'"):
        Content.model_validate(_content(experience=experience))


def test_same_bullet_id_in_different_jobs() -> None:
    experience = [_job(), _job(id="globex")]

    Content.model_validate(_content(experience=experience))


def test_unknown_description_tag() -> None:
    experience = [_job(descriptions=[{"text": "Made things."}, {"text": "Made things.", "tags": ["cobol"]}])]

    with pytest.raises(ValidationError, match="unknown id 'cobol' in tags of description 1 in job 'acme'"):
        Content.model_validate(_content(experience=experience))


def test_unknown_highlight_tag() -> None:
    experience = [_job(bullets=_bullet(highlights=[{"text": "2× faster", "tags": ["cobol"]}]))]

    with pytest.raises(
        ValidationError,
        match="unknown id 'cobol' in tags of highlight '2× faster' in variant 0 of bullet 'built-a-thing'",
    ):
        Content.model_validate(_content(experience=experience))


def test_highlight_not_in_variant_text() -> None:
    experience = [_job(bullets=_bullet(highlights=[{"text": "3× faster", "tags": ["backend"]}]))]

    with pytest.raises(ValidationError, match="highlight '3× faster' not found in bullet text"):
        Content.model_validate(_content(experience=experience))


def test_highlight_without_tags() -> None:
    experience = [_job(bullets=_bullet(highlights=[{"text": "2× faster", "tags": []}]))]

    with pytest.raises(ValidationError, match="tags\\s+List should have at least 1 item"):
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
    layout = {"max_bullets_total": 4, "min_bullets_per_job": 5, "max_skill_lines": 5, "max_highlights": 0}

    with pytest.raises(ValidationError, match="exceeds max_bullets_total"):
        Content.model_validate(_content(layout=layout))
