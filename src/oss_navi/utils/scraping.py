"""Scraping utilities with fake_useragent and proxy support."""

import asyncio
import random
import time
from typing import TYPE_CHECKING

import httpx

if TYPE_CHECKING:
    pass

# Default rate limit (seconds between requests)
DEFAULT_RATE_LIMIT = 2.0


class ScrapingConfig:
    """Configuration for scraping requests."""

    def __init__(
        self,
        rate_limit: float = DEFAULT_RATE_LIMIT,
        proxy: str | None = None,
        user_agent: str | None = None,
        timeout: float = 30.0,
    ):
        """Initialize scraping configuration.

        Args:
            rate_limit: Seconds between requests
            proxy: Proxy URL (e.g., "http://localhost:8118")
            user_agent: Custom user agent (default: random from fake_useragent)
            timeout: Request timeout in seconds
        """
        self.rate_limit = rate_limit
        self.proxy = proxy
        self.user_agent = user_agent
        self.timeout = timeout
        self._last_request_time = 0.0

    def get_user_agent(self) -> str:
        """Get user agent string.

        Uses fake_useragent if available, otherwise falls back to common agents.
        """
        if self.user_agent:
            return self.user_agent

        try:
            from fake_useragent import UserAgent
            ua = UserAgent()
            return ua.random
        except ImportError:
            # Fallback to common user agents
            agents = [
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
            ]
            return random.choice(agents)


class Scraper:
    """Rate-limited scraper with proxy support."""

    def __init__(self, config: ScrapingConfig | None = None):
        """Initialize scraper.

        Args:
            config: Scraping configuration
        """
        self.config = config or ScrapingConfig()

    def _wait_for_rate_limit(self) -> None:
        """Wait to respect rate limit."""
        elapsed = time.time() - self.config._last_request_time
        if elapsed < self.config.rate_limit:
            time.sleep(self.config.rate_limit - elapsed)
        self.config._last_request_time = time.time()

    def fetch(
        self,
        url: str,
        method: str = "GET",
        headers: dict | None = None,
        **kwargs,
    ) -> httpx.Response:
        """Fetch URL with rate limiting and user agent rotation.

        Args:
            url: URL to fetch
            method: HTTP method
            headers: Additional headers
            **kwargs: Additional arguments for httpx

        Returns:
            httpx.Response
        """
        self._wait_for_rate_limit()

        # Build headers
        request_headers = {
            "User-Agent": self.config.get_user_agent(),
        }
        if headers:
            request_headers.update(headers)

        # Build client kwargs
        client_kwargs = {
            "timeout": self.config.timeout,
        }
        if self.config.proxy:
            client_kwargs["proxy"] = self.config.proxy

        with httpx.Client(**client_kwargs) as client:
            response = client.request(
                method=method,
                url=url,
                headers=request_headers,
                **kwargs,
            )
            return response

    async def fetch_async(
        self,
        url: str,
        method: str = "GET",
        headers: dict | None = None,
        **kwargs,
    ) -> httpx.Response:
        """Async fetch URL with rate limiting and user agent rotation.

        Args:
            url: URL to fetch
            method: HTTP method
            headers: Additional headers
            **kwargs: Additional arguments for httpx

        Returns:
            httpx.Response
        """
        await asyncio.sleep(self.config.rate_limit)

        # Build headers
        request_headers = {
            "User-Agent": self.config.get_user_agent(),
        }
        if headers:
            request_headers.update(headers)

        # Build client kwargs
        client_kwargs = {
            "timeout": self.config.timeout,
        }
        if self.config.proxy:
            client_kwargs["proxy"] = self.config.proxy

        async with httpx.AsyncClient(**client_kwargs) as client:
            response = await client.request(
                method=method,
                url=url,
                headers=request_headers,
                **kwargs,
            )
            return response

    def fetch_json(self, url: str, **kwargs) -> dict | None:
        """Fetch URL and parse as JSON.

        Args:
            url: URL to fetch
            **kwargs: Additional arguments for fetch

        Returns:
            Parsed JSON dict or None on error
        """
        try:
            response = self.fetch(url, **kwargs)
            if response.status_code == 200:
                return response.json()
        except Exception:
            pass
        return None

    def fetch_text(self, url: str, **kwargs) -> str | None:
        """Fetch URL and return text content.

        Args:
            url: URL to fetch
            **kwargs: Additional arguments for fetch

        Returns:
            Text content or None on error
        """
        try:
            response = self.fetch(url, **kwargs)
            if response.status_code == 200:
                return response.text
        except Exception:
            pass
        return None


def create_scraper(
    rate_limit: float = DEFAULT_RATE_LIMIT,
    proxy: str | None = None,
) -> Scraper:
    """Create a scraper with specified configuration.

    Args:
        rate_limit: Seconds between requests
        proxy: Proxy URL

    Returns:
        Configured Scraper instance
    """
    config = ScrapingConfig(rate_limit=rate_limit, proxy=proxy)
    return Scraper(config)


# Convenience functions
def scrape_url(
    url: str,
    rate_limit: float = DEFAULT_RATE_LIMIT,
    proxy: str | None = None,
) -> str | None:
    """Scrape a URL with rate limiting.

    Args:
        url: URL to scrape
        rate_limit: Seconds between requests
        proxy: Optional proxy URL

    Returns:
        Page content or None on error
    """
    scraper = create_scraper(rate_limit=rate_limit, proxy=proxy)
    return scraper.fetch_text(url)


def scrape_json(
    url: str,
    rate_limit: float = DEFAULT_RATE_LIMIT,
    proxy: str | None = None,
) -> dict | None:
    """Scrape a URL and parse as JSON.

    Args:
        url: URL to scrape
        rate_limit: Seconds between requests
        proxy: Optional proxy URL

    Returns:
        Parsed JSON or None on error
    """
    scraper = create_scraper(rate_limit=rate_limit, proxy=proxy)
    return scraper.fetch_json(url)
