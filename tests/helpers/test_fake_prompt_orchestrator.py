"""Tests for the fake prompt orchestrator stub.

Verifies that the FakePromptOrchestrator provides deterministic, configurable
responses without making network calls.
"""

from pathlib import Path
from unittest.mock import Mock


from namegnome.models.core import MediaFile
from tests.helpers.fake_prompt_orchestrator import (
    FakePromptOrchestrator,
    stub_llm,
    set_fake_confidence,
    get_fake_orchestrator,
)


class TestFakePromptOrchestrator:
    """Test the FakePromptOrchestrator class directly."""

    def test_init_default_confidence(self):
        """Test default confidence level initialization."""
        orchestrator = FakePromptOrchestrator()
        assert orchestrator.confidence == 0.90

    def test_init_custom_confidence(self):
        """Test custom confidence level initialization."""
        orchestrator = FakePromptOrchestrator(confidence=0.60)
        assert orchestrator.confidence == 0.60

    def test_deterministic_hash(self):
        """Test that hash generation is deterministic."""
        orchestrator = FakePromptOrchestrator()
        hash1 = orchestrator._get_deterministic_hash("test")
        hash2 = orchestrator._get_deterministic_hash("test")
        assert hash1 == hash2

        # Different inputs should produce different hashes
        hash3 = orchestrator._get_deterministic_hash("different")
        assert hash1 != hash3

    def test_split_anthology_high_confidence(self):
        """Test split_anthology with high confidence (auto mode)."""
        orchestrator = FakePromptOrchestrator(confidence=0.90)

        # Create a mock MediaFile
        media_file = Mock(spec=MediaFile)
        media_file.path = Path("/test/Show-S01E01-E02-Episode Title.mp4")

        result = orchestrator.split_anthology(
            media_file=media_file,
            show_name="Test Show",
            season_number=1,
            episode_list=[
                {"episode": 1, "title": "Episode 1"},
                {"episode": 2, "title": "Episode 2"},
            ],
        )

        assert "episode_numbers" in result
        assert "episode_list" in result
        assert result["episode_numbers"] == ["1", "2"]  # Should extract span

    def test_split_anthology_medium_confidence(self):
        """Test split_anthology with medium confidence (manual mode)."""
        orchestrator = FakePromptOrchestrator(confidence=0.50)

        media_file = Mock(spec=MediaFile)
        media_file.path = Path("/test/Show-S01E01-E02-Episode Title.mp4")

        result = orchestrator.split_anthology(
            media_file=media_file, show_name="Test Show", season_number=1
        )

        # Medium confidence should return fewer episodes
        assert len(result["episode_numbers"]) <= 1

    def test_split_anthology_low_confidence(self):
        """Test split_anthology with low confidence (unsupported mode)."""
        orchestrator = FakePromptOrchestrator(confidence=0.30)

        media_file = Mock(spec=MediaFile)
        media_file.path = Path("/test/Show-S01E01-E02-Episode Title.mp4")

        result = orchestrator.split_anthology(
            media_file=media_file, show_name="Test Show", season_number=1
        )

        # Low confidence should return empty
        assert result["episode_numbers"] == []

    def test_split_anthology_single_episode(self):
        """Test split_anthology with single episode pattern."""
        orchestrator = FakePromptOrchestrator(confidence=0.90)

        media_file = Mock(spec=MediaFile)
        media_file.path = Path("/test/Show-S01E05-Episode Title.mp4")

        result = orchestrator.split_anthology(
            media_file=media_file, show_name="Test Show", season_number=1
        )

        assert result["episode_numbers"] == ["5"]  # Leading zeros removed

    def test_split_anthology_anthology_keywords(self):
        """Test split_anthology with anthology keywords."""
        orchestrator = FakePromptOrchestrator(confidence=0.90)

        media_file = Mock(spec=MediaFile)
        media_file.path = Path("/test/Show-Episode1 and Episode2.mp4")

        result = orchestrator.split_anthology(
            media_file=media_file, show_name="Test Show", season_number=1
        )

        # Should detect anthology pattern and return 2 episodes
        assert len(result["episode_numbers"]) == 2

    def test_extract_episode_titles_high_confidence(self):
        """Test extract_episode_titles_from_filename with high confidence."""
        orchestrator = FakePromptOrchestrator(confidence=0.90)

        result = orchestrator.extract_episode_titles_from_filename(
            filename="Show-S01E01-The Great Adventure.mp4",
            episode_titles=["The Great Adventure", "Another Episode", "The Adventure"],
        )

        assert len(result) > 0
        assert all("title" in item and "confidence" in item for item in result)
        # Should find "The Great Adventure" as exact match
        titles = [item["title"] for item in result]
        assert "The Great Adventure" in titles

    def test_extract_episode_titles_low_confidence(self):
        """Test extract_episode_titles_from_filename with low confidence."""
        orchestrator = FakePromptOrchestrator(confidence=0.30)

        result = orchestrator.extract_episode_titles_from_filename(
            filename="Show-S01E01-The Great Adventure.mp4",
            episode_titles=["The Great Adventure", "Another Episode"],
        )

        # Low confidence should return empty
        assert result == []

    def test_normalize_title_with_llm_high_confidence(self):
        """Test normalize_title_with_llm with high confidence."""
        orchestrator = FakePromptOrchestrator(confidence=0.90)

        result = orchestrator.normalize_title_with_llm(
            segment="great adventure",
            episode_titles=["The Great Adventure", "Another Episode"],
        )

        # Should match to official title
        assert result == "The Great Adventure"

    def test_normalize_title_with_llm_no_match(self):
        """Test normalize_title_with_llm with no good match."""
        orchestrator = FakePromptOrchestrator(confidence=0.90)

        result = orchestrator.normalize_title_with_llm(
            segment="completely different",
            episode_titles=["The Great Adventure", "Another Episode"],
        )

        # Should return original segment when no match
        assert result == "completely different"

    def test_llm_generate_variants_high_confidence(self):
        """Test llm_generate_variants with high confidence."""
        orchestrator = FakePromptOrchestrator(confidence=0.90)

        result = orchestrator.llm_generate_variants("The Great Adventure!")

        assert len(result) > 1  # Should generate multiple variants
        assert "The Great Adventure!" in result  # Original should be included
        assert "The Great Adventure" in result  # Without exclamation
        assert "The_Great_Adventure!" in result  # With underscores

    def test_llm_generate_variants_low_confidence(self):
        """Test llm_generate_variants with low confidence."""
        orchestrator = FakePromptOrchestrator(confidence=0.30)

        result = orchestrator.llm_generate_variants("The Great Adventure!")

        # Low confidence should only return original
        assert result == ["The Great Adventure!"]

    def test_llm_disambiguate_candidates_high_confidence(self):
        """Test llm_disambiguate_candidates with high confidence."""
        orchestrator = FakePromptOrchestrator(confidence=0.90)

        result = orchestrator.llm_disambiguate_candidates(
            filename="Show-The Great Adventure and Another Story.mp4",
            candidates=["The Great Adventure", "Another Story", "Different Episode"],
        )

        # Should find matching candidates
        assert "The Great Adventure" in result
        assert "Another Story" in result
        assert "Different Episode" not in result

    def test_llm_disambiguate_candidates_empty_input(self):
        """Test llm_disambiguate_candidates with empty candidates."""
        orchestrator = FakePromptOrchestrator(confidence=0.90)

        result = orchestrator.llm_disambiguate_candidates(
            filename="Show-Episode.mp4", candidates=[]
        )

        assert result == []


