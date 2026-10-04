import pytest
from hypothesis import given
from hypothesis import strategies as st

from app.content.models import Bullet, Content, Job
from app.content.selection.bullets import choose_description, choose_variant
from app.content.selection.scoring import bullet_score, relevance
from tests.content.builder import Builder


def test_relevance_no_match_is_zero() -> None:
    assert relevance(["x"], {"a": 3}) == 0
    assert relevance([], {"a": 3}) == 0


def test_relevance_any_match_is_positive() -> None:
    assert relevance(["a"], {"a": 1}) > 0


def test_relevance_higher_weight_ranks_higher() -> None:
    weights = {"a": 3, "b": 2, "c": 1}

    assert relevance(["a"], weights) > relevance(["b"], weights) > relevance(["c"], weights)


def test_relevance_extra_match_never_lowers() -> None:
    weights = {"a": 3, "b": 2}

    assert relevance(["a", "b"], weights) >= relevance(["a"], weights)
    assert relevance(["a", "x"], weights) == relevance(["a"], weights)


def test_relevance_strong_extra_match_beats_weak_one() -> None:
    weights = {"a": 3, "b": 2, "c": 1}

    assert relevance(["a", "b"], weights) > relevance(["a", "c"], weights)


def test_relevance_best_match_dominates() -> None:
    weights = {"a": 3, "b": 2, "c": 1}

    assert relevance(["a"], weights) > relevance(["b", "c"], weights)


def test_relevance_order_does_not_matter() -> None:
    weights = {"a": 3, "b": 2, "c": 1}

    assert relevance(["c", "b", "a"], weights) == relevance(["a", "b", "c"], weights)


KNOWN = ["a", "b", "c", "d", "e"]
UNKNOWN = ["x", "y", "z"]

weights_st = st.dictionaries(st.sampled_from(KNOWN), st.integers(min_value=1, max_value=3))
tags_st = st.lists(st.sampled_from(KNOWN + UNKNOWN))


@given(tags=tags_st, weights=weights_st)
def test_relevance_property_order_does_not_matter(tags: list[str], weights: dict[str, int]) -> None:
    assert relevance(tags, weights) == pytest.approx(relevance(list(reversed(tags)), weights))
    assert relevance(tags, weights) == pytest.approx(relevance(sorted(tags), weights))


@given(tags=tags_st, weights=weights_st, extra=st.sampled_from(KNOWN + UNKNOWN))
def test_relevance_property_extra_tag_never_lowers(tags: list[str], weights: dict[str, int], extra: str) -> None:
    assert relevance([*tags, extra], weights) >= relevance(tags, weights)


@given(tags=st.lists(st.sampled_from(UNKNOWN)), weights=weights_st)
def test_relevance_property_no_match_is_zero(tags: list[str], weights: dict[str, int]) -> None:
    assert relevance(tags, weights) == 0


@given(tags=tags_st, weights=weights_st)
def test_relevance_property_any_match_is_positive(tags: list[str], weights: dict[str, int]) -> None:
    if any(tag in weights for tag in tags):
        assert relevance(tags, weights) > 0


def _scoring_content(
    build: Builder, *, bullets: list[dict[str, object]], descriptions: list[dict[str, object]] | None = None
) -> Content:
    return build.content(
        skills=[build.category("programming", [build.skill("python"), build.skill("rust")])],
        concepts=[build.concept("product"), build.concept("devops")],
        jobs=[build.job("acme", bullets=bullets, descriptions=descriptions)],
    )


def _bullets(build: Builder, *bullets: dict[str, object]) -> list[Bullet]:
    return list(_scoring_content(build, bullets=list(bullets)).experience[0].bullets)


def _job(build: Builder, descriptions: list[dict[str, object]]) -> Job:
    return _scoring_content(build, bullets=[build.bullet("built-a-thing")], descriptions=descriptions).experience[0]


def test_bullet_score_relevance_raises_score(build: Builder) -> None:
    matching, other = _bullets(build, build.bullet("matching", tags=["python"]), build.bullet("other", tags=["rust"]))

    assert bullet_score(matching, {"python": 3}) > bullet_score(other, {"python": 3})


def test_bullet_score_priority_raises_score(build: Builder) -> None:
    strong, weak = _bullets(
        build, build.bullet("strong", tags=["python"], priority=3), build.bullet("weak", tags=["python"], priority=1)
    )

    assert bullet_score(strong, {}) > bullet_score(weak, {})


def test_choose_variant_uses_matching_angle(build: Builder) -> None:
    (bullet,) = _bullets(
        build,
        build.bullet(
            "rbac",
            variants=[build.variant("Default phrasing."), build.variant("Product phrasing.", tags=["product"])],
        ),
    )

    assert choose_variant(bullet, {"product": 3}).text == "Product phrasing."


def test_choose_variant_defaults_to_first_without_match(build: Builder) -> None:
    (bullet,) = _bullets(
        build,
        build.bullet(
            "rbac",
            variants=[build.variant("Default phrasing."), build.variant("Product phrasing.", tags=["product"])],
        ),
    )

    assert choose_variant(bullet, {}).text == "Default phrasing."


def test_choose_description_follows_angle(build: Builder) -> None:
    job = _job(
        build,
        descriptions=[{"text": "Default description.", "tags": []}, {"text": "Ops description.", "tags": ["devops"]}],
    )

    assert choose_description(job, {"devops": 3}).text == "Ops description."
