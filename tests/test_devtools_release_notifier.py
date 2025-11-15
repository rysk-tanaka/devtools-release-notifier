#!/usr/bin/env python

from devtools_release_notifier.main import main


def test_x04_data_link():
    assert main() is None
