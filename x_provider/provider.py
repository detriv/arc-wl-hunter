"""Abstract X Provider interface."""
from __future__ import annotations

import logging
from abc import ABC, abstractmethod

from config import Config
from models.post import Post


class XProvider(ABC):
    """Abstract base for X/Twitter data providers."""

    def __init__(self, config: Config, logger: logging.Logger) -> None:
        self.config = config
        self.logger = logger

    @abstractmethod
    async def initialize(self) -> None:
        """Initialize the provider (launch browser, etc.)."""
        ...

    @abstractmethod
    async def close(self) -> None:
        """Close the provider and release resources."""
        ...

    @abstractmethod
    async def validate_session(self) -> bool:
        """Check if the X session is authenticated."""
        ...

    @abstractmethod
    async def search_posts(
        self,
        query: str,
        max_results: int | None = None,
    ) -> list[Post]:
        """Search X for posts matching the query."""
        ...

    @abstractmethod
    async def login_flow(self) -> None:
        """Launch browser for manual X login."""
        ...
