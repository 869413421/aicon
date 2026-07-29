from unittest.mock import patch

from src.services.provider.custom_provider import CustomProvider
from src.services.provider.factory import ProviderFactory


def test_factory_uses_atlascloud_openai_compatible_endpoint():
    with patch("src.services.provider.custom_provider.AsyncOpenAI") as openai:
        provider = ProviderFactory.create("atlascloud", "test-key")

    assert isinstance(provider, CustomProvider)
    assert provider.base_url == "https://api.atlascloud.ai/v1"
    openai.assert_called_once_with(
        api_key="test-key",
        base_url="https://api.atlascloud.ai/v1",
    )
