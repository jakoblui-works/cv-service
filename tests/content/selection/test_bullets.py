from app.content.selection.bullets import select_bullets
from tests.content.builder import Builder


def _select(
    build: Builder,
    jobs: list[dict[str, object]],
    *,
    min_per_job: int,
    max_total: int,
    weights: dict[str, int],
) -> dict[str, list[str]]:
    content = build.content(
        skills=[build.category("programming", [build.skill("python"), build.skill("rust")])],
        jobs=jobs,
        layout={
            "max_bullets_total": max_total,
            "min_bullets_per_job": min_per_job,
            "max_skill_lines": 20,
            "max_highlights": 5,
        },
    )
    selected = select_bullets(content, weights)
    return {job_id: [bullet.id for bullet in bullets] for job_id, bullets in selected.items()}


def test_select_every_job_gets_its_floor(build: Builder) -> None:
    jobs = [
        build.job("a", bullets=[build.bullet("a1", tags=["python"]), build.bullet("a2", tags=["python"])]),
        build.job("b", bullets=[build.bullet("b1")]),
    ]

    selected = _select(build, jobs, min_per_job=1, max_total=3, weights={"python": 3})

    assert selected["b"] == ["b1"]


def test_select_total_is_capped(build: Builder) -> None:
    jobs = [build.job("a", bullets=[build.bullet(f"a{i}") for i in range(1, 7)])]

    selected = _select(build, jobs, min_per_job=1, max_total=3, weights={})

    assert sum(len(ids) for ids in selected.values()) == 3


def test_select_best_bullets_fill_free_slots(build: Builder) -> None:
    jobs = [
        build.job("a", bullets=[build.bullet("a1", tags=["python"]), build.bullet("a2")]),
        build.job("b", bullets=[build.bullet("b1", tags=["python"]), build.bullet("b2", tags=["python"])]),
    ]

    selected = _select(build, jobs, min_per_job=1, max_total=3, weights={"python": 3})

    assert selected == {"a": ["a1"], "b": ["b1", "b2"]}


def test_select_short_job_gets_all_its_bullets(build: Builder) -> None:
    jobs = [
        build.job("a", bullets=[build.bullet("a1")]),
        build.job("b", bullets=[build.bullet("b1"), build.bullet("b2"), build.bullet("b3")]),
    ]

    selected = _select(build, jobs, min_per_job=2, max_total=4, weights={})

    assert selected["a"] == ["a1"]
    assert len(selected["b"]) == 3


def test_select_orders_by_score_within_job(build: Builder) -> None:
    jobs = [
        build.job(
            "a",
            bullets=[build.bullet("low"), build.bullet("mid", tags=["rust"]), build.bullet("high", tags=["python"])],
        )
    ]

    selected = _select(build, jobs, min_per_job=1, max_total=3, weights={"python": 3, "rust": 1})

    assert selected["a"] == ["high", "mid", "low"]


def test_select_ties_keep_authored_order(build: Builder) -> None:
    jobs = [build.job("a", bullets=[build.bullet("first"), build.bullet("second"), build.bullet("third")])]

    selected = _select(build, jobs, min_per_job=1, max_total=3, weights={})

    assert selected["a"] == ["first", "second", "third"]


def test_select_priority_decides_without_picks(build: Builder) -> None:
    jobs = [build.job("a", bullets=[build.bullet("weak", priority=1), build.bullet("strong", priority=3)])]

    selected = _select(build, jobs, min_per_job=1, max_total=2, weights={})

    assert selected["a"] == ["strong", "weak"]
