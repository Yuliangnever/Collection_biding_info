from src.topic_utils import DEFAULT_TOPICS, parse_topics, settings_with_topics


def test_parse_topics_uses_default_when_empty() -> None:
    assert parse_topics("") == DEFAULT_TOPICS


def test_parse_topics_splits_common_separators() -> None:
    assert parse_topics("光伏 风电，储能、柔性支架") == [
        "光伏",
        "风电",
        "储能",
        "柔性支架",
    ]


def test_settings_with_topics_overrides_target_topics() -> None:
    settings = {"keywords": {"target_topics": ["光伏"]}}

    updated = settings_with_topics(settings, ["风电"])

    assert updated["keywords"]["target_topics"] == ["风电"]
    assert settings["keywords"]["target_topics"] == ["光伏"]

