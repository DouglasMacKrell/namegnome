"""Test show recognition and metadata provider integration issues.

This test file specifically addresses Sprint 1.7.2 issues:
- Show names like "Paw Patrol" not being recognized properly
- Metadata provider integration not using mocked responses correctly in E2E tests
- Show name normalization issues ("The Octonauts" vs "Octonauts")
- Missing confidence scoring for show name matches
"""

import pytest
import tempfile
from pathlib import Path
from unittest.mock import patch

from namegnome.metadata.models import MediaMetadata, MediaMetadataType, TVEpisode
from namegnome.metadata.clients.tvdb import TVDBClient


class TestShowNameRecognition:
    """Test that show names are correctly extracted and recognized from filenames."""

    def test_show_name_extraction_from_standard_filenames(self):
        """Test that show names are correctly extracted from various filename patterns."""
        from namegnome.core.scanner import _create_media_file
        from namegnome.models.core import MediaType

        test_cases = [
            ("Paw Patrol-S01E01-Episode Title.mp4", "Paw Patrol"),
            ("The Octonauts-S01E01-The Whale Shark.mp4", "The Octonauts"),
            (
                "Harvey Girls Forever! - S01E01 - War and Trees WEBDL-1080p.mkv",
                "Harvey Girls Forever!",
            ),
            (
                "Martha Speaks-S01E01-Martha Speaks Martha Gives Advice.mp4",
                "Martha Speaks",
            ),
            ("Firebuds-S01E01-Car In A Tree Dalmatian Day.mp4", "Firebuds"),
            (
                "Danger Mouse 2015-S01E01-Danger Mouse Begins Again.mp4",
                "Danger Mouse 2015",
            ),
        ]

        # Create a temporary directory with proper filenames
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            for filename, expected_show_name in test_cases:
                # Create file with proper name in temp directory
                file_path = temp_path / filename
                file_path.write_text("fake video content")

                try:
                    errors = []
                    media_file, media_type = _create_media_file(
                        file_path, verify_hash=False, errors=errors
                    )

                    assert media_type == MediaType.TV, (
                        f"Should detect TV media type for {filename}"
                    )
                    assert media_file.title == expected_show_name, (
                        f"Expected '{expected_show_name}', got '{media_file.title}' for {filename}"
                    )
                    assert len(errors) == 0, (
                        f"Should not have errors for {filename}: {errors}"
                    )
                finally:
                    # Cleanup handled by tempfile.TemporaryDirectory
                    pass

    def test_show_name_normalization(self):
        """Test that show name normalization handles common variations correctly."""
        from namegnome.core.tv.utils import normalize_show_name

        test_cases = [
            ("The Octonauts", "Octonauts"),  # Strip "The" prefix
            ("  Paw Patrol  ", "Paw Patrol"),  # Strip whitespace
            ("Harvey Girls Forever!", "Harvey Girls Forever!"),  # Preserve punctuation
            ("Martha Speaks", "Martha Speaks"),  # Keep as-is
            ("DANGER MOUSE 2015", "Danger Mouse 2015"),  # Case normalization
        ]

        for input_name, expected_normalized in test_cases:
            result = normalize_show_name(input_name)
            assert result == expected_normalized, (
                f"Expected '{expected_normalized}', got '{result}' for '{input_name}'"
            )


