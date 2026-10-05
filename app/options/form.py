from app.content.models import Content, ContentModel

# Shape version of the published form options. A shape change is a new version (a new row), never an edit of this one.
VERSION = 1


class Option(ContentModel):
    id: str
    label: str


class SkillGroup(ContentModel):
    id: str
    label: str
    skills: list[Option]


class FormOptions(ContentModel):
    titles: list[Option]
    concepts: list[Option]
    skill_groups: list[SkillGroup]  # non-pinned skill categories, in display order


def build_form_options(content: Content) -> FormOptions:
    titles = [Option(id=t.id, label=t.label) for t in content.titles]
    concepts = [Option(id=c.id, label=c.label) for c in content.concepts]
    skill_groups = [
        SkillGroup(
            id=category.id,
            label=category.label,
            skills=[Option(id=s.id, label=s.label) for s in category.skills],
        )
        for category in content.skills
        if not category.pinned
    ]

    return FormOptions(titles=titles, concepts=concepts, skill_groups=skill_groups)
