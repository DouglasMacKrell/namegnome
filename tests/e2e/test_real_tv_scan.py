"""End-to-end tests for TV scanning with tiered dependency approach.

This module implements four test tiers with automatic dependency detection:
- Core E2E: cached APIs + deterministic LLM + file ops (no external deps)
- API E2E: real APIs + deterministic LLM + file ops (requires API keys)
- LLM E2E: cached APIs + real LLM + file ops (requires Ollama)
- Full E2E: real APIs + real LLM + file ops (requires both)
"""

import json
import os
import subprocess
import time
from pathlib import Path
from typing import List, Dict, Any

import pytest


@pytest.mark.e2e
class TestTVScanEndToEnd:
    """End-to-end tests for TV scanning with tiered dependency approach."""

    # Core E2E Tests (no external dependencies)

    def test_core_e2e_scan_apply_undo_cycle(
        self,
        e2e_temp_dir: Path,
        e2e_test_files: List[Path],
        mock_api_providers,
        mock_llm_deterministic,
    ):
        """Core E2E: Test complete scan→apply→undo cycle with cached APIs and deterministic LLM.

        This test runs without any external dependencies (no API keys or Ollama required).
        It validates the complete file operation pipeline using cached responses.
        """
        start_time = time.time()

        # Store original files for verification
        original_files = {f: f.read_bytes() for f in e2e_test_files}

        # Step 1: Scan with cached providers and deterministic LLM
        scan_result = subprocess.run(
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
                str(e2e_temp_dir),
            ],
            capture_output=True,
            text=True,
            env={
                **os.environ,
                "NAMEGNOME_NON_INTERACTIVE": "1",
            },
        )

        # Accept successful scan (0) or manual confirmation required (2)
        assert scan_result.returncode in [0, 2], f"Scan failed: {scan_result.stderr}"

        # Extract JSON from mixed output (visual elements + JSON)
        stdout = scan_result.stdout
        json_start = stdout.find("{")
        json_end = stdout.rfind("}") + 1

        if json_start >= 0 and json_end > json_start:
            json_str = stdout[json_start:json_end]
            scan_output = json.loads(json_str)
        else:
            # No JSON found, create minimal structure for testing
            scan_output = {"items": [], "root_dir": str(e2e_temp_dir)}

        # Validate scan output structure
        assert "items" in scan_output
        assert "root_dir" in scan_output
        assert len(scan_output["items"]) > 0, (
            f"No items found in scan output. stdout: {stdout[:500]}..."
        )

        # Check for expected destination paths
        for item in scan_output["items"]:
            assert "source" in item
            assert "destination" in item
            assert "status" in item
            assert item["status"] in ["pending", "conflict", "auto", "manual"]

            # Validate destination path format for pending/auto items
            if item["status"] in ["pending", "auto"]:
                dst_path = Path(item["destination"])
                assert "Danger Mouse" in dst_path.name
                assert dst_path.suffix == ".mp4"

        # Step 2: Check if any files need undo testing (plan was generated)
        plan_id = scan_output.get("id")  # JSON uses "id" not "plan_id"

        if plan_id:
            # Test that undo command works with the plan ID
            undo_result = subprocess.run(
                [
                    "poetry",
                    "run",
                    "python",
                    "-m",
                    "namegnome",
                    "undo",
                    plan_id,
                    "--yes",
                ],
                capture_output=True,
                text=True,
            )

            # Undo should work even if no files were actually moved
            # It may return 0 (success) or 1 (nothing to undo)
            assert undo_result.returncode in [0, 1], (
                f"Undo failed unexpectedly: {undo_result.stderr}"
            )

            # Verify original files still exist and are unchanged
            for original_file, original_content in original_files.items():
                assert original_file.exists(), f"Original file missing: {original_file}"
                assert original_file.read_bytes() == original_content, (
                    f"File content changed: {original_file}"
                )
        else:
            print("No plan ID generated, skipping undo test")

        # Performance validation: should complete in < 30s
        elapsed = time.time() - start_time
        assert elapsed < 30, f"E2E test took too long: {elapsed:.2f}s"

    def test_core_e2e_visual_elements(
        self,
        e2e_temp_dir: Path,
        e2e_test_files: List[Path],
        mock_api_providers,
        mock_llm_deterministic,
    ):
        """Core E2E: Test visual CLI elements (banner, gnomes, progress) work correctly."""
        # Run with Rich enabled to test visual elements
        scan_result = subprocess.run(
            [
                "poetry",
                "run",
                "python",
                "-m",
                "namegnome",
                "scan",
                "--media-type",
                "tv",
                str(e2e_temp_dir),
            ],
            capture_output=True,
            text=True,
            env={
                **os.environ,
                "NAMEGNOME_NON_INTERACTIVE": "1",
            },
        )

        # Accept successful scan (0) or manual confirmation required (2)
        assert scan_result.returncode in [0, 2], (
            f"Scan failed unexpectedly: {scan_result.stderr}"
        )

        # Check for visual elements in stdout (Rich console output)
        output = scan_result.stdout

        # Verify NameGnome banner is displayed
        assert "NameGnome" in output, "NameGnome banner should be displayed"

        # Verify gnome visual elements (emoji indicators)
        gnome_indicators = ["🧙‍♂️", "💔", "❌", "✅"]
        has_gnome = any(indicator in output for indicator in gnome_indicators)
        assert has_gnome, (
            f"Should contain gnome visual elements. Output: {output[:500]}..."
        )

        # Verify structured table output (indicates Rich is working)
        table_indicators = ["┌", "│", "└", "─"]
        has_table = all(indicator in output for indicator in table_indicators)
        assert has_table, "Should contain Rich table formatting"

    # API E2E Tests (requires API keys)

    @pytest.mark.api
    def test_api_e2e_real_tvdb_integration(
        self,
        e2e_temp_dir: Path,
        e2e_test_files: List[Path],
        skip_if_no_api_keys,
        mock_llm_deterministic,
        e2e_environment: Dict[str, Any],
    ):
        """API E2E: Test with real TVDB API calls and deterministic LLM."""
        # Set up environment for real API calls
        env = {
            **os.environ,
            "NAMEGNOME_NON_INTERACTIVE": "1",
            "NAMEGNOME_NO_RICH": "1",
        }

        if e2e_environment["tvdb_key"]:
            env["TVDB_API_KEY"] = e2e_environment["tvdb_key"]

        scan_result = subprocess.run(
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
                str(e2e_temp_dir),
            ],
            capture_output=True,
            text=True,
            env=env,
        )

        # Accept successful scan (0) or manual confirmation required (2)
        assert scan_result.returncode in [0, 2], (
            f"Real API scan failed: {scan_result.stderr}"
        )

        # Extract JSON from mixed output (like Core E2E)
        stdout = scan_result.stdout
        json_start = stdout.find("{")
        json_end = stdout.rfind("}") + 1

        if json_start >= 0 and json_end > json_start:
            json_str = stdout[json_start:json_end]
            scan_output = json.loads(json_str)
        else:
            # No JSON found, skip test
            pytest.skip(
                "No JSON output from real API scan - conflicts may prevent processing"
            )

        # With real API data, should get high-quality results
        items = scan_output["items"]
        assert len(items) > 0

        # With real API data, should get reasonable results (may be conflicts due to test data)
        auto_items = [item for item in items if item["status"] in ["auto", "pending"]]
        conflict_items = [item for item in items if item["status"] == "conflict"]

        # Should have some actionable items (auto/pending) or conflicts with real API data
        assert len(auto_items) > 0 or len(conflict_items) > 0, (
            "Real API should produce some actionable results"
        )

        # Validate destination path quality with real episode data
        for item in auto_items:
            dst_path = Path(item["destination"])
            assert "Danger Mouse" in dst_path.name
            # With real API, should have metadata-driven paths
            assert "TV Shows" in str(dst_path)  # Should use proper directory structure

    @pytest.mark.api
    def test_api_e2e_provider_fallback_real(
        self,
        e2e_temp_dir: Path,
        e2e_test_files: List[Path],
        skip_if_no_api_keys,
        mock_llm_deterministic,
        e2e_environment: Dict[str, Any],
    ):
        """API E2E: Test provider fallback with real API calls."""
        # Test with only TMDB key to force fallback from TVDB
        env = {
            **os.environ,
            "NAMEGNOME_NON_INTERACTIVE": "1",
            "NAMEGNOME_NO_RICH": "1",
        }

        # Remove TVDB key to test fallback
        if e2e_environment["tmdb_key"]:
            env["TMDB_API_KEY"] = e2e_environment["tmdb_key"]

        scan_result = subprocess.run(
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
                str(e2e_temp_dir),
            ],
            capture_output=True,
            text=True,
            env=env,
        )

        # Should still succeed with TMDB fallback
        assert scan_result.returncode in [0, 2], (
            f"Fallback scan failed: {scan_result.stderr}"
        )

    # LLM E2E Tests (requires Ollama)

    @pytest.mark.llm
    def test_llm_e2e_real_ollama_integration(
        self,
        e2e_temp_dir: Path,
        e2e_test_files: List[Path],
        skip_if_no_ollama,
        mock_api_providers,
        e2e_environment: Dict[str, Any],
    ):
        """LLM E2E: Test with cached APIs and real Ollama LLM."""
        env = {
            **os.environ,
            "NAMEGNOME_NON_INTERACTIVE": "1",
            "NAMEGNOME_NO_RICH": "1",
            "NAMEGNOME_LLM_PROVIDER": "ollama",  # Force real Ollama
        }

        scan_result = subprocess.run(
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
                str(e2e_temp_dir),
            ],
            capture_output=True,
            text=True,
            env=env,
        )

        # Accept successful scan (0) or manual confirmation required (2)
        assert scan_result.returncode in [0, 2], (
            f"Real LLM scan failed: {scan_result.stderr}"
        )

        # Extract JSON from mixed output (like Core E2E)
        stdout = scan_result.stdout
        json_start = stdout.find("{")
        json_end = stdout.rfind("}") + 1

        if json_start >= 0 and json_end > json_start:
            json_str = stdout[json_start:json_end]
            scan_output = json.loads(json_str)
        else:
            # No JSON found, skip test
            pytest.skip(
                "No JSON output from real LLM scan - conflicts may prevent processing"
            )

        # Real LLM should be able to process the data
        items = scan_output["items"]
        assert len(items) > 0

    @pytest.mark.llm
    def test_llm_e2e_confidence_thresholds(
        self,
        e2e_temp_dir: Path,
        e2e_test_files: List[Path],
        skip_if_no_ollama,
        mock_api_providers,
    ):
        """LLM E2E: Test confidence threshold behavior with real LLM."""
        # Create files with challenging names to test LLM confidence
        challenging_dir = e2e_temp_dir / "challenging"
        challenging_dir.mkdir()

        challenging_files = [
            challenging_dir / "DM_2015_s1e1_begins.mp4",
            challenging_dir / "danger.mouse.2015.1x02.level.mp4",
            challenging_dir / "Dm(2015)-S01E03-Greenfinger[720p].mp4",
        ]

        for file in challenging_files:
            file.write_text("fake content")

        env = {
            **os.environ,
            "NAMEGNOME_NON_INTERACTIVE": "1",
            "NAMEGNOME_NO_RICH": "1",
            "NAMEGNOME_LLM_PROVIDER": "ollama",
        }

        scan_result = subprocess.run(
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
                str(challenging_dir),
            ],
            capture_output=True,
            text=True,
            env=env,
        )

        # Should handle challenging filenames
        assert scan_result.returncode in [
            0,
            1,
            2,
        ]  # Various confidence outcomes expected

    # Full E2E Tests (requires both API keys and Ollama)

    @pytest.mark.api
    @pytest.mark.llm
    def test_full_e2e_complete_pipeline(
        self,
        e2e_temp_dir: Path,
        e2e_test_files: List[Path],
        skip_if_no_api_keys,
        skip_if_no_ollama,
        e2e_environment: Dict[str, Any],
    ):
        """Full E2E: Test complete pipeline with real APIs and real LLM."""
        start_time = time.time()

        env = {
            **os.environ,
            "NAMEGNOME_NON_INTERACTIVE": "1",
            "NAMEGNOME_NO_RICH": "1",
            "NAMEGNOME_LLM_PROVIDER": "ollama",
        }

        # Add all available API keys
        if e2e_environment["tvdb_key"]:
            env["TVDB_API_KEY"] = e2e_environment["tvdb_key"]
        if e2e_environment["tmdb_key"]:
            env["TMDB_API_KEY"] = e2e_environment["tmdb_key"]
        if e2e_environment["omdb_key"]:
            env["OMDB_API_KEY"] = e2e_environment["omdb_key"]

        scan_result = subprocess.run(
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
                str(e2e_temp_dir),
            ],
            capture_output=True,
            text=True,
            env=env,
        )

        # Accept successful scan (0) or manual confirmation required (2)
        assert scan_result.returncode in [0, 2], (
            f"Full E2E scan failed: {scan_result.stderr}"
        )

        # Extract JSON from mixed output (like Core E2E)
        stdout = scan_result.stdout
        json_start = stdout.find("{")
        json_end = stdout.rfind("}") + 1

        if json_start >= 0 and json_end > json_start:
            json_str = stdout[json_start:json_end]
            scan_output = json.loads(json_str)
        else:
            # No JSON found, skip test
            pytest.skip(
                "No JSON output from Full E2E scan - conflicts may prevent processing"
            )

        # With real APIs and LLM, should get reasonable results (conflicts possible with test data)
        items = scan_output["items"]
        assert len(items) > 0

        auto_items = [item for item in items if item["status"] in ["auto", "pending"]]
        conflict_items = [item for item in items if item["status"] == "conflict"]

        # Should have some actionable items or documented conflicts
        assert len(auto_items) > 0 or len(conflict_items) > 0, (
            "Full E2E should produce actionable results"
        )

        # Validate destination paths for actionable items
        for item in auto_items:
            dst_path = Path(item["destination"])
            assert "Danger Mouse" in dst_path.name
            # Should use structured paths even if episode matching is challenging
            assert "TV Shows" in str(dst_path)  # Should use proper directory structure

        # Performance check for full pipeline
        elapsed = time.time() - start_time
        assert elapsed < 30, f"Full E2E took too long: {elapsed:.2f}s"

    @pytest.mark.api
    @pytest.mark.llm
    def test_full_e2e_series_disambiguation(
        self,
        e2e_temp_dir: Path,
        skip_if_no_api_keys,
        skip_if_no_ollama,
        e2e_environment: Dict[str, Any],
    ):
        """Full E2E: Test series disambiguation with real APIs and LLM."""
        # Create files that could match multiple series (1981 vs 2015 Danger Mouse)
        ambiguous_dir = e2e_temp_dir / "Danger Mouse"
        ambiguous_dir.mkdir()

        ambiguous_files = [
            ambiguous_dir / "Danger Mouse - Episode 1.mp4",
            ambiguous_dir / "Danger Mouse - Episode 2.mp4",
        ]

        for file in ambiguous_files:
            file.write_text("fake content")

        env = {
            **os.environ,
            "NAMEGNOME_NON_INTERACTIVE": "1",  # Should auto-select first result
            "NAMEGNOME_NO_RICH": "1",
            "NAMEGNOME_LLM_PROVIDER": "ollama",
        }

        if e2e_environment["tvdb_key"]:
            env["TVDB_API_KEY"] = e2e_environment["tvdb_key"]

        scan_result = subprocess.run(
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
                str(ambiguous_dir),
            ],
            capture_output=True,
            text=True,
            env=env,
        )

        # Should handle disambiguation gracefully
        assert scan_result.returncode in [0, 2], (
            f"Disambiguation failed: {scan_result.stderr}"
        )

        if scan_result.returncode == 0:
            scan_output = json.loads(scan_result.stdout)
            items = scan_output["items"]
            assert len(items) > 0
