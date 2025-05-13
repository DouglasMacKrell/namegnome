"""Tests for the MetadataClient base interface.

Covers expected usage, edge cases, and failure modes for the abstract
metadata provider interface. See TASK.md Sprint 2.1 and PLANNING.md.
"""

import pytest

from namegnome.metadata.base import MetadataClient
from namegnome.metadata.models import MediaMetadata, MediaMetadataType


class DummyClient(MetadataClient):
    """Dummy implementation for testing the abstract base class."""

    async def search(self, title: str, year: int | None = None) -> list[MediaMetadata]:
        """Return a dummy MediaMetadata result for testing.

        Args:
            title: The title to search for.
            year: Optional release year.

        Returns:
            List with a single MediaMetadata object.
        """
        return [
            MediaMetadata(
                title=title,
                media_type=MediaMetadataType.MOVIE,
                provider="dummy",
                provider_id="1",
            )
        ]

    async def details(self, provider_id: str) -> MediaMetadata:
        """Return a dummy MediaMetadata object for testing.

        Args:
            provider_id: The provider-specific ID.

        Returns:
            A MediaMetadata object with the given provider_id.
        """
        return MediaMetadata(
            title="Test Movie",
            media_type=MediaMetadataType.MOVIE,
            provider="dummy",
            provider_id=provider_id,
        )


@pytest.mark.asyncio
async def test_expected_flow_search_and_details() -> None:
    """Expected flow: DummyClient returns MediaMetadata for search and details."""
    client = DummyClient()
    results = await client.search("Test Title", 2020)
    assert len(results) == 1
    assert results[0].title == "Test Title"
    details = await client.details("1")
    assert details.provider_id == "1"
    assert details.title == "Test Movie"


@pytest.mark.asyncio
async def test_edge_case_empty_title() -> None:
    """Edge case: search with empty title returns MediaMetadata with empty title."""
    client = DummyClient()
    results = await client.search("", None)
    assert len(results) == 1
    assert results[0].title == ""


def test_failure_not_implemented() -> None:
    """Failure case: TypeError is raised if abstract methods are not implemented.

    Python's ABC prevents instantiation of abstract classes without all abstract
    methods implemented. This test ensures that attempting to instantiate a
    subclass without implementing required methods raises TypeError.
    """

    class IncompleteClient(MetadataClient):
        pass

    with pytest.raises(TypeError):
        IncompleteClient()  # type: ignore[abstract]