class TestStubLLMContextManager:
    """Test the stub_llm context manager."""

    def test_stub_llm_context_manager(self):
        """Test that stub_llm patches LLM functions correctly."""
        # Create a mock media file
        media_file = Mock(spec=MediaFile)
        media_file.path = Path("/test/Show-S01E01-Episode.mp4")

        # Test that the context manager patches the function
        with stub_llm(confidence=0.90) as fake_orchestrator:
            # Import the function inside the context manager to ensure patching works
            from namegnome.llm.prompt_orchestrator import split_anthology

            # This should use the fake implementation
            result = split_anthology(
                media_file=media_file, show_name="Test Show", season_number=1
            )

            # Verify it's using the fake implementation
            assert "episode_numbers" in result
            assert "episode_list" in result
            assert isinstance(fake_orchestrator, FakePromptOrchestrator)
            # The fake implementation should return at least one episode number for this filename
            assert len(result["episode_numbers"]) > 0

    def test_stub_llm_different_confidence_levels(self):
        """Test that different confidence levels produce different results."""
        from pathlib import Path

        # Create a proper MediaFile mock with a real Path object
        media_file = Mock(spec=MediaFile)
        media_file.path = Path("/test/Show-S01E01-E02-Episode.mp4")

        # Test the fake orchestrator directly first
        from tests.helpers.fake_prompt_orchestrator import FakePromptOrchestrator

        direct_orchestrator = FakePromptOrchestrator(confidence=0.90)
        direct_result = direct_orchestrator.split_anthology(media_file, "Show", 1)
        print(f"Direct fake orchestrator result: {direct_result}")

        # High confidence - import inside context manager to ensure patching works
        with stub_llm(confidence=0.90) as fake_orch:
            from namegnome.llm.prompt_orchestrator import split_anthology

            print(f"Fake orchestrator instance: {fake_orch}")
            print(f"Fake orchestrator confidence: {fake_orch.confidence}")
            high_result = split_anthology(media_file, "Show", 1)
            print(f"High confidence result: {high_result}")

        # Medium confidence (should reduce episodes)
        with stub_llm(confidence=0.50):
            from namegnome.llm.prompt_orchestrator import split_anthology

            medium_result = split_anthology(media_file, "Show", 1)
            print(f"Medium confidence result: {medium_result}")

        # Low confidence
        with stub_llm(confidence=0.30):
            from namegnome.llm.prompt_orchestrator import split_anthology

            low_result = split_anthology(media_file, "Show", 1)
            print(f"Low confidence result: {low_result}")

        # Results should be different - high should have most episodes, low should have fewest
        assert len(high_result["episode_numbers"]) >= len(
            medium_result["episode_numbers"]
        )
        assert len(medium_result["episode_numbers"]) >= len(
            low_result["episode_numbers"]
        )
        assert (
            len(high_result["episode_numbers"]) > 0
        )  # High confidence should find something


