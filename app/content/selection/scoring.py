from collections.abc import Iterable

from app.content.models import Bullet

EXTRA_MATCH_BONUS = 0.1


def relevance(tags: Iterable[str], weights: dict[str, int]) -> float:
    tag_weights = sorted((weights[t] for t in tags if t in weights), reverse=True)

    if not tag_weights:
        return 0.0

    best_weight = tag_weights.pop(0)

    score = best_weight + sum(tag_weights) * EXTRA_MATCH_BONUS

    return score


def bullet_score(bullet: Bullet, weights: dict[str, int]) -> float:
    return relevance(bullet.tags, weights) + bullet.priority
