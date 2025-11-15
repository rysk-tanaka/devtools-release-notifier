"""Tests for main notifier."""

import json

import httpx
import respx
import yaml

from devtools_release_notifier.notifier import UnifiedReleaseNotifier

# Sample configuration
SAMPLE_CONFIG = {
    "tools": [
        {
            "name": "Test Tool",
            "enabled": True,
            "sources": [
                {
                    "type": "homebrew_cask",
                    "priority": 1,
                    "api_url": "https://formulae.brew.sh/api/cask/test.json",
                }
            ],
            "notification": {"webhook_env": "DISCORD_WEBHOOK", "color": 5814783},
        }
    ],
    "common": {"check_interval_hours": 6, "cache_directory": "./cache"},
}

# Sample Homebrew response
HOMEBREW_RESPONSE = {
    "token": "test",
    "version": "1.0.0",
    "homepage": "https://example.com",
    "url": "https://example.com/download.dmg",
}


class TestUnifiedReleaseNotifier:
    """Tests for UnifiedReleaseNotifier."""

    def test_init(self, tmp_path, monkeypatch):
        """Test notifier initialization."""
        # Create temporary config file
        config_file = tmp_path / "config.yml"
        with open(config_file, "w") as f:
            yaml.dump(SAMPLE_CONFIG, f)

        # Change to temp directory
        monkeypatch.chdir(tmp_path)

        notifier = UnifiedReleaseNotifier(str(config_file))
        assert notifier.config is not None
        assert len(notifier.config.tools) == 1
        assert notifier.config.tools[0].name == "Test Tool"

    def test_get_cache_path(self, tmp_path, monkeypatch):
        """Test cache path generation."""
        config_file = tmp_path / "config.yml"
        with open(config_file, "w") as f:
            yaml.dump(SAMPLE_CONFIG, f)

        monkeypatch.chdir(tmp_path)

        notifier = UnifiedReleaseNotifier(str(config_file))
        cache_path = notifier.get_cache_path("Test Tool")

        assert cache_path.name == "test_tool_version.json"
        assert cache_path.parent.name == "cache"

    def test_save_and_load_cached_version(self, tmp_path, monkeypatch):
        """Test saving and loading cached version."""
        config_file = tmp_path / "config.yml"
        with open(config_file, "w") as f:
            yaml.dump(SAMPLE_CONFIG, f)

        monkeypatch.chdir(tmp_path)

        notifier = UnifiedReleaseNotifier(str(config_file))

        # Save version
        notifier.save_cached_version("Test Tool", "1.0.0")

        # Load version
        cached = notifier.load_cached_version("Test Tool")
        assert cached is not None
        assert cached.version == "1.0.0"

    def test_load_cached_version_not_found(self, tmp_path, monkeypatch):
        """Test loading non-existent cached version."""
        config_file = tmp_path / "config.yml"
        with open(config_file, "w") as f:
            yaml.dump(SAMPLE_CONFIG, f)

        monkeypatch.chdir(tmp_path)

        notifier = UnifiedReleaseNotifier(str(config_file))

        # Try to load non-existent cache
        cached = notifier.load_cached_version("Nonexistent Tool")
        assert cached is None

    @respx.mock
    def test_run_with_new_release(self, tmp_path, monkeypatch):
        """Test run with new release."""
        config_file = tmp_path / "config.yml"
        with open(config_file, "w") as f:
            yaml.dump(SAMPLE_CONFIG, f)

        monkeypatch.chdir(tmp_path)
        monkeypatch.delenv("DISCORD_WEBHOOK", raising=False)

        # Mock Homebrew API
        respx.get("https://formulae.brew.sh/api/cask/test.json").mock(
            return_value=httpx.Response(200, json=HOMEBREW_RESPONSE)
        )

        output_file = tmp_path / "releases.json"
        notifier = UnifiedReleaseNotifier(str(config_file))
        notifier.run(output_file=str(output_file), no_notify=True)

        # Check output file
        assert output_file.exists()
        with open(output_file) as f:
            releases = json.load(f)

        assert len(releases) == 1
        assert releases[0]["tool_name"] == "Test Tool"
        assert releases[0]["version"] == "1.0.0"

        # Check cache
        cached = notifier.load_cached_version("Test Tool")
        assert cached is not None
        assert cached.version == "1.0.0"

    @respx.mock
    def test_run_with_existing_version(self, tmp_path, monkeypatch):
        """Test run with existing version (no update)."""
        config_file = tmp_path / "config.yml"
        with open(config_file, "w") as f:
            yaml.dump(SAMPLE_CONFIG, f)

        monkeypatch.chdir(tmp_path)
        monkeypatch.delenv("DISCORD_WEBHOOK", raising=False)

        # Mock Homebrew API
        respx.get("https://formulae.brew.sh/api/cask/test.json").mock(
            return_value=httpx.Response(200, json=HOMEBREW_RESPONSE)
        )

        notifier = UnifiedReleaseNotifier(str(config_file))

        # Save existing version
        notifier.save_cached_version("Test Tool", "1.0.0")

        output_file = tmp_path / "releases.json"
        notifier.run(output_file=str(output_file), no_notify=True)

        # Output file should not be created (no new releases)
        assert not output_file.exists()

    @respx.mock
    def test_process_tool_disabled(self, tmp_path, monkeypatch):
        """Test processing disabled tool."""
        config = SAMPLE_CONFIG.copy()
        config["tools"][0]["enabled"] = False

        config_file = tmp_path / "config.yml"
        with open(config_file, "w") as f:
            yaml.dump(config, f)

        monkeypatch.chdir(tmp_path)

        output_file = tmp_path / "releases.json"
        notifier = UnifiedReleaseNotifier(str(config_file))
        notifier.run(output_file=str(output_file), no_notify=True)

        # Output file should not be created (tool disabled)
        assert not output_file.exists()

    @respx.mock
    def test_process_tool_with_discord_notification(self, tmp_path, monkeypatch):
        """Test processing tool with Discord notification."""
        # Create fresh config for this test
        config = {
            "tools": [
                {
                    "name": "Test Tool",
                    "enabled": True,
                    "sources": [
                        {
                            "type": "homebrew_cask",
                            "priority": 1,
                            "api_url": "https://formulae.brew.sh/api/cask/test.json",
                        }
                    ],
                    "notification": {"webhook_env": "DISCORD_WEBHOOK", "color": 5814783},
                }
            ],
            "common": {"check_interval_hours": 6, "cache_directory": "./cache"},
        }

        config_file = tmp_path / "config.yml"
        with open(config_file, "w") as f:
            yaml.dump(config, f)

        monkeypatch.chdir(tmp_path)
        monkeypatch.setenv("DISCORD_WEBHOOK", "https://discord.com/api/webhooks/123/abc")

        # Mock Homebrew API
        respx.get("https://formulae.brew.sh/api/cask/test.json").mock(
            return_value=httpx.Response(200, json=HOMEBREW_RESPONSE)
        )

        # Mock Discord webhook
        respx.post("https://discord.com/api/webhooks/123/abc").mock(
            return_value=httpx.Response(204)
        )

        notifier = UnifiedReleaseNotifier(str(config_file))
        notifier.run(no_notify=False)

        # Verify Discord webhook was called
        assert len([call for call in respx.calls if "discord.com" in str(call.request.url)]) == 1
