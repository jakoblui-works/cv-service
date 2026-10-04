from collections.abc import Iterable
from datetime import date
from typing import Annotated, Self

from pydantic import BaseModel, ConfigDict, Field, model_validator

Id = Annotated[str, Field(pattern=r"^[a-z0-9]+(-[a-z0-9]+)*$")]


class ContentModel(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


class Link(ContentModel):
    text: str  # substring of the surrounding text to turn into a hyperlink
    url: str


class Project(ContentModel):
    name: str
    discipline: str
    kind: str
    location: str
    start_year: int
    end_year: int | None = None
    description: str
    links: list[Link] = []

    @model_validator(mode="after")
    def check_links(self) -> Self:
        for link in self.links:
            if link.text not in self.description:
                raise ValueError(f"link text {link.text!r} not found in description of project {self.name!r}")
        return self


class Education(ContentModel):
    institution: str
    department: str
    degree: str
    location: str
    start_year: int
    end_year: int | None = None
    description: str


class Static(ContentModel):
    name: str
    city: str
    projects: list[Project]
    education: list[Education]


class Skill(ContentModel):
    id: Id
    label: str
    priority: int = Field(default=0, ge=0)


class SkillCategory(ContentModel):
    id: Id
    label: str
    pinned: bool = False
    skills: list[Skill] = Field(min_length=1)


class Concept(ContentModel):
    id: Id
    label: str
    implies: list[Id] = []


class Title(ContentModel):
    id: Id
    label: str
    profile: str
    emphasis: list[Id] = []


class Role(ContentModel):
    title: str
    start: date
    end: date | None = None

    @model_validator(mode="after")
    def check_dates(self) -> Self:
        for d in (self.start, self.end):
            if d is not None and d.day != 1:
                raise ValueError(f"role {self.title!r}: date {d} must be on the 1st of the month")
        if self.end is not None and self.end < self.start:
            raise ValueError(f"role {self.title!r}: end {self.end} is before start {self.start}")
        return self


class Highlight(ContentModel):
    text: str  # substring of the variant text to emphasise
    tags: list[Id] = Field(min_length=1)
    priority: int = Field(default=0, ge=0)


class BulletVariant(ContentModel):
    text: str
    tags: list[Id] = []
    highlights: list[Highlight] = []

    @model_validator(mode="after")
    def check_highlights(self) -> Self:
        for highlight in self.highlights:
            if highlight.text not in self.text:
                raise ValueError(f"highlight {highlight.text!r} not found in bullet text {self.text!r}")
        return self


class Bullet(ContentModel):
    id: Id
    priority: int = Field(default=0, ge=0)
    tags: list[Id] = []  # what the achievement demonstrates; variant tags are only the phrasing's angle
    variants: list[BulletVariant] = Field(min_length=1)  # first = default phrasing


class DescriptionVariant(ContentModel):
    text: str
    tags: list[Id] = []


class Job(ContentModel):
    id: Id
    company: str
    employment: str
    location: str
    tagline: str | None = None
    descriptions: list[DescriptionVariant] = Field(min_length=1)  # first = default
    promotion_note: str | None = None
    roles: list[Role] = Field(min_length=1)
    bullets: list[Bullet]


class Layout(ContentModel):
    max_bullets_total: int = Field(ge=1)
    min_bullets_per_job: int = Field(ge=1)
    max_skill_lines: int = Field(ge=1)
    max_highlights: int = Field(ge=0)


def _check_unique(ids: Iterable[str], kind: str) -> set[str]:
    seen: set[str] = set()
    for id_ in ids:
        if id_ in seen:
            raise ValueError(f"duplicate {kind} id {id_!r}")
        seen.add(id_)
    return seen


def _check_refs(refs: Iterable[str], known: set[str], where: str) -> None:
    for ref in refs:
        if ref not in known:
            raise ValueError(f"unknown id {ref!r} in {where}")


def _check_layout(layout: Layout, jobs: list[Job]) -> None:
    if layout.min_bullets_per_job * len(jobs) > layout.max_bullets_total:
        raise ValueError(
            f"min_bullets_per_job={layout.min_bullets_per_job} × {len(jobs)} jobs "
            f"exceeds max_bullets_total={layout.max_bullets_total}"
        )


class Content(ContentModel):
    static: Static
    skills: list[SkillCategory]
    concepts: list[Concept]
    titles: list[Title]
    experience: list[Job]
    layout: Layout

    @model_validator(mode="after")
    def check_layout(self) -> Self:
        _check_layout(self.layout, self.experience)

        return self

    @model_validator(mode="after")
    def check_ids(self) -> Self:
        skill_ids = [skill.id for category in self.skills for skill in category.skills]
        # Skills and concepts share one tag namespace.
        tag_ids = _check_unique([*skill_ids, *(concept.id for concept in self.concepts)], "skill/concept")
        _check_unique((category.id for category in self.skills), "skill category")
        _check_unique((job.id for job in self.experience), "job")
        _check_unique((title.id for title in self.titles), "title")

        for concept in self.concepts:
            _check_refs(concept.implies, set(skill_ids), f"implies of concept {concept.id!r} (must be a skill)")
        for title in self.titles:
            _check_refs(title.emphasis, tag_ids, f"emphasis of title {title.id!r}")
        for job in self.experience:
            _check_unique((bullet.id for bullet in job.bullets), f"bullet (job {job.id!r})")
            for i, description in enumerate(job.descriptions):
                _check_refs(description.tags, tag_ids, f"tags of description {i} in job {job.id!r}")
            for bullet in job.bullets:
                _check_refs(bullet.tags, tag_ids, f"tags of bullet {bullet.id!r} in job {job.id!r}")
                for i, variant in enumerate(bullet.variants):
                    where = f"variant {i} of bullet {bullet.id!r} in job {job.id!r}"
                    _check_refs(variant.tags, tag_ids, f"tags of {where}")
                    for highlight in variant.highlights:
                        _check_refs(highlight.tags, tag_ids, f"tags of highlight {highlight.text!r} in {where}")

        return self
