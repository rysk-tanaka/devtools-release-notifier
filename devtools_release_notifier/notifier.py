"""Main notifier script."""

import argparse
import json
import os
import sys
import traceback
from pathlib import Path

import yaml
from pydantic import ValidationError

from devtools_release_notifier.models.config import AppConfig
from devtools_release_notifier.models.output import ReleaseOutput
from devtools_release_notifier.models.release import CachedRelease, ReleaseInfo
from devtools_release_notifier.notifiers import DiscordNotifier
from devtools_release_notifier.sources import (
    GitHubCommitsSource,
    GitHubReleaseSource,
    HomebrewCaskSource,
    ReleaseSource,
)


class UnifiedReleaseNotifier:
    """Unified release notifier for development tools."""

    def __init__(self, config_path: str = "config.yml"):
        """Initialize notifier with configuration.

        Args:
            config_path: Path to configuration file
        """
        # Load configuration
        with open(config_path) as f:
            config_data = yaml.safe_load(f)

        self.config = AppConfig(**config_data)

        # Create cache directory
        cache_dir = Path(self.config.common.cache_directory)
        cache_dir.mkdir(parents=True, exist_ok=True)

        # Initialize Discord notifier
        self.discord_notifier = DiscordNotifier()

        # Initialize storage for new releases
        self.new_releases: list[ReleaseOutput] = []

    def get_source(self, source_config) -> ReleaseSource:
        """Get source instance based on configuration.

        Args:
            source_config: Source configuration

        Returns:
            Source instance

        Raises:
            ValueError: If source type is unknown
        """
        source_map: dict[str, type[ReleaseSource]] = {
            "github_releases": GitHubReleaseSource,
            "homebrew_cask": HomebrewCaskSource,
            "github_commits": GitHubCommitsSource,
        }

        source_class = source_map.get(source_config.type)
        if not source_class:
            raise ValueError(f"Unknown source type: {source_config.type}")

        # Convert Pydantic model to dict for source initialization
        return source_class(source_config.model_dump())

    def get_cache_path(self, tool_name: str) -> Path:
        """Get cache file path for a tool.

        Args:
            tool_name: Tool name

        Returns:
            Path to cache file
        """
        # Convert tool name to snake_case for filename
        filename = tool_name.lower().replace(" ", "_") + "_version.json"
        return Path(self.config.common.cache_directory) / filename

    def load_cached_version(self, tool_name: str) -> CachedRelease | None:
        """Load cached version information.

        Args:
            tool_name: Tool name

        Returns:
            Cached release information or None if not found
        """
        cache_path = self.get_cache_path(tool_name)
        if not cache_path.exists():
            return None

        try:
            with open(cache_path) as f:
                data = json.load(f)
            return CachedRelease(**data)
        except json.JSONDecodeError as e:
            print(f"⚠️  Failed to parse cache for {tool_name}: Invalid JSON - {e}")
            return None
        except ValidationError as e:
            print(f"⚠️  Failed to validate cache for {tool_name}: {e}")
            return None
        except OSError as e:
            print(f"⚠️  Failed to read cache for {tool_name}: {e}")
            return None

    def save_cached_version(self, tool_name: str, version: str):
        """Save version to cache.

        Args:
            tool_name: Tool name
            version: Version string
        """
        cache_path = self.get_cache_path(tool_name)
        cached = CachedRelease(version=version)

        try:
            with open(cache_path, "w") as f:
                json.dump(cached.model_dump(), f, indent=2)
        except OSError as e:
            print(f"⚠️  Failed to write cache for {tool_name}: {e}")

    def process_tool(self, tool_config, output_file: str | None, no_notify: bool):
        """Process a single tool.

        Args:
            tool_config: Tool configuration
            output_file: Output file path for new releases
            no_notify: Skip Discord notification
        """
        if not tool_config.enabled:
            print(f"⏭️  {tool_config.name}: Skipped (disabled)")
            return

        print(f"\n🔍 Processing {tool_config.name}...")

        # Sort sources by priority
        sorted_sources = sorted(tool_config.sources, key=lambda s: s.priority)

        # Try sources in priority order
        latest_info: ReleaseInfo | None = None
        for source_config in sorted_sources:
            print(f"  Trying {source_config.type} (priority {source_config.priority})...")
            try:
                source = self.get_source(source_config)
                result = source.fetch_latest_version()
                if result:
                    # Convert dict to ReleaseInfo
                    latest_info = ReleaseInfo(**result)
                    print(f"  ✓ Got version {latest_info.version} from {source_config.type}")
                    break
            except Exception as e:
                print(f"  ✗ Failed: {e}")
                continue

        if not latest_info:
            print(f"⚠️  {tool_config.name}: No version information available")
            return

        # Check cache
        cached = self.load_cached_version(tool_config.name)
        if cached and cached.version == latest_info.version:
            print(f"ℹ️  {tool_config.name}: Already up to date ({latest_info.version})")
            return

        print(f"🎉 {tool_config.name}: New version {latest_info.version}")

        # Prepare output if requested
        if output_file:
            release_output = ReleaseOutput(
                tool_name=tool_config.name,
                version=latest_info.version,
                content=latest_info.content,
                url=latest_info.url,
                color=tool_config.notification.color,
                webhook_env=tool_config.notification.webhook_env,
            )
            self.new_releases.append(release_output)

        # Send Discord notification if not disabled
        if not no_notify:
            webhook_url = os.getenv(tool_config.notification.webhook_env)
            if webhook_url:
                self.discord_notifier.send(
                    webhook_url=webhook_url,
                    tool_name=tool_config.name,
                    version=latest_info.version,
                    content=latest_info.content,
                    url=latest_info.url,
                    color=tool_config.notification.color,
                )
            else:
                print(
                    f"⚠️  {tool_config.name}: Webhook URL not found "
                    f"({tool_config.notification.webhook_env})"
                )

        # Update cache
        self.save_cached_version(tool_config.name, latest_info.version)

    def run(self, output_file: str | None = None, no_notify: bool = False):
        """Run notifier for all tools.

        Args:
            output_file: Output file path for new releases
            no_notify: Skip Discord notification
        """
        print("🚀 Starting devtools-release-notifier")

        for tool_config in self.config.tools:
            self.process_tool(tool_config, output_file, no_notify)

        # Write output file if requested and there are new releases
        if output_file and self.new_releases:
            with open(output_file, "w") as f:
                # Convert Pydantic models to dicts
                releases_data = [r.model_dump() for r in self.new_releases]
                json.dump(releases_data, f, indent=2)
            print(f"\n✓ Wrote {len(self.new_releases)} new releases to {output_file}")

        print("\n✅ Completed")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Development tools release notifier")
    parser.add_argument("--output", type=str, help="Output new releases to JSON file")
    parser.add_argument("--no-notify", action="store_true", help="Skip Discord notification")
    args = parser.parse_args()

    # Check config file exists
    config_path = "config.yml"
    if not os.path.exists(config_path):
        print(f"✗ Configuration file not found: {config_path}")
        sys.exit(1)

    try:
        notifier = UnifiedReleaseNotifier(config_path)
        notifier.run(output_file=args.output, no_notify=args.no_notify)
    except KeyboardInterrupt:
        print("\n\n⚠️  Interrupted by user")
        sys.exit(130)
    except Exception as e:
        print(f"\n✗ Error: {e}")
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