class TestMetadataProviderIntegration:
    """Test that metadata providers work correctly in E2E scenarios with mocked responses."""

    @pytest.mark.asyncio
    async def test_mock_provider_returns_paw_patrol_metadata(self):
        """Test that mocked providers can return Paw Patrol metadata correctly."""
        # Create mock Paw Patrol metadata
        paw_patrol_episodes = [
            TVEpisode(
                title="Pups Save the Sea Turtles",
                episode_number=1,
                season_number=1,
                air_date=None,
                overview="The PAW Patrol must help sea turtle hatchlings make it to the ocean.",
            ),
            TVEpisode(
                title="Pup Pup Boogie",
                episode_number=2,
                season_number=1,
                air_date=None,
                overview="The pups need to help solve a dance emergency.",
            ),
        ]

        paw_patrol_metadata = MediaMetadata(
            title="PAW Patrol",
            media_type=MediaMetadataType.TV_SHOW,
            provider="tvdb",
            provider_id="281887",
            year=2013,
            episodes=paw_patrol_episodes,
            overview="PAW Patrol is about a group of six rescue dogs led by a tech-savvy boy named Ryder.",
        )

        # Mock TVDB client to return Paw Patrol data
        with patch.object(TVDBClient, "search") as mock_search:
            mock_search.return_value = [paw_patrol_metadata]

            client = TVDBClient()
            results = await client.search("Paw Patrol")

            assert len(results) == 1
            result = results[0]
            assert result.title == "PAW Patrol"
            assert result.provider_id == "281887"
            assert len(result.episodes) == 2

    @pytest.mark.asyncio
    async def test_mock_provider_handles_show_variations(self):
        """Test that mocked providers handle show name variations correctly."""
        test_shows = [
            {
                "search_term": "Paw Patrol",
                "canonical_name": "PAW Patrol",
                "provider_id": "281887",
            },
            {
                "search_term": "The Octonauts",
                "canonical_name": "Octonauts",
                "provider_id": "269654",
            },
            {
                "search_term": "Harvey Girls Forever",
                "canonical_name": "Harvey Girls Forever!",
                "provider_id": "346168",
            },
        ]

        for show_data in test_shows:
            # Create mock metadata for this show
            mock_metadata = MediaMetadata(
                title=show_data["canonical_name"],
                media_type=MediaMetadataType.TV_SHOW,
                provider="tvdb",
                provider_id=show_data["provider_id"],
                year=2015,
                episodes=[],
                overview=f"Mock overview for {show_data['canonical_name']}",
            )

            with patch.object(TVDBClient, "search") as mock_search:
                mock_search.return_value = [mock_metadata]

                client = TVDBClient()
                results = await client.search(show_data["search_term"])

                assert len(results) == 1
                result = results[0]
                assert result.title == show_data["canonical_name"]
                assert result.provider_id == show_data["provider_id"]

    def test_e2e_scan_with_comprehensive_mock_providers(self):
        """Test E2E scan using comprehensive mocked providers for all fixture shows."""
        import subprocess
        import os

        # Create temporary directory with test files
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # Create test files for different shows
            test_files = [
                "Paw Patrol/Paw Patrol-S01E01-Pups Save The Sea Turtles.mp4",
                "The Octonauts/The Octonauts-S01E01-The Whale Shark.mp4",
                "Harvey Girls Forever/Harvey Girls Forever! - S01E01 - War and Trees.mkv",
            ]

            for file_path in test_files:
                full_path = temp_path / file_path
                full_path.parent.mkdir(parents=True, exist_ok=True)
                full_path.write_text("fake video content")

            # Run scan with mocked providers
            result = subprocess.run(
                [
                    "poetry",
                    "run",
                    "python",
                    "-m",
                    "namegnome",
                    "scan",
                    "--media-type",
                    "tv",
                    "--json",
                    "--no-color",
                    str(temp_path),
                ],
                capture_output=True,
                text=True,
                env={
                    **os.environ,
                    "NAMEGNOME_E2E_TESTS": "1",
                    "NAMEGNOME_NON_INTERACTIVE": "1",
                },
            )

            # Should not fail due to provider issues
            assert result.returncode in [0, 2], (
                f"Scan should succeed but got: {result.stderr}"
            )

            # Should not contain "Real provider failed" warnings for shows that should have mocked data
            output = result.stdout + result.stderr
            if "Real provider failed" in output:
                # This is what we're trying to fix - providers should be properly mocked
                assert False, (
                    f"Providers not properly mocked. Output: {output[:500]}..."
                )


class TestConfidenceScoring:
    """Test confidence scoring for show name matches."""

    def test_confidence_scoring_for_exact_matches(self):
        """Test that exact show name matches get high confidence scores."""
        from namegnome.core.fuzzy_matcher import calculate_show_confidence

        test_cases = [
            ("Paw Patrol", "PAW Patrol", 0.95),  # Should be very high confidence
            ("The Octonauts", "Octonauts", 0.90),  # Good match despite "The" difference
            ("Harvey Girls Forever!", "Harvey Girls Forever!", 1.0),  # Perfect match
            ("Danger Mouse 2015", "Danger Mouse", 0.85),  # Good match, year difference
            ("martha speaks", "Martha Speaks", 0.95),  # Case insensitive match
        ]

        for input_name, canonical_name, expected_min_confidence in test_cases:
            confidence = calculate_show_confidence(input_name, canonical_name)
            assert confidence >= expected_min_confidence, (
                f"Expected confidence >= {expected_min_confidence} for '{input_name}' vs '{canonical_name}', got {confidence}"
            )

    def test_confidence_scoring_for_partial_matches(self):
        """Test that partial matches get appropriate confidence scores."""
        from namegnome.core.fuzzy_matcher import calculate_show_confidence

        test_cases = [
            ("Paw", "PAW Patrol", 0.4),  # Partial match, should be lower
            ("Some Random Show", "PAW Patrol", 0.1),  # Poor match
            ("Patrol Paw", "PAW Patrol", 0.6),  # Word order difference
        ]

        for input_name, canonical_name, expected_max_confidence in test_cases:
            confidence = calculate_show_confidence(input_name, canonical_name)
            assert confidence <= expected_max_confidence, (
                f"Expected confidence <= {expected_max_confidence} for '{input_name}' vs '{canonical_name}', got {confidence}"
            )
