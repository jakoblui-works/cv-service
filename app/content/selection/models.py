from typing import Self

from pydantic import model_validator

from app.content.models import ContentModel, Job, Static, Title


class SelectedBullet(ContentModel):
    bullet_id: str
    text: str  # the chosen variant's text
    highlight: str | None = None  # substring of text to emphasise

    @model_validator(mode="after")
    def check_highlight(self) -> Self:
        if self.highlight is not None and self.highlight not in self.text:
            raise ValueError(f"highlight {self.highlight!r} not found in bullet text {self.text!r}")
        return self


class SelectedJob(ContentModel):
    job: Job  # for company, roles, tagline, promotion note
    description: str  # the chosen description variant's text
    bullets: list[SelectedBullet]


class SkillLine(ContentModel):
    label: str  # category label
    skills: list[str]  # skill labels, in display order


class Selection(ContentModel):
    title: Title
    static: Static
    jobs: list[SelectedJob]  # chronological, same order as content
    skill_lines: list[SkillLine]  # display order, pinned first
