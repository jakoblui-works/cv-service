import math

from app.content.models import Content, Skill, SkillCategory
from app.content.selection.models import SkillLine
from app.content.selection.scoring import relevance

# Calibrated against rendered PDFs (ragged-right, no hyphenation; 2026-10-11): the longest line that stayed on one
# line was 116 chars, the shortest that wrapped 120.
CHARS_PER_LINE = 116


def line_count(line: SkillLine) -> int:
    chars = len(f"{line.label}: ") + len(" • ".join(line.skills))
    return max(1, math.ceil(chars / CHARS_PER_LINE))


def skill_score(skill: Skill, weights: dict[str, int]) -> float:
    return relevance([skill.id], weights) + skill.priority


def category_score(category: SkillCategory, weights: dict[str, int]) -> float:
    return relevance([skill.id for skill in category.skills], weights)


def is_shown(skill: Skill, weights: dict[str, int]) -> bool:
    # Priority 0 means "only when asked for": such a skill shows only when the request makes it relevant.
    return skill.priority > 0 or relevance([skill.id], weights) > 0


def ranked_line(category: SkillCategory, weights: dict[str, int]) -> SkillLine:
    shown = (skill for skill in category.skills if is_shown(skill, weights))
    skills = sorted(shown, key=lambda skill: skill_score(skill, weights), reverse=True)
    return SkillLine(label=category.label, skills=[skill.label for skill in skills])


def fitted_line(line: SkillLine, remaining: int) -> SkillLine | None:
    # Drops the least relevant skills (ranked last) until the line fits; None if nothing is left.
    skills = list(line.skills)
    while skills and line_count(SkillLine(label=line.label, skills=skills)) > remaining:
        skills.pop()
    return SkillLine(label=line.label, skills=skills) if skills else None


def select_skill_lines(content: Content, weights: dict[str, int]) -> list[SkillLine]:
    pinned = [category for category in content.skills if category.pinned]
    candidates = sorted(
        (category for category in content.skills if not category.pinned),
        key=lambda category: category_score(category, weights),
        reverse=True,
    )

    lines: list[SkillLine] = []
    remaining = content.layout.max_skill_lines

    # Pinned categories come first, so they always get room; every line is filtered, ranked and trimmed to fit.
    for category in [*pinned, *candidates]:
        line = fitted_line(ranked_line(category, weights), remaining)
        if line is not None:
            lines.append(line)
            remaining -= line_count(line)

    return lines
