from collections.abc import Sequence

from app.content.models import Content

Data = dict[str, object]


def _label(id_: str) -> str:
    return id_.replace("-", " ").capitalize()


class Builder:
    """Builds small hand-made Content; anything not given gets a default that validates on its own."""

    def skill(self, id: str, priority: int = 0) -> Data:
        return {"id": id, "label": _label(id), "priority": priority}

    def category(self, id: str, skills: Sequence[Data], pinned: bool = False) -> Data:
        return {"id": id, "label": _label(id), "pinned": pinned, "skills": list(skills)}

    def concept(self, id: str, implies: Sequence[str] = ()) -> Data:
        return {"id": id, "label": _label(id), "implies": list(implies)}

    def title(self, id: str, emphasis: Sequence[str] = ()) -> Data:
        return {"id": id, "label": _label(id), "profile": f"{_label(id)} profile.", "emphasis": list(emphasis)}

    def variant(self, text: str, tags: Sequence[str] = (), highlights: Sequence[Data] = ()) -> Data:
        return {"text": text, "tags": list(tags), "highlights": list(highlights)}

    def highlight(self, text: str, tags: Sequence[str], priority: int = 0) -> Data:
        return {"text": text, "tags": list(tags), "priority": priority}

    def bullet(
        self, id: str, tags: Sequence[str] = (), priority: int = 0, variants: Sequence[Data] | None = None
    ) -> Data:
        if variants is None:
            variants = [self.variant(f"{_label(id)}.")]
        return {"id": id, "tags": list(tags), "priority": priority, "variants": list(variants)}

    def job(self, id: str, bullets: Sequence[Data] | None = None, descriptions: Sequence[Data] | None = None) -> Data:
        if bullets is None:
            bullets = [self.bullet("built-a-thing")]
        if descriptions is None:
            descriptions = [{"text": f"Worked at {_label(id)}.", "tags": []}]
        return {
            "id": id,
            "company": _label(id),
            "employment": "Full Time",
            "location": "Testville",
            "descriptions": list(descriptions),
            "roles": [{"title": "Developer", "start": "2020-01-01"}],
            "bullets": list(bullets),
        }

    def content(
        self,
        skills: Sequence[Data] | None = None,
        concepts: Sequence[Data] | None = None,
        titles: Sequence[Data] | None = None,
        jobs: Sequence[Data] | None = None,
        layout: Data | None = None,
    ) -> Content:
        if skills is None:
            skills = [self.category("programming", [self.skill("python")])]
        if titles is None:
            titles = [self.title("engineer")]
        if jobs is None:
            jobs = [self.job("acme")]
        if layout is None:
            layout = {"max_bullets_total": 20, "min_bullets_per_job": 1, "max_skill_lines": 20, "max_highlights": 5}
        return Content.model_validate(
            {
                "static": {"name": "Test Person", "city": "Testville", "projects": [], "education": []},
                "skills": list(skills),
                "concepts": list(concepts or []),
                "titles": list(titles),
                "experience": list(jobs),
                "layout": layout,
            }
        )
