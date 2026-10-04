import pytest

from app.content.selection import skills
from app.content.selection.models import SkillLine
from app.content.selection.skills import line_count, select_skill_lines
from tests.content.builder import Builder


def _select(
    build: Builder, categories: list[dict[str, object]], weights: dict[str, int], *, max_lines: int = 20
) -> list[SkillLine]:
    content = build.content(
        skills=categories,
        layout={"max_bullets_total": 20, "min_bullets_per_job": 1, "max_skill_lines": max_lines, "max_highlights": 5},
    )
    return select_skill_lines(content, weights)


def _labels(lines: list[SkillLine]) -> list[str]:
    return [line.label for line in lines]


def test_skills_pinned_first_and_unchanged(build: Builder) -> None:
    categories = [
        build.category("programming", [build.skill("python")]),
        build.category("languages", [build.skill("swedish"), build.skill("danish", priority=3)], pinned=True),
    ]

    lines = _select(build, categories, {"python": 3})

    assert lines[0] == SkillLine(label="Languages", skills=["Swedish", "Danish"])


def test_skills_picked_skill_moves_category_ahead(build: Builder) -> None:
    categories = [
        build.category("tools", [build.skill("git")]),
        build.category("programming", [build.skill("python")]),
    ]

    lines = _select(build, categories, {"python": 3})

    assert _labels(lines) == ["Programming", "Tools"]


def test_skills_ordered_by_relevance_within_category(build: Builder) -> None:
    categories = [build.category("programming", [build.skill("go"), build.skill("python")])]

    lines = _select(build, categories, {"python": 3})

    assert lines[0].skills == ["Python", "Go"]


def test_skills_without_picks_priority_then_yaml_order(build: Builder) -> None:
    categories = [
        build.category("programming", [build.skill("go"), build.skill("rust"), build.skill("python", priority=2)])
    ]

    lines = _select(build, categories, {})

    assert lines[0].skills == ["Python", "Go", "Rust"]


def test_skills_without_picks_keep_yaml_category_order(build: Builder) -> None:
    categories = [
        build.category("tools", [build.skill("git")]),
        build.category("programming", [build.skill("python")]),
        build.category("databases", [build.skill("postgres")]),
    ]

    lines = _select(build, categories, {})

    assert _labels(lines) == ["Tools", "Programming", "Databases"]


def test_skills_total_lines_within_budget(build: Builder, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(skills, "CHARS_PER_LINE", 20)
    categories = [
        build.category("languages", [build.skill("danish"), build.skill("english")], pinned=True),
        build.category("programming", [build.skill("python"), build.skill("rust"), build.skill("go")]),
        build.category("tools", [build.skill("git"), build.skill("docker")]),
        build.category("databases", [build.skill("postgres")]),
    ]

    lines = _select(build, categories, {"python": 3}, max_lines=3)

    assert sum(line_count(line) for line in lines) <= 3
    assert lines[0].label == "Languages"


def test_skills_skip_category_that_does_not_fit(build: Builder, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(skills, "CHARS_PER_LINE", 20)
    categories = [
        build.category("languages", [build.skill("danish")], pinned=True),
        build.category("long", [build.skill("alpha"), build.skill("bravo"), build.skill("charlie")]),
        build.category("tools", [build.skill("git")]),
    ]

    lines = _select(build, categories, {"alpha": 3}, max_lines=2)

    assert _labels(lines) == ["Languages", "Tools"]


def test_line_count_short_line_is_one() -> None:
    assert line_count(SkillLine(label="Programming", skills=["Python"])) == 1


def test_line_count_long_line_wraps() -> None:
    line = SkillLine(label="Programming", skills=["x" * skills.CHARS_PER_LINE])

    assert line_count(line) >= 2
