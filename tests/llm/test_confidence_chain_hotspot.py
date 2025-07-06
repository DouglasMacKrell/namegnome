"""Tests for LLM confidence chain and manual fallback logic.

Tests the confidence thresholds and routing logic:
- ≥0.75 → auto (PlanStatus.PENDING)
- 0.40-0.74 → manual (PlanStatus.MANUAL)
- <0.40 → unsupported/failed

This module tests the complete confidence chain from LLM response through
plan item status assignment.
"""

import pytest
from pathlib import Path
from unittest.mock import AsyncMock, patch, Mock

from namegnome.models.core import MediaFile, MediaType, PlanStatus
from namegnome.llm.prompt_orchestrator import (
    split_anthology,
    extract_episode_titles_from_filename,
)


class TestConfidenceThresholds:
    """Test that LLM functions return confidence scores and route correctly."""

    def test_split_anthology_returns_confidence_scores(self):
        """Test that split_anthology returns confidence scores for routing decisions."""
        media_file = Mock(spec=MediaFile)
        media_file.path = Path("/test/Show-S01E01-E02-Two Episodes.mp4")

        with patch("namegnome.llm.ollama_client.generate") as mock_generate:
            # Mock LLM response with confidence
            mock_generate.return_value = AsyncMock(
                return_value='{"Show-S01E01-E02-Two Episodes.mp4": {"episodes": [1, 2], "confidence": 0.85}}'
            )

            result = split_anthology(media_file, "Show", 1)

            # Should return confidence score for routing
            assert "confidence" in result, (
                "split_anthology should return confidence scores"
            )
            assert isinstance(result["confidence"], float), (
                "Confidence should be a float"
            )
            assert 0.0 <= result["confidence"] <= 1.0, (
                "Confidence should be between 0 and 1"
            )

    def test_extract_episode_titles_returns_confidence(self):
        """Test that extract_episode_titles_from_filename returns confidence scores."""
        with patch("namegnome.llm.ollama_client.generate") as mock_generate:
            # Mock LLM response with confidence
            mock_generate.return_value = AsyncMock(
                return_value='[{"title": "Episode One", "confidence": 0.90}, {"title": "Episode Two", "confidence": 0.75}]'
            )

            result = extract_episode_titles_from_filename(
                "Show-S01E01-Episode One Episode Two.mp4",
                ["Episode One", "Episode Two", "Different Episode"],
            )

            # Should return list of dicts with confidence
            assert isinstance(result, list), "Should return list of extracted titles"
            for item in result:
                assert "confidence" in item, (
                    "Each extracted title should have confidence"
                )
                assert isinstance(item["confidence"], float), (
                    "Confidence should be float"
                )

    @pytest.mark.parametrize(
        "confidence,expected_status",
        [
            (0.85, PlanStatus.PENDING),  # ≥0.75 → auto
            (0.60, PlanStatus.MANUAL),  # 0.40-0.74 → manual
            (0.30, PlanStatus.FAILED),  # <0.40 → unsupported/failed
        ],
    )
    def test_confidence_routing_to_plan_status(self, confidence, expected_status):
        """Test that confidence scores are properly routed to plan item status."""
        # This test will fail initially because the routing logic doesn't exist
        from namegnome.core.planner import route_confidence_to_status

        status = route_confidence_to_status(confidence)
        assert status == expected_status, (
            f"Confidence {confidence} should route to {expected_status}"
        )

    def test_confidence_threshold_constants_are_consistent(self):
        """Test that confidence thresholds are consistently defined."""
        from namegnome.core.planner import (
            LLM_CONFIDENCE_AUTO_THRESHOLD,
            LLM_CONFIDENCE_MANUAL_THRESHOLD,
        )

        # Should match documented thresholds in SCAN_RULES.md
        assert LLM_CONFIDENCE_AUTO_THRESHOLD == 0.75, (
            "LLM_CONFIDENCE_AUTO_THRESHOLD should be 0.75 per SCAN_RULES.md"
        )
        assert LLM_CONFIDENCE_MANUAL_THRESHOLD == 0.40, (
            "LLM_CONFIDENCE_MANUAL_THRESHOLD should be 0.40 per SCAN_RULES.md"
        )


