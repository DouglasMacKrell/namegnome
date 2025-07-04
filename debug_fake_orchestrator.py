from unittest.mock import Mock
from pathlib import Path
from tests.helpers.fake_prompt_orchestrator import FakePromptOrchestrator
from namegnome.models.core import MediaFile

# Create a mock MediaFile
media_file = Mock(spec=MediaFile)
media_file.path = Path("/test/Show-S01E01-E02-Episode.mp4")

# Test with different confidence levels
for confidence in [0.90, 0.50, 0.30]:
    orchestrator = FakePromptOrchestrator(confidence=confidence)
    result = orchestrator.split_anthology(
        media_file=media_file, show_name="Test Show", season_number=1
    )
    print(f"Confidence {confidence}: {result['episode_numbers']}")
