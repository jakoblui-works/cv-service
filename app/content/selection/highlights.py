from app.content.models import Bullet, BulletVariant, Highlight
from app.content.selection.scoring import bullet_score, relevance


def highlight_score(bullet: Bullet, highlight: Highlight, weights: dict[str, int]) -> float:
    return bullet_score(bullet, weights) + relevance(highlight.tags, weights) + highlight.priority


def best_highlight(bullet: Bullet, variant: BulletVariant, weights: dict[str, int]) -> Highlight | None:
    if not variant.highlights:
        return None
    return max(variant.highlights, key=lambda highlight: highlight_score(bullet, highlight, weights))


def select_highlights(
    chosen: dict[str, list[tuple[Bullet, BulletVariant]]],
    weights: dict[str, int],
    max_highlights: int,
) -> dict[tuple[str, str], str]:

    candidates = [
        ((job_id, bullet.id), highlight, highlight_score(bullet, highlight, weights))
        for job_id, pairs in chosen.items()
        for bullet, variant in pairs
        if (highlight := best_highlight(bullet, variant, weights)) is not None
    ]

    ranked = sorted(candidates, key=lambda candidate: candidate[2], reverse=True)

    return {key: highlight.text for key, highlight, _ in ranked[:max_highlights]}
