import math

from app.content.models import Content, Skill, SkillCategory
from app.content.selection.models import SkillLine
from app.content.selection.scoring import relevance

# Starting estimate; calibrate against rendered PDFs in the rendering step.
CHARS_PER_LINE = 120


def line_count(line: SkillLine) -> int:
    chars = len(f"{line.label}: ") + len(" • ".join(line.skills))
    return max(1, math.ceil(chars / CHARS_PER_LINE))


def skill_score(skill: Skill, weights: dict[str, int]) -> float:
    return relevance([skill.id], weights) + skill.priority


def category_score(category: SkillCategory, weights: dict[str, int]) -> float:
    return relevance([skill.id for skill in category.skills], weights)


def pinned_line(category: SkillCategory) -> SkillLine:
    return SkillLine(label=category.label, skills=[skill.label for skill in category.skills])


def ranked_line(category: SkillCategory, weights: dict[str, int]) -> SkillLine:
    skills = sorted(category.skills, key=lambda skill: skill_score(skill, weights), reverse=True)
    return SkillLine(label=category.label, skills=[skill.label for skill in skills])


def select_skill_lines(content: Content, weights: dict[str, int]) -> list[SkillLine]:

    lines = [pinned_line(category) for category in content.skills if category.pinned]

    candidates = sorted(
        (category for category in content.skills if not category.pinned),
        key=lambda category: category_score(category, weights),
        reverse=True,
    )

    remaining = content.layout.max_skill_lines - sum(line_count(line) for line in lines)

    for category in candidates:
        line = ranked_line(category, weights)
        if line_count(line) <= remaining:
            lines.append(line)
            remaining -= line_count(line)

    return lines
