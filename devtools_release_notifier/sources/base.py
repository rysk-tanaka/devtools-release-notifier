"""Base class for release information sources."""

from abc import ABC, abstractmethod


class ReleaseSource(ABC):
    """Abstract base class for release information sources."""

    def __init__(self, config: dict):
        """Initialize with configuration.

        Args:
            config: Configuration dictionary for this source
        """
        self.config = config

    @abstractmethod
    def fetch_latest_version(self) -> dict | None:
        """Fetch latest version information.

        Returns:
            Dictionary with version info or None if failed
        """
        pass
