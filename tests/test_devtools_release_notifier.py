#!/usr/bin/env python
"""Basic tests for devtools-release-notifier."""


def test_import():
    """Test basic module imports."""
    from devtools_release_notifier import notifier
    from devtools_release_notifier import sources
    from devtools_release_notifier import notifiers

    assert notifier is not None
    assert sources is not None
    assert notifiers is not None
