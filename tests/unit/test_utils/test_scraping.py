"""Tests for scraping utility."""

from unittest.mock import MagicMock, patch

from oss_navi.utils.scraping import (
    DEFAULT_RATE_LIMIT,
    Scraper,
    ScrapingConfig,
    create_scraper,
    scrape_json,
    scrape_url,
)


class TestScrapingConfig:
    """Tests for ScrapingConfig."""

    def test_create_config(self) -> None:
        """Test creating a ScrapingConfig."""
        config = ScrapingConfig(
            rate_limit=2.0,
            proxy="http://proxy:8080",
            user_agent="CustomAgent/1.0",
            timeout=60.0,
        )
        assert config.rate_limit == 2.0
        assert config.proxy == "http://proxy:8080"
        assert config.user_agent == "CustomAgent/1.0"
        assert config.timeout == 60.0

    def test_config_defaults(self) -> None:
        """Test ScrapingConfig defaults."""
        config = ScrapingConfig()
        assert config.rate_limit == DEFAULT_RATE_LIMIT
        assert config.proxy is None
        assert config.user_agent is None
        assert config.timeout == 30.0

    def test_get_user_agent_custom(self) -> None:
        """Test get_user_agent with custom agent."""
        config = ScrapingConfig(user_agent="CustomAgent/1.0")
        assert config.get_user_agent() == "CustomAgent/1.0"

    def test_get_user_agent_fallback(self) -> None:
        """Test get_user_agent fallback without fake_useragent."""
        config = ScrapingConfig()
        agent = config.get_user_agent()
        # Should return one of the fallback agents
        assert "Mozilla" in agent


class TestScraper:
    """Tests for Scraper class."""

    def test_create_scraper_with_config(self) -> None:
        """Test creating a Scraper with config."""
        config = ScrapingConfig(rate_limit=2.0)
        scraper = Scraper(config=config)
        assert scraper.config.rate_limit == 2.0

    def test_scraper_default_config(self) -> None:
        """Test Scraper with default config."""
        scraper = Scraper()
        assert scraper.config.rate_limit == DEFAULT_RATE_LIMIT

    @patch("oss_navi.utils.scraping.httpx.Client")
    def test_fetch(self, mock_client: MagicMock) -> None:
        """Test fetch method."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_instance = MagicMock()
        mock_instance.request.return_value = mock_response
        mock_instance.__enter__ = MagicMock(return_value=mock_instance)
        mock_instance.__exit__ = MagicMock(return_value=False)
        mock_client.return_value = mock_instance

        config = ScrapingConfig(rate_limit=0.0)  # No rate limit for testing
        scraper = Scraper(config=config)
        response = scraper.fetch("https://example.com")

        assert response.status_code == 200
        mock_instance.request.assert_called_once()

    @patch("oss_navi.utils.scraping.httpx.Client")
    def test_fetch_with_proxy(self, mock_client: MagicMock) -> None:
        """Test fetch with proxy."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_instance = MagicMock()
        mock_instance.request.return_value = mock_response
        mock_instance.__enter__ = MagicMock(return_value=mock_instance)
        mock_instance.__exit__ = MagicMock(return_value=False)
        mock_client.return_value = mock_instance

        config = ScrapingConfig(
            rate_limit=0.0,
            proxy="http://proxy:8080",
        )
        scraper = Scraper(config=config)
        scraper.fetch("https://example.com")

        # Check that proxy was passed to client
        call_kwargs = mock_client.call_args[1]
        assert call_kwargs["proxy"] == "http://proxy:8080"

    @patch("oss_navi.utils.scraping.httpx.Client")
    def test_fetch_json(self, mock_client: MagicMock) -> None:
        """Test fetch_json method."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"key": "value"}
        mock_instance = MagicMock()
        mock_instance.request.return_value = mock_response
        mock_instance.__enter__ = MagicMock(return_value=mock_instance)
        mock_instance.__exit__ = MagicMock(return_value=False)
        mock_client.return_value = mock_instance

        config = ScrapingConfig(rate_limit=0.0)
        scraper = Scraper(config=config)
        result = scraper.fetch_json("https://example.com/api")

        assert result == {"key": "value"}

    @patch("oss_navi.utils.scraping.httpx.Client")
    def test_fetch_json_error(self, mock_client: MagicMock) -> None:
        """Test fetch_json returns None on error."""
        mock_instance = MagicMock()
        mock_instance.request.side_effect = Exception("Network error")
        mock_instance.__enter__ = MagicMock(return_value=mock_instance)
        mock_instance.__exit__ = MagicMock(return_value=False)
        mock_client.return_value = mock_instance

        config = ScrapingConfig(rate_limit=0.0)
        scraper = Scraper(config=config)
        result = scraper.fetch_json("https://example.com/api")

        assert result is None

    @patch("oss_navi.utils.scraping.httpx.Client")
    def test_fetch_text(self, mock_client: MagicMock) -> None:
        """Test fetch_text method."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = "<html>content</html>"
        mock_instance = MagicMock()
        mock_instance.request.return_value = mock_response
        mock_instance.__enter__ = MagicMock(return_value=mock_instance)
        mock_instance.__exit__ = MagicMock(return_value=False)
        mock_client.return_value = mock_instance

        config = ScrapingConfig(rate_limit=0.0)
        scraper = Scraper(config=config)
        result = scraper.fetch_text("https://example.com")

        assert result == "<html>content</html>"


class TestConvenienceFunctions:
    """Tests for convenience functions."""

    @patch("oss_navi.utils.scraping.httpx.Client")
    def test_create_scraper_func(self, mock_client: MagicMock) -> None:
        """Test create_scraper function."""
        scraper = create_scraper(rate_limit=5.0, proxy="http://proxy:8080")
        assert scraper.config.rate_limit == 5.0
        assert scraper.config.proxy == "http://proxy:8080"

    @patch("oss_navi.utils.scraping.httpx.Client")
    def test_scrape_url(self, mock_client: MagicMock) -> None:
        """Test scrape_url function."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = "page content"
        mock_instance = MagicMock()
        mock_instance.request.return_value = mock_response
        mock_instance.__enter__ = MagicMock(return_value=mock_instance)
        mock_instance.__exit__ = MagicMock(return_value=False)
        mock_client.return_value = mock_instance

        result = scrape_url("https://example.com", rate_limit=0.0)
        assert result == "page content"

    @patch("oss_navi.utils.scraping.httpx.Client")
    def test_scrape_json(self, mock_client: MagicMock) -> None:
        """Test scrape_json function."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"data": "value"}
        mock_instance = MagicMock()
        mock_instance.request.return_value = mock_response
        mock_instance.__enter__ = MagicMock(return_value=mock_instance)
        mock_instance.__exit__ = MagicMock(return_value=False)
        mock_client.return_value = mock_instance

        result = scrape_json("https://example.com/api", rate_limit=0.0)
        assert result == {"data": "value"}
