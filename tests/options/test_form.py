from app.content.loader import load_content
from app.content.models import Content
from app.options.form import FormOptions, Option, SkillGroup, build_form_options
from tests.content.builder import Builder


def _content() -> Content:
    build = Builder()
    return build.content(
        skills=[
            build.category("languages", [build.skill("danish")], pinned=True),
            build.category("programming", [build.skill("rust"), build.skill("python")]),
            build.category("frontend", [build.skill("react")]),
        ],
        concepts=[build.concept("backend", implies=["python"]), build.concept("ui", implies=["react"])],
        titles=[build.title("lead"), build.title("engineer")],
    )


def test_titles_and_concepts_in_content_order() -> None:
    options = build_form_options(_content())

    assert options.titles == [Option(id="lead", label="Lead"), Option(id="engineer", label="Engineer")]
    assert options.concepts == [Option(id="backend", label="Backend"), Option(id="ui", label="Ui")]


def test_skill_groups_in_content_order() -> None:
    options = build_form_options(_content())

    assert options.skill_groups == [
        SkillGroup(
            id="programming",
            label="Programming",
            skills=[Option(id="rust", label="Rust"), Option(id="python", label="Python")],
        ),
        SkillGroup(id="frontend", label="Frontend", skills=[Option(id="react", label="React")]),
    ]


def test_pinned_categories_are_left_out() -> None:
    options = build_form_options(_content())

    group_ids = [group.id for group in options.skill_groups]
    skill_ids = [skill.id for group in options.skill_groups for skill in group.skills]
    assert "languages" not in group_ids
    assert "danish" not in skill_ids


def test_options_round_trip_through_json() -> None:
    options = build_form_options(_content())

    assert FormOptions.model_validate(options.model_dump(mode="json")) == options


def test_real_content_publishes_every_choosable_option() -> None:
    content = load_content()

    options = build_form_options(content)

    assert len(options.titles) == len(content.titles)
    assert len(options.concepts) == len(content.concepts)
    assert len(options.skill_groups) == sum(1 for category in content.skills if not category.pinned)
