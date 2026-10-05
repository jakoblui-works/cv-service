from app.content.models import Content
from app.content.selection.bullets import choose_description, choose_variant, select_bullets
from app.content.selection.highlights import select_highlights
from app.content.selection.models import SelectedBullet, SelectedJob, Selection
from app.content.selection.request import SelectionRequest, expand_tags
from app.content.selection.skills import select_skill_lines


def select(content: Content, request: SelectionRequest) -> Selection:
    weights = expand_tags(content, request)
    chosen = select_bullets(content, weights)

    pairs = {
        job_id: [(bullet, choose_variant(bullet, weights)) for bullet in bullets] for job_id, bullets in chosen.items()
    }

    highlights = select_highlights(pairs, weights, content.layout.max_highlights)

    jobs = [
        SelectedJob(
            job=job,
            description=choose_description(job, weights).text,
            bullets=[
                SelectedBullet(bullet_id=bullet.id, text=variant.text, highlight=highlights.get((job.id, bullet.id)))
                for bullet, variant in pairs[job.id]
            ],
        )
        for job in content.experience
    ]

    skill_lines = select_skill_lines(content, weights)

    title = next(t for t in content.titles if t.id == request.title_id)

    return Selection(title=title, static=content.static, jobs=jobs, skill_lines=skill_lines)
