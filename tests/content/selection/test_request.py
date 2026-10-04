import pytest
from pydantic import ValidationError

from app.content.models import Content
from app.content.selection.request import SelectionRequest, expand_tags
from tests.content.builder import Builder


def _content(build: Builder) -> Content:
    return build.content(
        skills=[
            build.category("languages", [build.skill("danish")], pinned=True),
            build.category("programming", [build.skill("python")]),
        ],
        concepts=[build.concept("backend", implies=["python"])],
        titles=[build.title("engineer")],
    )


def _request(content: Content, **data: object) -> SelectionRequest:
    return SelectionRequest.model_validate(data, context={"content": content})


def _content_with_emphasis(build: Builder) -> Content:
    return build.content(
        skills=[build.category("programming", [build.skill("python"), build.skill("rust")])],
        concepts=[build.concept("backend", implies=["python"])],
        titles=[build.title("lead", emphasis=["backend"])],
    )


def test_valid_request_passes(build: Builder) -> None:
    content = _content(build)

    request = _request(content, title_id="engineer", concept_ids=["backend"], skill_ids=["python"])

    assert request.title_id == "engineer"


def test_invalid_request_unknown_title(build: Builder) -> None:
    content = _content(build)

    with pytest.raises(ValidationError, match="unknown title"):
        _request(content, title_id="designer", concept_ids=["backend"], skill_ids=["python"])


def test_invalid_request_unknown_concept(build: Builder) -> None:
    content = _content(build)

    with pytest.raises(ValidationError, match="unknown concept"):
        _request(content, title_id="engineer", concept_ids=["frontend"])


def test_invalid_request_unknown_skill(build: Builder) -> None:
    content = _content(build)

    with pytest.raises(ValidationError, match="not selectable skill"):
        _request(content, title_id="engineer", skill_ids=["rust"])


def test_invalid_request_pinned_skill(build: Builder) -> None:
    content = _content(build)

    with pytest.raises(ValidationError, match="not selectable skill"):
        _request(content, title_id="engineer", skill_ids=["danish"])


def test_invalid_request_malformed_id(build: Builder) -> None:
    content = _content(build)

    with pytest.raises(ValidationError):
        _request(content, title_id="Not An Id")


def test_request_requires_content_context() -> None:
    with pytest.raises(ValidationError, match="must be validated with context"):
        SelectionRequest(title_id="engineer")


def test_expand_direct_skill(build: Builder) -> None:
    content = _content(build)

    weights = expand_tags(content, _request(content, title_id="engineer", skill_ids=["python"]))

    assert weights["python"] == 3


def test_expand_concept_and_implied_skill(build: Builder) -> None:
    content = _content(build)

    weights = expand_tags(content, _request(content, title_id="engineer", concept_ids=["backend"]))

    assert weights["backend"] == 3
    assert weights["python"] == 2


def test_expand_highest_route_wins(build: Builder) -> None:
    content = _content(build)

    weights = expand_tags(
        content, _request(content, title_id="engineer", concept_ids=["backend"], skill_ids=["python"])
    )

    assert weights["python"] == 3


def test_expand_title_emphasis(build: Builder) -> None:
    content = _content_with_emphasis(build)

    weights = expand_tags(content, _request(content, title_id="lead"))

    assert weights == {"backend": 1, "python": 1}


def test_expand_emphasis_does_not_lower_picked(build: Builder) -> None:
    content = _content_with_emphasis(build)

    weights = expand_tags(content, _request(content, title_id="lead", skill_ids=["python"]))

    assert weights["python"] == 3


def test_expand_unreached_tags_absent(build: Builder) -> None:
    content = _content_with_emphasis(build)

    weights = expand_tags(content, _request(content, title_id="lead"))

    assert "rust" not in weights
