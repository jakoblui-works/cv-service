from tests.content.builder import Builder


def test_default_content_is_valid(build: Builder) -> None:
    content = build.content()

    assert [job.id for job in content.experience] == ["acme"]
    assert len(content.experience[0].bullets) == 1


def test_custom_job_round_trips(build: Builder) -> None:
    job = build.job(
        "globex",
        bullets=[
            build.bullet("shipped-it", priority=2),
            build.bullet(
                "scaled-it",
                tags=["python"],
                variants=[build.variant("Scaled it 10×.", highlights=[build.highlight("10×", ["python"])])],
            ),
        ],
    )

    content = build.content(jobs=[job])

    assert content.model_dump(mode="json", exclude_none=True)["experience"] == [job]
