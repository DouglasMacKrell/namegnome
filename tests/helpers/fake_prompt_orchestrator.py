"""Deterministic LLM stub for regression testing.

This module provides a configurable, no-network replacement for the LLM functions
in prompt_orchestrator.py. It returns deterministic responses based on configurable
confidence levels and input patterns.
"""

import hashlib
import re
from contextlib import contextmanager
from typing import Generator, Optional
from unittest.mock import patch

import pytest

from namegnome.models.core import MediaFile


class FakePromptOrchestrator:
    """Deterministic LLM stub for regression testing.

    Provides configurable responses that simulate different confidence levels
    and LLM behaviors without making any network calls.
    """

    def __init__(self, confidence: float = 0.90):
        """Initialize the fake orchestrator with a confidence level.

        Args:
            confidence: Base confidence level (0.0 to 1.0)
                - >= 0.75: Returns "auto" quality responses
                - 0.40-0.74: Returns "manual" quality responses
                - < 0.40: Returns "unsupported" quality responses
        """
        self.confidence = confidence
        self._deterministic_seed = 42

    def _get_deterministic_hash(self, input_str: str) -> str:
        """Generate deterministic hash for consistent responses."""
        return hashlib.md5(
            f"{input_str}_{self._deterministic_seed}".encode()
        ).hexdigest()[:8]

    def split_anthology(
        self,
        media_file: MediaFile,
        show_name: str,
        season_number: int,
        model: Optional[str] = None,
        episode_list: Optional[list[dict[str, object]]] = None,
    ) -> dict[str, object]:
        """Fake implementation of split_anthology.

        Returns deterministic episode mappings based on filename patterns.
        """
        filename = str(media_file.path.name)

        # Extract episode numbers from filename patterns
        episode_numbers = []

        # Pattern 1: S01E01-E02 style spans
        span_match = re.search(r"S\d+E(\d+)[-–]E(\d+)", filename)
        if span_match:
            start_ep = int(span_match.group(1))
            end_ep = int(span_match.group(2))
            episode_numbers = [str(i) for i in range(start_ep, end_ep + 1)]

        # Pattern 2: Single episode S01E01
        elif re.search(r"S\d+E(\d+)", filename):
            ep_match = re.search(r"S\d+E(\d+)", filename)
            if ep_match:
                episode_numbers = [
                    str(int(ep_match.group(1)))
                ]  # Convert to int then str to remove leading zeros

        # Pattern 3: Multi-episode anthology files (assume 2 episodes)
        elif any(
            keyword in filename.lower() for keyword in ["and", "&", "plus", "with"]
        ):
            # For anthology files, assume 2 consecutive episodes
            base_ep = 1  # Default starting episode
            if episode_list and len(episode_list) >= 2:
                # Use first two episodes from episode list
                sorted_eps = sorted(
                    episode_list, key=lambda x: int(x.get("episode", 1))
                )
                episode_numbers = [
                    str(ep.get("episode", i + 1)) for i, ep in enumerate(sorted_eps[:2])
                ]
            else:
                episode_numbers = [str(base_ep), str(base_ep + 1)]

        # Fallback: single episode
        if not episode_numbers:
            episode_numbers = ["1"]

        # Adjust confidence based on pattern complexity
        if self.confidence >= 0.75:
            # High confidence - return clean episode numbers
            pass
        elif self.confidence >= 0.40:
            # Medium confidence - add some uncertainty
            if len(episode_numbers) > 1:
                # Sometimes only return first episode for manual review
                episode_numbers = episode_numbers[:1]
        else:
            # Low confidence - return empty for unsupported
            episode_numbers = []

        return {"episode_numbers": episode_numbers, "episode_list": episode_list}

    def extract_episode_titles_from_filename(
        self,
        filename: str,
        episode_titles: list[str],
        model: Optional[str] = None,
    ) -> list[dict[str, object]]:
        """Fake implementation of extract_episode_titles_from_filename.

        Returns deterministic title extractions with confidence scores.
        """
        results = []

        # Normalize filename for matching
        normalized_filename = filename.lower().replace("-", " ").replace("_", " ")

        for title in episode_titles:
            normalized_title = title.lower().replace("-", " ").replace("_", " ")

            # Simple substring matching with confidence adjustment
            if normalized_title in normalized_filename:
                confidence = self.confidence
                # Boost confidence for exact matches
                if title.lower() in filename.lower():
                    confidence = min(1.0, confidence + 0.1)

                results.append({"title": title, "confidence": confidence})
            elif any(
                word in normalized_filename
                for word in normalized_title.split()
                if len(word) > 3
            ):
                # Partial word matching with lower confidence
                confidence = max(0.3, self.confidence - 0.2)
                results.append({"title": title, "confidence": confidence})

        # Sort by confidence descending
        results.sort(key=lambda x: x["confidence"], reverse=True)

        # Apply confidence filtering
        if self.confidence >= 0.75:
            # High confidence - return top matches
            return results[:2]
        elif self.confidence >= 0.40:
            # Medium confidence - return fewer matches
            return results[:1]
        else:
            # Low confidence - return empty
            return []

    def normalize_title_with_llm(
        self, segment: str, episode_titles: list[str], model: Optional[str] = None
    ) -> str:
        """Fake implementation of normalize_title_with_llm.

        Returns deterministic title normalization.
        """
        if not episode_titles:
            return segment

        # Normalize segment for matching
        normalized_segment = segment.lower().replace("-", " ").replace("_", " ")

        # Find best match
        best_match = None
        best_score = 0

        for title in episode_titles:
            normalized_title = title.lower().replace("-", " ").replace("_", " ")

            # Simple scoring based on common words
            segment_words = set(normalized_segment.split())
            title_words = set(normalized_title.split())

            if segment_words & title_words:  # Any common words
                score = len(segment_words & title_words) / len(
                    segment_words | title_words
                )
                if score > best_score:
                    best_score = score
                    best_match = title

        # Apply confidence thresholds
        if self.confidence >= 0.75 and best_match and best_score > 0.3:
            return best_match
        elif self.confidence >= 0.40 and best_match and best_score > 0.5:
            return best_match
        else:
            # Low confidence or no good match - return segment
            return segment

    def llm_generate_variants(
        self, title: str, model: Optional[str] = None
    ) -> list[str]:
        """Fake implementation of llm_generate_variants.

        Returns deterministic filename variants.
        """
        variants = [title]  # Always include original

        if self.confidence >= 0.40:  # Only generate variants for reasonable confidence
            # Common transformations
            variants.extend(
                [
                    title.replace(" ", ""),  # Remove spaces
                    title.replace(" ", "_"),  # Underscores
                    title.replace(" ", "-"),  # Hyphens
                    title.replace(" and ", " & "),  # And to ampersand
                    title.replace("'", ""),  # Remove apostrophes
                    title.replace("!", ""),  # Remove exclamation marks
                    title.replace("?", ""),  # Remove question marks
                    title.replace(":", ""),  # Remove colons
                    title.replace(",", ""),  # Remove commas
                ]
            )

            # Remove duplicates while preserving order
            seen = set()
            unique_variants = []
            for variant in variants:
                if variant not in seen:
                    seen.add(variant)
                    unique_variants.append(variant)
            variants = unique_variants

        return variants[:5]  # Limit to 5 variants

    def llm_disambiguate_candidates(
        self, filename: str, candidates: list[str], model: Optional[str] = None
    ) -> list[str]:
        """Fake implementation of llm_disambiguate_candidates.

        Returns deterministic candidate selection.
        """
        if not candidates:
            return []

        # Normalize filename for matching
        normalized_filename = filename.lower().replace("-", " ").replace("_", " ")

        selected = []

        for candidate in candidates:
            normalized_candidate = candidate.lower().replace("-", " ").replace("_", " ")

            # Simple matching logic
            if normalized_candidate in normalized_filename:
                selected.append(candidate)
            elif any(
                word in normalized_filename
                for word in normalized_candidate.split()
                if len(word) > 3
            ):
                # Partial word matching
                if self.confidence >= 0.60:  # Only for decent confidence
                    selected.append(candidate)

        # Apply confidence-based filtering
        if self.confidence >= 0.75:
            # High confidence - return all matches
            return selected
        elif self.confidence >= 0.40:
            # Medium confidence - return fewer matches
            return selected[:2]
        else:
            # Low confidence - return first candidate or empty
            return candidates[:1] if candidates else []