class TestGlobalFunctions:
    """Test the global helper functions."""

    def test_set_and_get_fake_confidence(self):
        """Test setting and getting global fake confidence."""
        original_confidence = get_fake_orchestrator().confidence

        try:
            set_fake_confidence(0.75)
            assert get_fake_orchestrator().confidence == 0.75

            set_fake_confidence(0.45)
            assert get_fake_orchestrator().confidence == 0.45
        finally:
            # Restore original confidence
            set_fake_confidence(original_confidence)

    def test_global_fake_functions(self):
        """Test that global fake functions work correctly."""
        from tests.helpers.fake_prompt_orchestrator import (
            split_anthology,
            extract_episode_titles_from_filename,
            normalize_title_with_llm,
            llm_generate_variants,
            llm_disambiguate_candidates,
        )

        # Create mock data
        media_file = Mock(spec=MediaFile)
        media_file.path = Path("/test/Show-S01E01-Episode.mp4")

        # Test all functions work without errors
        result1 = split_anthology(media_file, "Show", 1)
        assert "episode_numbers" in result1

        result2 = extract_episode_titles_from_filename("filename.mp4", ["Title"])
        assert isinstance(result2, list)

        result3 = normalize_title_with_llm("segment", ["Title"])
        assert isinstance(result3, str)

        result4 = llm_generate_variants("Title")
        assert isinstance(result4, list)

        result5 = llm_disambiguate_candidates("filename.mp4", ["Title"])
        assert isinstance(result5, list)


class TestDeterministicBehavior:
    """Test that the fake orchestrator is truly deterministic."""

    def test_repeated_calls_same_result(self):
        """Test that repeated calls with same input produce same output."""
        orchestrator = FakePromptOrchestrator(confidence=0.90)

        media_file = Mock(spec=MediaFile)
        media_file.path = Path("/test/Show-S01E01-E02-Episode.mp4")

        # Call multiple times
        result1 = orchestrator.split_anthology(media_file, "Show", 1)
        result2 = orchestrator.split_anthology(media_file, "Show", 1)
        result3 = orchestrator.split_anthology(media_file, "Show", 1)

        # All results should be identical
        assert result1 == result2 == result3

    def test_different_orchestrators_same_result(self):
        """Test that different orchestrator instances with same confidence produce same results."""
        media_file = Mock(spec=MediaFile)
        media_file.path = Path("/test/Show-S01E01-Episode.mp4")

        orchestrator1 = FakePromptOrchestrator(confidence=0.80)
        orchestrator2 = FakePromptOrchestrator(confidence=0.80)

        result1 = orchestrator1.split_anthology(media_file, "Show", 1)
        result2 = orchestrator2.split_anthology(media_file, "Show", 1)

        assert result1 == result2
