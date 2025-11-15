#!/usr/bin/env python
"""Basic tests for devtools-release-notifier."""


def test_import():
    """Test basic module imports."""
    from devtools_release_notifier import notifier
    from devtools_release_notifier.sources import base
    from devtools_release_notifier.notifiers import discord

    assert notifier is not None
    assert base is not None
    assert discord is not None