# Global instance for easy access
_fake_orchestrator = FakePromptOrchestrator()


def set_fake_confidence(confidence: float) -> None:
    """Set the global fake orchestrator confidence level."""
    global _fake_orchestrator
    _fake_orchestrator.confidence = confidence


def get_fake_orchestrator() -> FakePromptOrchestrator:
    """Get the global fake orchestrator instance."""
    return _fake_orchestrator


# Monkey-patch functions that can be used directly
def split_anthology(
    media_file: MediaFile,
    show_name: str,
    season_number: int,
    model: Optional[str] = None,
    episode_list: Optional[list[dict[str, object]]] = None,
) -> dict[str, object]:
    """Fake split_anthology function."""
    return _fake_orchestrator.split_anthology(
        media_file, show_name, season_number, model, episode_list
    )


def extract_episode_titles_from_filename(
    filename: str,
    episode_titles: list[str],
    model: Optional[str] = None,
) -> list[dict[str, object]]:
    """Fake extract_episode_titles_from_filename function."""
    return _fake_orchestrator.extract_episode_titles_from_filename(
        filename, episode_titles, model
    )


def normalize_title_with_llm(
    segment: str, episode_titles: list[str], model: Optional[str] = None
) -> str:
    """Fake normalize_title_with_llm function."""
    return _fake_orchestrator.normalize_title_with_llm(segment, episode_titles, model)


