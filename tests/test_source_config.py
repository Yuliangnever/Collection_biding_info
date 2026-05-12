from src.config_loader import load_settings
from src.source_config import load_enabled_sources


def test_loads_configured_tender_sources() -> None:
    settings = load_settings()

    sources = load_enabled_sources(settings["sources"])

    assert len(sources) == 11
    assert sources[0].platform == "国家能源招标网 / 国能e招"
    assert sources[-1].platform == "中核集团电子采购平台"

