from typing import Self

from pydantic import ValidationInfo, model_validator

from app.content.models import Content, ContentModel, Id


class SelectionRequest(ContentModel):
    title_id: Id
    concept_ids: list[Id] = []
    skill_ids: list[Id] = []

    @model_validator(mode="after")
    def check_against_content(self, info: ValidationInfo) -> Self:
        content = info.context.get("content") if info.context else None
        if not isinstance(content, Content):
            raise ValueError("SelectionRequest must be validated with context={'content': Content}")

        titles = {title.id for title in content.titles}
        concepts = {concept.id for concept in content.concepts}
        selectable_skills = {
            skill.id for category in content.skills if not category.pinned for skill in category.skills
        }

        if self.title_id not in titles:
            raise ValueError(f"unknown title {self.title_id!r}")
        for concept_id in self.concept_ids:
            if concept_id not in concepts:
                raise ValueError(f"unknown concept {concept_id!r}")
        for skill_id in self.skill_ids:
            if skill_id not in selectable_skills:
                raise ValueError(f"unknown or not selectable skill {skill_id!r}")
        return self


def expand_tags(content: Content, request: SelectionRequest) -> dict[str, int]:
    weights: dict[str, int] = {}

    def add(tag: str, weight: int) -> None:
        weights[tag] = max(weight, weights.get(tag, 0))

    concepts = {c.id: c for c in content.concepts}
    titles = {t.id: t for t in content.titles}

    for skill_id in request.skill_ids:
        # Set direct skill weight to 3
        add(skill_id, 3)

    for concept_id in request.concept_ids:
        # Set direct concept weight to 3
        add(concept_id, 3)

        for skill_id in concepts[concept_id].implies:
            # Set implied skill weight to 2
            add(skill_id, 2)

    title = titles[request.title_id]

    for tag in title.emphasis:
        # Set emphasised concept or skill weight to 1
        add(tag, 1)

        concept = concepts.get(tag)
        if concept is None:
            continue

        for skill_id in concept.implies:
            # Set implied skill weight for emphasised concept to 1
            add(skill_id, 1)

    return weights