def llm_generate_variants(title: str, model: Optional[str] = None) -> list[str]:
    """Fake llm_generate_variants function."""
    return _fake_orchestrator.llm_generate_variants(title, model)


def llm_disambiguate_candidates(
    filename: str, candidates: list[str], model: Optional[str] = None
) -> list[str]:
    """Fake llm_disambiguate_candidates function."""
    return _fake_orchestrator.llm_disambiguate_candidates(filename, candidates, model)


# Pytest fixtures and context managers


@contextmanager
def stub_llm(confidence: float = 0.90) -> Generator[FakePromptOrchestrator, None, None]:
    """Context manager to temporarily replace LLM functions with fake ones.

    Args:
        confidence: Confidence level for the fake LLM (0.0 to 1.0)

    Yields:
        FakePromptOrchestrator instance for further configuration

    Example:
        with stub_llm(confidence=0.50) as fake_llm:
            # All LLM calls will use the fake implementation
            result = split_anthology(media_file, "Show", 1)
    """
    fake_orchestrator = FakePromptOrchestrator(confidence)

    # Create the fake functions bound to this instance
    def fake_split_anthology(*args, **kwargs):
        print(f"fake_split_anthology called with args: {args}, kwargs: {kwargs}")
        result = fake_orchestrator.split_anthology(*args, **kwargs)
        print(f"fake_split_anthology returning: {result}")
        return result

    def fake_extract_titles(*args, **kwargs):
        return fake_orchestrator.extract_episode_titles_from_filename(*args, **kwargs)

    def fake_normalize_title(*args, **kwargs):
        return fake_orchestrator.normalize_title_with_llm(*args, **kwargs)

    def fake_generate_variants(*args, **kwargs):
        return fake_orchestrator.llm_generate_variants(*args, **kwargs)

    def fake_disambiguate(*args, **kwargs):
        return fake_orchestrator.llm_disambiguate_candidates(*args, **kwargs)

    # Patch all the LLM functions
    with (
        patch(
            "namegnome.llm.prompt_orchestrator.split_anthology", fake_split_anthology
        ),
        patch(
            "namegnome.llm.prompt_orchestrator.extract_episode_titles_from_filename",
            fake_extract_titles,
        ),
        patch(
            "namegnome.llm.prompt_orchestrator.normalize_title_with_llm",
            fake_normalize_title,
        ),
        patch(
            "namegnome.llm.prompt_orchestrator.llm_generate_variants",
            fake_generate_variants,
        ),
        patch(
            "namegnome.llm.prompt_orchestrator.llm_disambiguate_candidates",
            fake_disambiguate,
        ),
    ):
        yield fake_orchestrator


@pytest.fixture
def stub_llm_fixture():
    """Pytest fixture to replace LLM functions with fake ones.

    Returns a context manager that can be used with different confidence levels.

    Example:
        def test_something(stub_llm_fixture):
            with stub_llm_fixture(confidence=0.90) as fake_llm:
                # Test with high confidence
                pass

            with stub_llm_fixture(confidence=0.50) as fake_llm:
                # Test with medium confidence
                pass
    """
    return stub_llm


@pytest.fixture
def stub_llm_auto():
    """Pytest fixture for high-confidence LLM stub (auto mode).

    Automatically patches LLM functions with confidence=0.90 for the test duration.
    """
    with stub_llm(confidence=0.90) as fake_orchestrator:
        yield fake_orchestrator


@pytest.fixture
def stub_llm_manual():
    """Pytest fixture for medium-confidence LLM stub (manual mode).

    Automatically patches LLM functions with confidence=0.50 for the test duration.
    """
    with stub_llm(confidence=0.50) as fake_orchestrator:
        yield fake_orchestrator


@pytest.fixture
def stub_llm_unsupported():
    """Pytest fixture for low-confidence LLM stub (unsupported mode).

    Automatically patches LLM functions with confidence=0.30 for the test duration.
    """
    with stub_llm(confidence=0.30) as fake_orchestrator:
        yield fake_orchestrator
