"""Tests for namegnome.core.tv.utils helper functions."""

from namegnome.core.tv import utils as tu


def test_strip_preamble_dash():
    assert tu._strip_preamble("Martha Speaks - The Penguin") == "The Penguin"


def test_strip_preamble_colon():
    assert tu._strip_preamble("Paw Patrol: Pups Save A Train") == "Pups Save A Train"


def test_strip_preamble_no_delim():
    original = "Generic Episode Title"
    assert tu._strip_preamble(original) == original 