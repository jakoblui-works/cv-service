from app.content.models import Bullet, BulletVariant
from app.content.selection.highlights import select_highlights
from tests.content.builder import Builder


def _chosen(build: Builder, jobs: list[dict[str, object]]) -> dict[str, list[tuple[Bullet, BulletVariant]]]:
    content = build.content(
        skills=[build.category("programming", [build.skill("python"), build.skill("rust")])],
        jobs=jobs,
    )
    return {job.id: [(bullet, bullet.variants[0]) for bullet in job.bullets] for job in content.experience}


def _highlighted(build: Builder, id: str, tags: list[str] | None = None) -> dict[str, object]:
    variant = build.variant("Built it in Python.", highlights=[build.highlight("Python", tags=["python"])])
    return build.bullet(id, tags=tags or [], variants=[variant])


def test_highlights_total_is_capped(build: Builder) -> None:
    chosen = _chosen(build, [build.job("a", bullets=[_highlighted(build, f"a{i}") for i in range(1, 5)])])

    highlights = select_highlights(chosen, {"python": 3}, max_highlights=2)

    assert len(highlights) == 2


def test_highlights_at_most_one_per_bullet(build: Builder) -> None:
    variant = build.variant(
        "Built it in Python and Rust.",
        highlights=[build.highlight("Python", tags=["python"]), build.highlight("Rust", tags=["rust"])],
    )
    chosen = _chosen(build, [build.job("a", bullets=[build.bullet("a1", variants=[variant])])])

    highlights = select_highlights(chosen, {"python": 3, "rust": 3}, max_highlights=5)

    assert list(highlights) == [("a", "a1")]


def test_highlights_relevant_bullet_wins(build: Builder) -> None:
    chosen = _chosen(
        build, [build.job("a", bullets=[_highlighted(build, "plain"), _highlighted(build, "relevant", tags=["rust"])])]
    )

    highlights = select_highlights(chosen, {"python": 1, "rust": 3}, max_highlights=1)

    assert list(highlights) == [("a", "relevant")]


def test_highlights_matching_candidate_wins_within_bullet(build: Builder) -> None:
    variant = build.variant(
        "Built it in Python and Rust.",
        highlights=[build.highlight("Python", tags=["python"]), build.highlight("Rust", tags=["rust"])],
    )
    chosen = _chosen(build, [build.job("a", bullets=[build.bullet("a1", variants=[variant])])])

    highlights = select_highlights(chosen, {"rust": 3}, max_highlights=5)

    assert highlights == {("a", "a1"): "Rust"}


def test_highlights_only_from_chosen_variant(build: Builder) -> None:
    variants = [
        build.variant("Built it."),
        build.variant("Built it in Python.", highlights=[build.highlight("Python", tags=["python"])]),
    ]
    chosen = _chosen(build, [build.job("a", bullets=[build.bullet("a1", variants=variants)])])

    highlights = select_highlights(chosen, {"python": 3}, max_highlights=5)

    assert highlights == {}


def test_highlights_zero_max_is_empty(build: Builder) -> None:
    chosen = _chosen(build, [build.job("a", bullets=[_highlighted(build, "a1")])])

    assert select_highlights(chosen, {"python": 3}, max_highlights=0) == {}


def test_highlights_ties_prefer_earlier_job(build: Builder) -> None:
    jobs = [build.job("b", bullets=[_highlighted(build, "b1")]), build.job("a", bullets=[_highlighted(build, "a1")])]
    chosen = _chosen(build, jobs)

    highlights = select_highlights(chosen, {"python": 3}, max_highlights=1)

    assert list(highlights) == [("b", "b1")]


def test_highlights_ties_prefer_earlier_bullet(build: Builder) -> None:
    chosen = _chosen(build, [build.job("a", bullets=[_highlighted(build, "earlier"), _highlighted(build, "later")])])

    highlights = select_highlights(chosen, {"python": 3}, max_highlights=1)

    assert list(highlights) == [("a", "earlier")]
