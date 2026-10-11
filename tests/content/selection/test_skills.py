import pytest
from hypothesis import given
from hypothesis import strategies as st

from app.content.selection import skills
from app.content.selection.models import SkillLine
from app.content.selection.skills import line_count, ranked_line, select_skill_lines
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


def test_skills_pinned_first_and_ranked(build: Builder) -> None:
    categories = [
        build.category("programming", [build.skill("python", priority=1)]),
        build.category(
            "languages", [build.skill("swedish", priority=1), build.skill("danish", priority=3)], pinned=True
        ),
    ]

    lines = _select(build, categories, {"python": 3})

    assert lines[0] == SkillLine(label="Languages", skills=["Danish", "Swedish"])


def test_skills_pinned_on_top_even_when_less_relevant(build: Builder) -> None:
    categories = [
        build.category("programming", [build.skill("python", priority=1)]),
        build.category("languages", [build.skill("danish", priority=1)], pinned=True),
    ]

    lines = _select(build, categories, {"python": 3})

    assert _labels(lines) == ["Languages", "Programming"]


def test_skills_always_shown_ordered_by_relevance(build: Builder) -> None:
    categories = [
        build.category("frontend", [build.skill("react", priority=1)], always_shown=True),
        build.category("programming", [build.skill("python", priority=1)]),
    ]

    lines = _select(build, categories, {"python": 3})

    assert _labels(lines) == ["Programming", "Frontend"]


def test_skills_always_shown_gets_room_before_more_relevant(build: Builder) -> None:
    categories = [
        build.category("programming", [build.skill("python", priority=1)]),
        build.category("frontend", [build.skill("react", priority=1)], always_shown=True),
    ]

    lines = _select(build, categories, {"python": 3}, max_lines=1)

    assert _labels(lines) == ["Frontend"]


def test_skills_picked_skill_moves_category_ahead(build: Builder) -> None:
    categories = [
        build.category("tools", [build.skill("git", priority=1)]),
        build.category("programming", [build.skill("python", priority=1)]),
    ]

    lines = _select(build, categories, {"python": 3})

    assert _labels(lines) == ["Programming", "Tools"]


def test_skills_ordered_by_relevance_within_category(build: Builder) -> None:
    categories = [build.category("programming", [build.skill("go", priority=1), build.skill("python", priority=1)])]

    lines = _select(build, categories, {"python": 3})

    assert lines[0].skills == ["Python", "Go"]


def test_skills_without_picks_priority_then_yaml_order(build: Builder) -> None:
    categories = [
        build.category(
            "programming",
            [build.skill("go", priority=1), build.skill("rust", priority=1), build.skill("python", priority=2)],
        )
    ]

    lines = _select(build, categories, {})

    assert lines[0].skills == ["Python", "Go", "Rust"]


def test_skills_without_picks_keep_yaml_category_order(build: Builder) -> None:
    categories = [
        build.category("tools", [build.skill("git", priority=1)]),
        build.category("programming", [build.skill("python", priority=1)]),
        build.category("databases", [build.skill("postgres", priority=1)]),
    ]

    lines = _select(build, categories, {})

    assert _labels(lines) == ["Tools", "Programming", "Databases"]


def test_skills_without_priority_hidden_unless_relevant(build: Builder) -> None:
    categories = [build.category("frontend", [build.skill("react", priority=1), build.skill("swr")])]

    assert _select(build, categories, {})[0].skills == ["React"]
    assert "Swr" in _select(build, categories, {"swr": 1})[0].skills


def test_skills_category_with_nothing_shown_is_skipped(build: Builder) -> None:
    categories = [
        build.category("niche", [build.skill("cobol")], pinned=True),
        build.category("programming", [build.skill("python", priority=1)]),
    ]

    lines = _select(build, categories, {})

    assert _labels(lines) == ["Programming"]


def test_skills_total_lines_within_budget(build: Builder, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(skills, "CHARS_PER_LINE", 20)
    categories = [
        build.category(
            "languages", [build.skill("danish", priority=1), build.skill("english", priority=1)], pinned=True
        ),
        build.category(
            "programming", [build.skill("python"), build.skill("rust", priority=1), build.skill("go", priority=1)]
        ),
        build.category("tools", [build.skill("git", priority=1), build.skill("docker", priority=1)]),
        build.category("databases", [build.skill("postgres", priority=1)]),
    ]

    lines = _select(build, categories, {"python": 3}, max_lines=3)

    assert sum(line_count(line) for line in lines) <= 3
    assert lines[0].label == "Languages"


def test_skills_category_that_does_not_fit_is_trimmed_to_its_most_relevant(
    build: Builder, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(skills, "CHARS_PER_LINE", 20)
    long = [build.skill("alpha", priority=1), build.skill("bravo", priority=1), build.skill("charlie", priority=1)]
    categories = [
        build.category("languages", [build.skill("danish", priority=1)], pinned=True),
        build.category("long", long),
    ]

    lines = _select(build, categories, {"charlie": 3}, max_lines=2)

    assert _labels(lines) == ["Languages", "Long"]
    assert line_count(lines[1]) == 1
    assert 0 < len(lines[1].skills) < len(long)
    assert lines[1].skills[0] == "Charlie"


_SKILL_IDS = ["python", "rust", "go", "git", "docker", "postgres", "redis", "react"]


@given(
    weights=st.dictionaries(st.sampled_from(_SKILL_IDS), st.integers(min_value=1, max_value=3)),
    priorities=st.lists(st.integers(min_value=0, max_value=3), min_size=len(_SKILL_IDS), max_size=len(_SKILL_IDS)),
    max_lines=st.integers(min_value=1, max_value=6),
    chars_per_line=st.integers(min_value=15, max_value=60),
)
def test_skills_lines_fit_budget_and_keep_top_ranked_skills(
    weights: dict[str, int], priorities: list[int], max_lines: int, chars_per_line: int
) -> None:
    build = Builder()
    skill_data = [build.skill(id_, priority=p) for id_, p in zip(_SKILL_IDS, priorities, strict=True)]
    content = build.content(
        skills=[
            build.category("languages", skill_data[:2], pinned=True),
            build.category("tools", skill_data[2:5], always_shown=True),
            build.category("data", skill_data[5:]),
        ],
        layout={"max_bullets_total": 20, "min_bullets_per_job": 1, "max_skill_lines": max_lines, "max_highlights": 5},
    )

    with pytest.MonkeyPatch.context() as monkeypatch:
        monkeypatch.setattr(skills, "CHARS_PER_LINE", chars_per_line)
        lines = select_skill_lines(content, weights)

    assert sum(line_count(line) for line in lines) <= max_lines
    full = {category.label: ranked_line(category, weights).skills for category in content.skills}
    for line in lines:
        assert line.skills
        assert line.skills == full[line.label][: len(line.skills)]


def test_line_count_short_line_is_one() -> None:
    assert line_count(SkillLine(label="Programming", skills=["Python"])) == 1


def test_line_count_long_line_wraps() -> None:
    line = SkillLine(label="Programming", skills=["x" * skills.CHARS_PER_LINE])

    assert line_count(line) >= 2