class TestConfidenceChainIntegration:
    """Test the complete confidence chain from LLM through plan item creation."""

    def test_high_confidence_creates_auto_plan_items(self):
        """Test that high confidence LLM responses create auto plan items."""
        media_file = Mock(spec=MediaFile)
        media_file.path = Path("/test/Show-S01E01-Episode.mp4")
        media_file.media_type = MediaType.TV
        media_file.title = "Show"
        media_file.season = 1
        media_file.episode = 1
        media_file.episode_title = "Episode"
        media_file.year = None
        media_file.size = 1000
        media_file.modified_date = Mock()
        media_file.hash = None
        media_file.metadata_ids = {}

        with patch("namegnome.llm.prompt_orchestrator.split_anthology") as mock_split:
            mock_split.return_value = {
                "episode_numbers": ["1"],
                "confidence": 0.90,  # High confidence
                "episode_list": [],
            }

            # Test the actual planning pipeline
            from namegnome.core.tv.plan_orchestration import create_tv_rename_plan
            from namegnome.core.tv.tv_plan_context import TVRenamePlanBuildContext
            from namegnome.models.core import ScanResult
            from namegnome.rules.plex import PlexRuleSet

            scan_result = ScanResult(
                files=[media_file],
                root_dir=Path("/test"),
                media_types=[MediaType.TV],
                platform="plex",
            )

            ctx = TVRenamePlanBuildContext(
                scan_result=scan_result,
                rule_set=PlexRuleSet(),
                plan_id="test_plan",
                platform="plex",
            )

            plan = create_tv_rename_plan(ctx)

            # Should create auto plan item (not manual)
            assert len(plan.items) > 0, "Should create plan items"
            for item in plan.items:
                if item.media_file.path == media_file.path:
                    assert item.status != PlanStatus.MANUAL, (
                        "High confidence should not create manual items"
                    )
                    assert not item.manual, "High confidence should not set manual flag"

    def test_medium_confidence_creates_manual_plan_items(self):
        """Test that medium confidence LLM responses create manual plan items."""
        media_file = Mock(spec=MediaFile)
        media_file.path = Path("/test/Show-S01E01-Episode.mp4")
        media_file.media_type = MediaType.TV
        media_file.title = "Show"
        media_file.season = 1
        media_file.episode = 1
        media_file.episode_title = "Episode"
        media_file.year = None
        media_file.size = 1000
        media_file.modified_date = Mock()
        media_file.hash = None
        media_file.metadata_ids = {}

        with (
            patch("namegnome.llm.prompt_orchestrator.split_anthology") as mock_split1,
            patch(
                "namegnome.core.tv.anthology.tv_anthology_split.split_anthology",
                create=True,
            ) as mock_split2,
        ):
            mock_result = {
                "episode_numbers": ["1"],
                "confidence": 0.60,  # Medium confidence
                "episode_list": [],
            }
            mock_split1.return_value = mock_result
            mock_split2.return_value = mock_result

            # Test the actual planning pipeline
            from namegnome.core.tv.plan_orchestration import create_tv_rename_plan
            from namegnome.core.tv.tv_plan_context import TVRenamePlanBuildContext
            from namegnome.models.core import ScanResult
            from namegnome.rules.plex import PlexRuleSet

            scan_result = ScanResult(
                files=[media_file],
                root_dir=Path("/test"),
                media_types=[MediaType.TV],
                platform="plex",
            )

            ctx = TVRenamePlanBuildContext(
                scan_result=scan_result,
                rule_set=PlexRuleSet(),
                plan_id="test_plan",
                platform="plex",
            )

            plan = create_tv_rename_plan(ctx)

            # Should create manual plan item
            assert len(plan.items) > 0, "Should create plan items"
            for item in plan.items:
                if item.media_file.path == media_file.path:
                    assert item.status == PlanStatus.MANUAL, (
                        "Medium confidence should create manual items"
                    )
                    assert item.manual, "Medium confidence should set manual flag"
                    assert "confidence" in item.manual_reason, (
                        "Manual reason should mention confidence"
                    )

    def test_low_confidence_creates_failed_plan_items(self):
        """Test that low confidence LLM responses create failed/unsupported plan items."""
        media_file = Mock(spec=MediaFile)
        media_file.path = Path("/test/Show-S01E01-Episode.mp4")
        media_file.media_type = MediaType.TV
        media_file.title = "Show"
        media_file.season = 1
        media_file.episode = 1
        media_file.episode_title = "Episode"
        media_file.year = None
        media_file.size = 1000
        media_file.modified_date = Mock()
        media_file.hash = None
        media_file.metadata_ids = {}

        with patch("namegnome.llm.prompt_orchestrator.split_anthology") as mock_split:
            mock_split.return_value = {
                "episode_numbers": [],
                "confidence": 0.25,  # Low confidence
                "episode_list": [],
            }

            # Test the actual planning pipeline
            from namegnome.core.tv.plan_orchestration import create_tv_rename_plan
            from namegnome.core.tv.tv_plan_context import TVRenamePlanBuildContext
            from namegnome.models.core import ScanResult
            from namegnome.rules.plex import PlexRuleSet

            scan_result = ScanResult(
                files=[media_file],
                root_dir=Path("/test"),
                media_types=[MediaType.TV],
                platform="plex",
            )

            ctx = TVRenamePlanBuildContext(
                scan_result=scan_result,
                rule_set=PlexRuleSet(),
                plan_id="test_plan",
                platform="plex",
            )

            plan = create_tv_rename_plan(ctx)

            # Should create failed/unsupported plan item
            assert len(plan.items) > 0, "Should create plan items"
            for item in plan.items:
                if item.media_file.path == media_file.path:
                    assert item.status in [PlanStatus.FAILED, PlanStatus.MANUAL], (
                        "Low confidence should create failed/manual items"
                    )
                    if item.manual_reason:
                        assert (
                            "confidence" in item.manual_reason
                            or "No confident match" in item.manual_reason
                        )


