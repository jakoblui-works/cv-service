from app.content.models import Bullet, BulletVariant, Content, DescriptionVariant, Job
from app.content.selection.scoring import bullet_score, relevance


def choose_variant(bullet: Bullet, weights: dict[str, int]) -> BulletVariant:
    return max(bullet.variants, key=lambda variant: relevance(variant.tags, weights))


def choose_description(job: Job, weights: dict[str, int]) -> DescriptionVariant:
    return max(job.descriptions, key=lambda description: relevance(description.tags, weights))


def select_bullets(content: Content, weights: dict[str, int]) -> dict[str, list[Bullet]]:

    ranked_bullets = {
        job.id: sorted(job.bullets, key=lambda b: bullet_score(b, weights), reverse=True) for job in content.experience
    }

    selected_bullets = {
        job_id: bullets[: content.layout.min_bullets_per_job] for job_id, bullets in ranked_bullets.items()
    }

    leftovers = sorted(
        [
            (job.id, bullet)
            for job in content.experience
            for bullet in ranked_bullets[job.id][content.layout.min_bullets_per_job :]
        ],
        key=lambda tup: bullet_score(tup[1], weights),
        reverse=True,
    )

    free_slots = content.layout.max_bullets_total - sum(len(bullets) for bullets in selected_bullets.values())

    for job_id, bullet in leftovers[:free_slots]:
        selected_bullets[job_id].append(bullet)

    return selected_bullets