class TestLLMFallbackChain:
    """Test the complete fallback chain: provider → LLM → manual."""

    def test_provider_success_skips_llm(self):
        """Test that successful provider data skips LLM processing."""
        # This tests the provider → LLM fallback logic
        pass  # Will implement after fixing core confidence issues

    def test_provider_failure_triggers_llm(self):
        """Test that provider failure triggers LLM fallback."""
        # This tests the provider → LLM fallback logic
        pass  # Will implement after fixing core confidence issues

    def test_llm_failure_triggers_manual(self):
        """Test that LLM failure triggers manual fallback."""
        media_file = Mock(spec=MediaFile)
        media_file.path = Path("/test/Show-S01E01-Episode.mp4")
        media_file.media_type = MediaType.TV
        media_file.title = "Show"
        media_file.season = 1
        media_file.episode = 1
        media_file.episode_title = "Episode"
        media_file.year = None
        media_file.size = 1000
        media_file.modified_date = Mock()
        media_file.hash = None
        media_file.metadata_ids = {}

        with patch("namegnome.llm.prompt_orchestrator.split_anthology") as mock_split:
            # Simulate LLM failure
            mock_split.side_effect = RuntimeError("LLM call failed")

            # Test that the planning pipeline handles LLM failures gracefully
            from namegnome.core.tv.plan_orchestration import create_tv_rename_plan
            from namegnome.core.tv.tv_plan_context import TVRenamePlanBuildContext
            from namegnome.models.core import ScanResult
            from namegnome.rules.plex import PlexRuleSet

            scan_result = ScanResult(
                files=[media_file],
                root_dir=Path("/test"),
                media_types=[MediaType.TV],
                platform="plex",
            )

            ctx = TVRenamePlanBuildContext(
                scan_result=scan_result,
                rule_set=PlexRuleSet(),
                plan_id="test_plan",
                platform="plex",
            )

            plan = create_tv_rename_plan(ctx)

            # Should handle gracefully and create manual items
            assert len(plan.items) > 0, "Should create plan items even on LLM failure"
            for item in plan.items:
                if item.media_file.path == media_file.path:
                    assert item.manual, "LLM failure should trigger manual fallback"
                    assert (
                        "LLM" in item.manual_reason
                        or "No confident match" in item.manual_reason
                    )


class TestConfidenceLogging:
    """Test that confidence decision points are properly logged."""

    def test_confidence_decisions_are_logged(self):
        """Test that confidence decisions are logged for debugging."""
        # This will test the logging requirement from Sprint 1.7.3
        pass  # Will implement after core fixes
