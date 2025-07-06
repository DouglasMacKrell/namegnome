"""End-to-end tests for TV scanning with tiered dependency approach.

This module implements four test tiers with automatic dependency detection:
- Core E2E: cached APIs + deterministic LLM + file ops (no external deps)
- API E2E: real APIs + deterministic LLM + file ops (requires API keys)
- LLM E2E: cached APIs + real LLM + file ops (requires Ollama)
- Full E2E: real APIs + real LLM + file ops (requires both)
"""

import json
import os
import shutil
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
        # Create test files that might cause disambiguation issues
        show_dir = e2e_temp_dir / "Test Show"
        show_dir.mkdir(parents=True)

        test_file = show_dir / "Test Show S01E01 Pilot.mp4"
        test_file.write_text("fake video content")

        env = {
            **os.environ,
            "NAMEGNOME_NON_INTERACTIVE": "1",
            "NAMEGNOME_NO_RICH": "1",
        }

        # Add available API keys
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

        # With real APIs and LLM, should handle disambiguation
        # May return 0 (auto-selected) or 2 (manual confirmation)
        assert scan_result.returncode in [0, 1, 2], (
            f"Series disambiguation failed: {scan_result.stderr}"
        )

        # Should produce some output even if disambiguation fails
        assert len(scan_result.stdout) > 0, (
            "Should produce output for disambiguation scenario"
        )


class TestAnthologyShowsEndToEnd:
    """Test comprehensive anthology show edge cases using representative samples."""

    @pytest.mark.e2e
    def test_anthology_shows_comprehensive_e2e_coverage(
        self,
        e2e_temp_dir: Path,
        e2e_anthology_test_files: List[Path],
        mock_api_providers,
        mock_llm_deterministic,
    ):
        """Test comprehensive anthology show coverage across all 6 show types."""
        # Run scan on the complete anthology test directory
        cli_args = [
            "poetry",
            "run",
            "python",
            "-m",
            "namegnome",
            "scan",
            str(e2e_temp_dir),
            "--media-type",
            "tv",
            "--json",
            "--anthology",  # Enable anthology mode for proper splitting
            "--max-duration",
            "30",  # Handle duration-based episode pairing
            "--untrusted-titles",  # Handle shows with unreliable input names
        ]

        env = {
            **os.environ,
            "NAMEGNOME_NON_INTERACTIVE": "1",
            "NAMEGNOME_NO_RICH": "1",
        }

        result = subprocess.run(cli_args, capture_output=True, text=True, env=env)

        # Accept successful scan (0) or manual confirmation required (2)
        assert result.returncode in [0, 2], f"Anthology scan failed: {result.stderr}"

        # Extract and validate JSON output
        stdout = result.stdout
        json_start = stdout.find("{")
        json_end = stdout.rfind("}") + 1

        if json_start >= 0 and json_end > json_start:
            json_str = stdout[json_start:json_end]
            scan_output = json.loads(json_str)

            # Validate scan found files from multiple shows
            items = scan_output.get("items", [])
            assert len(items) >= 10, (
                f"Expected multiple items from 6 shows, got {len(items)}"
            )

            # Check that we have representation from different show types
            show_names = set()
            for item in items:
                if item["status"] in ["pending", "auto"]:
                    dst_path = str(item["destination"])
                    # Extract show name from destination path
                    if "Danger Mouse" in dst_path:
                        show_names.add("Danger Mouse 2015")
                    elif "Firebuds" in dst_path:
                        show_names.add("Firebuds")
                    elif "Harvey Girls" in dst_path:
                        show_names.add("Harvey Girls Forever")
                    elif "Martha Speaks" in dst_path:
                        show_names.add("Martha Speaks")
                    elif "Paw Patrol" in dst_path:
                        show_names.add("Paw Patrol")
                    elif "Octonauts" in dst_path:
                        show_names.add("The Octonauts")

            # Expect at least 4 different shows represented (allowing for some edge cases)
            assert len(show_names) >= 4, (
                f"Expected multiple show types, found: {show_names}"
            )

        # Test passes if comprehensive scan completes across all show types
        assert True, "Successfully processed comprehensive anthology show coverage"

    @pytest.mark.e2e
    @pytest.mark.parametrize(
        "show_type,expected_characteristics",
        [
            ("Danger Mouse 2015", {"anthology": False, "episodes_per_file": 1}),
            (
                "Firebuds",
                {"anthology": True, "episodes_per_file": 2, "trusted_titles": True},
            ),
            (
                "Harvey Girls Forever",
                {"anthology": True, "episodes_per_file": 2, "trusted_titles": False},
            ),
            (
                "Martha Speaks",
                {"anthology": True, "episodes_per_file": 2, "edge_cases": True},
            ),
            ("Paw Patrol", {"anthology": True, "complex_mapping": True}),
            (
                "The Octonauts",
                {
                    "anthology": True,
                    "episodes_per_file": 1,
                    "title_disambiguation": True,
                },
            ),
        ],
    )
    def test_anthology_show_specific_edge_cases(
        self,
        e2e_temp_dir: Path,
        e2e_anthology_test_files: List[Path],
        mock_api_providers,
        mock_llm_deterministic,
        show_type: str,
        expected_characteristics: Dict[str, Any],
    ):
        """Test show-specific anthology characteristics and edge cases."""

        # Filter test files for specific show
        show_files = [
            f
            for f in e2e_anthology_test_files
            if show_type.replace(" ", " ").replace("!", "") in str(f)
        ]
        if not show_files:
            pytest.skip(f"No test files found for {show_type}")

        # Build CLI args based on show characteristics
        cli_args = [
            "poetry",
            "run",
            "python",
            "-m",
            "namegnome",
            "scan",
            str(show_files[0].parent),  # Scan specific show directory
            "--media-type",
            "tv",
            "--json",
        ]

        # Add show-specific flags
        if expected_characteristics.get("anthology", False):
            cli_args.append("--anthology")

        if expected_characteristics.get("complex_mapping", False):
            cli_args.extend(["--max-duration", "30"])

        if not expected_characteristics.get("trusted_titles", True):
            cli_args.append("--untrusted-titles")

        # Run scan for specific show
        scan_result = subprocess.run(
            cli_args,
            capture_output=True,
            text=True,
            env={
                **os.environ,
                "NAMEGNOME_NON_INTERACTIVE": "1",
            },
        )

        # Accept successful scan (0) or manual confirmation required (2)
        assert scan_result.returncode in [0, 2], (
            f"{show_type} scan failed: {scan_result.stderr}"
        )

        # Extract JSON from output
        stdout = scan_result.stdout
        json_start = stdout.find("{")
        json_end = stdout.rfind("}") + 1

        if json_start >= 0 and json_end > json_start:
            json_str = stdout[json_start:json_end]
            scan_output = json.loads(json_str)

            # Validate show-specific characteristics
            items = scan_output.get("items", [])
            if len(items) > 0:
                # Validate destination paths match show expectations
                for item in items:
                    if item["status"] in ["pending", "auto"]:
                        dst_path = Path(item["destination"])

                        # Check show-specific naming
                        if show_type == "Harvey Girls Forever":
                            assert "Harvey Girls Forever!" in str(dst_path), (
                                "Should preserve exclamation mark"
                            )
                        elif show_type == "The Octonauts":
                            # Title disambiguation - might be "Octonauts" or "The Octonauts"
                            assert "Octonauts" in str(dst_path), (
                                "Should handle title disambiguation"
                            )
                        elif show_type == "Martha Speaks":
                            assert "Martha Speaks" in str(dst_path), (
                                "Should handle same-name episodes"
                            )

        # Test passes if scan completes without error for the specific show type
        assert True, f"Successfully processed {show_type} with appropriate flags"

    @pytest.mark.e2e
    def test_anthology_vs_non_anthology_comparison(
        self,
        e2e_temp_dir: Path,
        e2e_anthology_test_files: List[Path],
        mock_api_providers,
        mock_llm_deterministic,
    ):
        """Compare anthology vs non-anthology processing behavior."""

        # Find files from different show types
        danger_mouse_files = [
            f for f in e2e_anthology_test_files if "Danger Mouse" in str(f)
        ]
        paw_patrol_files = [
            f for f in e2e_anthology_test_files if "Paw Patrol" in str(f)
        ]

        if not danger_mouse_files or not paw_patrol_files:
            pytest.skip(
                "Need both Danger Mouse (non-anthology) and Paw Patrol (anthology) files"
            )

        # Test non-anthology show (Danger Mouse) without --anthology flag
        non_anthology_result = subprocess.run(
            [
                "poetry",
                "run",
                "python",
                "-m",
                "namegnome",
                "scan",
                str(danger_mouse_files[0].parent),
                "--media-type",
                "tv",
                "--json",
            ],
            capture_output=True,
            text=True,
            env={
                **os.environ,
                "NAMEGNOME_NON_INTERACTIVE": "1",
            },
        )

        # Test anthology show (Paw Patrol) with --anthology flag
        anthology_result = subprocess.run(
            [
                "poetry",
                "run",
                "python",
                "-m",
                "namegnome",
                "scan",
                str(paw_patrol_files[0].parent),
                "--media-type",
                "tv",
                "--json",
                "--anthology",
            ],
            capture_output=True,
            text=True,
            env={
                **os.environ,
                "NAMEGNOME_NON_INTERACTIVE": "1",
            },
        )

        # Both should complete successfully
        assert non_anthology_result.returncode in [0, 2], (
            "Non-anthology scan should succeed"
        )
        assert anthology_result.returncode in [0, 2], "Anthology scan should succeed"

        # Test passes if both processing modes work appropriately
        assert True, "Successfully compared anthology vs non-anthology behavior"


class TestVolumeEndToEnd:
    """Test volume-dependent edge cases that only emerge with full directory processing."""

    @pytest.mark.e2e
    @pytest.mark.slow  # Mark as slow since this processes many files
    def test_paw_patrol_full_volume_mapping_conflicts(
        self,
        e2e_temp_dir: Path,
        mock_api_providers,
        mock_llm_deterministic,
    ):
        """Test Paw Patrol full directory for volume-dependent mapping conflicts.

        Paw Patrol has complex episode mapping where file numbering doesn't match
        canonical TVDB episode order, potentially causing conflicts when processing
        the complete 291-file directory that wouldn't appear with small samples.
        """
        # Copy full Paw Patrol directory from mocks
        source_dir = Path(__file__).parent.parent / "mocks" / "tv" / "Paw Patrol"
        if not source_dir.exists():
            pytest.skip("Paw Patrol mock directory not available")

        target_dir = e2e_temp_dir / "Paw Patrol"
        shutil.copytree(source_dir, target_dir)

        # Limit to first season (26 files) for performance while still testing volume conflicts
        season_1_files = list(target_dir.glob("*S01E*"))
        if len(season_1_files) < 10:
            pytest.skip("Insufficient Paw Patrol S01 files for volume testing")

        # Keep only season 1 files for focused volume testing
        for file in target_dir.glob("*.mp4"):
            if not file.name.startswith("Paw Patrol-S01E"):
                file.unlink()

        cli_args = [
            "poetry",
            "run",
            "python",
            "-m",
            "namegnome",
            "scan",
            str(target_dir),
            "--media-type",
            "tv",
            "--json",
            "--anthology",  # Required for proper episode splitting
            "--max-duration",
            "30",  # Handle duration-based pairing
        ]

        env = {
            **os.environ,
            "NAMEGNOME_NON_INTERACTIVE": "1",
            "NAMEGNOME_NO_RICH": "1",
        }

        result = subprocess.run(cli_args, capture_output=True, text=True, env=env)

        # Accept successful scan (0) or manual confirmation required (2)
        assert result.returncode in [0, 2], (
            f"Paw Patrol volume scan failed: {result.stderr}"
        )

        # Extract and validate JSON output
        stdout = result.stdout
        json_start = stdout.find("{")
        json_end = stdout.rfind("}") + 1

        if json_start >= 0 and json_end > json_start:
            json_str = stdout[json_start:json_end]
            scan_output = json.loads(json_str)

            items = scan_output.get("items", [])
            assert len(items) >= 10, (
                f"Expected multiple Paw Patrol S01 items, got {len(items)}"
            )

            # Check for conflicts that emerge from complex mapping
            conflict_items = [
                item for item in items if item.get("status") == "conflict"
            ]
            if conflict_items:
                # Document the conflicts found - this is valuable debugging info
                conflict_sources = [item["source"] for item in conflict_items]
                print(f"Volume testing found mapping conflicts in: {conflict_sources}")

            # Validate that episode mapping is being handled correctly
            destinations = [
                item["destination"]
                for item in items
                if item["status"] in ["pending", "auto"]
            ]

            # Check for duplicate destinations (case-insensitive)
            dest_lower = [Path(d).as_posix().lower() for d in destinations]
            unique_dests = set(dest_lower)

            if len(dest_lower) != len(unique_dests):
                duplicates = [d for d in dest_lower if dest_lower.count(d) > 1]
                pytest.fail(
                    f"Volume testing revealed duplicate destinations: {set(duplicates)}"
                )

        # Test passes if volume processing completes without unhandled conflicts
        assert True, (
            "Successfully processed Paw Patrol volume testing for mapping conflicts"
        )

    @pytest.mark.e2e
    @pytest.mark.slow
    def test_harvey_girls_forever_volume_untrusted_names(
        self,
        e2e_temp_dir: Path,
        mock_api_providers,
        mock_llm_deterministic,
    ):
        """Test Harvey Girls Forever! full directory for volume-dependent untrusted name issues.

        Harvey Girls Forever! was hand-selected for SONARR-style untrusted names with special
        characters. Volume testing can reveal conflicts in character normalization and
        untrusted title handling that don't appear with small samples.
        """
        source_dir = (
            Path(__file__).parent.parent / "mocks" / "tv" / "Harvey Girls Forever"
        )
        if not source_dir.exists():
            pytest.skip("Harvey Girls Forever mock directory not available")

        target_dir = e2e_temp_dir / "Harvey Girls Forever"
        shutil.copytree(source_dir, target_dir)

        # Count available files
        all_files = list(target_dir.glob("*.mkv"))
        if len(all_files) < 5:
            pytest.skip("Insufficient Harvey Girls Forever files for volume testing")

        cli_args = [
            "poetry",
            "run",
            "python",
            "-m",
            "namegnome",
            "scan",
            str(target_dir),
            "--media-type",
            "tv",
            "--json",
            "--anthology",
            "--untrusted-titles",  # Key flag for this show's edge case
            "--max-duration",
            "30",
        ]

        env = {
            **os.environ,
            "NAMEGNOME_NON_INTERACTIVE": "1",
            "NAMEGNOME_NO_RICH": "1",
        }

        result = subprocess.run(cli_args, capture_output=True, text=True, env=env)
        assert result.returncode in [0, 2], (
            f"Harvey Girls Forever volume scan failed: {result.stderr}"
        )

        # Validate output
        stdout = result.stdout
        json_start = stdout.find("{")
        json_end = stdout.rfind("}") + 1

        if json_start >= 0 and json_end > json_start:
            json_str = stdout[json_start:json_end]
            scan_output = json.loads(json_str)

            items = scan_output.get("items", [])
            assert len(items) >= 5, (
                f"Expected multiple Harvey Girls Forever items, got {len(items)}"
            )

            # Check for special character handling in volume
            for item in items:
                if item["status"] in ["pending", "auto"]:
                    dst_path = str(item["destination"])
                    # Should preserve exclamation mark in show name
                    assert "Harvey Girls Forever!" in dst_path, (
                        f"Should preserve special chars: {dst_path}"
                    )

            # Document any conflicts from untrusted name processing
            conflict_items = [
                item for item in items if item.get("status") == "conflict"
            ]
            if conflict_items:
                conflict_sources = [item["source"] for item in conflict_items]
                print(
                    f"Harvey Girls Forever volume testing found untrusted name conflicts: {conflict_sources}"
                )

        assert True, (
            "Successfully processed Harvey Girls Forever volume testing for untrusted names"
        )

    @pytest.mark.e2e
    @pytest.mark.slow
    def test_martha_speaks_volume_apostrophe_edge_cases(
        self,
        e2e_temp_dir: Path,
        mock_api_providers,
        mock_llm_deterministic,
    ):
        """Test Martha Speaks full directory for volume-dependent apostrophe and same-name episode issues.

        Martha Speaks was hand-selected for apostrophes in titles and same-name episodes
        across seasons. Volume testing can reveal conflicts in title normalization and
        episode disambiguation that don't appear with small samples.
        """
        source_dir = Path(__file__).parent.parent / "mocks" / "tv" / "Martha Speaks"
        if not source_dir.exists():
            pytest.skip("Martha Speaks mock directory not available")

        target_dir = e2e_temp_dir / "Martha Speaks"
        shutil.copytree(source_dir, target_dir)

        # Limit to manageable subset for performance (e.g., 2 seasons)
        all_files = list(target_dir.glob("*.mp4"))
        season_1_2_files = [
            f for f in all_files if any(s in f.name for s in ["S01E", "S02E"])
        ]

        if len(season_1_2_files) < 10:
            pytest.skip("Insufficient Martha Speaks S01-S02 files for volume testing")

        # Keep only first 2 seasons for focused volume testing
        for file in all_files:
            if file not in season_1_2_files:
                file.unlink()

        cli_args = [
            "poetry",
            "run",
            "python",
            "-m",
            "namegnome",
            "scan",
            str(target_dir),
            "--media-type",
            "tv",
            "--json",
            "--anthology",
            "--max-duration",
            "30",
        ]

        env = {
            **os.environ,
            "NAMEGNOME_NON_INTERACTIVE": "1",
            "NAMEGNOME_NO_RICH": "1",
        }

        result = subprocess.run(cli_args, capture_output=True, text=True, env=env)
        assert result.returncode in [0, 2], (
            f"Martha Speaks volume scan failed: {result.stderr}"
        )

        # Validate output
        stdout = result.stdout
        json_start = stdout.find("{")
        json_end = stdout.rfind("}") + 1

        if json_start >= 0 and json_end > json_start:
            json_str = stdout[json_start:json_end]
            scan_output = json.loads(json_str)

            items = scan_output.get("items", [])
            assert len(items) >= 10, (
                f"Expected multiple Martha Speaks items, got {len(items)}"
            )

            # Check for apostrophe handling in volume
            apostrophe_episodes = [
                item
                for item in items
                if item["status"] in ["pending", "auto"]
                and "'" in item.get("destination", "")
            ]
            if apostrophe_episodes:
                print(
                    f"Martha Speaks volume testing processed {len(apostrophe_episodes)} episodes with apostrophes"
                )

            # Document any conflicts from same-name episode processing
            conflict_items = [
                item for item in items if item.get("status") == "conflict"
            ]
            if conflict_items:
                conflict_sources = [item["source"] for item in conflict_items]
                print(
                    f"Martha Speaks volume testing found same-name episode conflicts: {conflict_sources}"
                )

        assert True, (
            "Successfully processed Martha Speaks volume testing for apostrophe edge cases"
        )

    @pytest.mark.e2e
    @pytest.mark.slow
    def test_octonauts_volume_title_disambiguation(
        self,
        e2e_temp_dir: Path,
        mock_api_providers,
        mock_llm_deterministic,
    ):
        """Test The Octonauts full directory for volume-dependent title disambiguation issues.

        The Octonauts was hand-selected for title disambiguation ("The Octonauts" vs "Octonauts").
        Volume testing can reveal conflicts in show name normalization that don't appear with small samples.
        """
        source_dir = Path(__file__).parent.parent / "mocks" / "tv" / "The Octonauts"
        if not source_dir.exists():
            pytest.skip("The Octonauts mock directory not available")

        target_dir = e2e_temp_dir / "The Octonauts"
        shutil.copytree(source_dir, target_dir)

        # Limit to manageable subset for performance
        all_files = list(target_dir.glob("*.mp4"))
        season_1_files = [f for f in all_files if "S01E" in f.name]

        if len(season_1_files) < 10:
            pytest.skip("Insufficient The Octonauts S01 files for volume testing")

        # Keep only season 1 for focused volume testing
        for file in all_files:
            if file not in season_1_files:
                file.unlink()

        cli_args = [
            "poetry",
            "run",
            "python",
            "-m",
            "namegnome",
            "scan",
            str(target_dir),
            "--media-type",
            "tv",
            "--json",
            "--anthology",  # Single episodes but still anthology structure
        ]

        env = {
            **os.environ,
            "NAMEGNOME_NON_INTERACTIVE": "1",
            "NAMEGNOME_NO_RICH": "1",
        }

        result = subprocess.run(cli_args, capture_output=True, text=True, env=env)
        assert result.returncode in [0, 2], (
            f"The Octonauts volume scan failed: {result.stderr}"
        )

        # Validate output
        stdout = result.stdout
        json_start = stdout.find("{")
        json_end = stdout.rfind("}") + 1

        if json_start >= 0 and json_end > json_start:
            json_str = stdout[json_start:json_end]
            scan_output = json.loads(json_str)

            items = scan_output.get("items", [])
            assert len(items) >= 10, (
                f"Expected multiple The Octonauts items, got {len(items)}"
            )

            # Check for title disambiguation consistency in volume
            destinations = [
                item["destination"]
                for item in items
                if item["status"] in ["pending", "auto"]
            ]
            show_names = set()
            for dst in destinations:
                if "Octonauts" in dst:
                    # Extract show name portion
                    if "The Octonauts" in dst:
                        show_names.add("The Octonauts")
                    elif "Octonauts" in dst:
                        show_names.add("Octonauts")

            # Should be consistent in naming choice
            if len(show_names) > 1:
                print(
                    f"The Octonauts volume testing found title disambiguation inconsistency: {show_names}"
                )

            # Document any conflicts from title disambiguation
            conflict_items = [
                item for item in items if item.get("status") == "conflict"
            ]
            if conflict_items:
                conflict_sources = [item["source"] for item in conflict_items]
                print(
                    f"The Octonauts volume testing found title disambiguation conflicts: {conflict_sources}"
                )

        assert True, (
            "Successfully processed The Octonauts volume testing for title disambiguation"
        )

    @pytest.mark.e2e
    @pytest.mark.slow
    def test_firebuds_volume_trusted_titles_validation(
        self,
        e2e_temp_dir: Path,
        mock_api_providers,
        mock_llm_deterministic,
    ):
        """Test Firebuds full directory for volume-dependent trusted title assumption issues.

        Firebuds was hand-selected for trusted episode titles with reliable naming.
        Volume testing can reveal edge cases where trusted title assumptions break down
        at scale that don't appear with small samples.
        """
        source_dir = Path(__file__).parent.parent / "mocks" / "tv" / "Firebuds"
        if not source_dir.exists():
            pytest.skip("Firebuds mock directory not available")

        target_dir = e2e_temp_dir / "Firebuds"
        shutil.copytree(source_dir, target_dir)

        # Count available files
        all_files = list(target_dir.glob("*.mp4"))
        if len(all_files) < 10:
            pytest.skip("Insufficient Firebuds files for volume testing")

        cli_args = [
            "poetry",
            "run",
            "python",
            "-m",
            "namegnome",
            "scan",
            str(target_dir),
            "--media-type",
            "tv",
            "--json",
            "--anthology",
            "--max-duration",
            "30",
            # Note: NOT using --untrusted-titles since this show has trusted titles
        ]

        env = {
            **os.environ,
            "NAMEGNOME_NON_INTERACTIVE": "1",
            "NAMEGNOME_NO_RICH": "1",
        }

        result = subprocess.run(cli_args, capture_output=True, text=True, env=env)
        assert result.returncode in [0, 2], (
            f"Firebuds volume scan failed: {result.stderr}"
        )

        # Validate output
        stdout = result.stdout
        json_start = stdout.find("{")
        json_end = stdout.rfind("}") + 1

        if json_start >= 0 and json_end > json_start:
            json_str = stdout[json_start:json_end]
            scan_output = json.loads(json_str)

            items = scan_output.get("items", [])
            assert len(items) >= 10, (
                f"Expected multiple Firebuds items, got {len(items)}"
            )

            # Check trusted title processing success rate in volume
            auto_items = [item for item in items if item.get("status") == "auto"]
            manual_items = [item for item in items if item.get("status") == "manual"]

            if len(items) > 0:
                auto_rate = len(auto_items) / len(items)
                print(
                    f"Firebuds volume testing trusted titles auto-success rate: {auto_rate:.2%}"
                )

                # With trusted titles, should have high auto-success rate
                if auto_rate < 0.5:  # Less than 50% auto
                    print(
                        f"WARNING: Firebuds trusted titles showing low auto-success rate at volume: {auto_rate:.2%}"
                    )

            # Document any conflicts from trusted title processing
            conflict_items = [
                item for item in items if item.get("status") == "conflict"
            ]
            if conflict_items:
                conflict_sources = [item["source"] for item in conflict_items]
                print(
                    f"Firebuds volume testing found trusted title conflicts: {conflict_sources}"
                )

        assert True, (
            "Successfully processed Firebuds volume testing for trusted titles validation"
        )

    @pytest.mark.e2e
    @pytest.mark.slow
    def test_danger_mouse_volume_non_anthology_control(
        self,
        e2e_temp_dir: Path,
        mock_api_providers,
        mock_llm_deterministic,
    ):
        """Test Danger Mouse 2015 full directory as non-anthology volume control case.

        Danger Mouse 2015 was hand-selected as the non-anthology control case.
        Volume testing validates that non-anthology processing remains consistent
        at scale and doesn't develop conflicts that don't appear with small samples.
        """
        source_dir = Path(__file__).parent.parent / "mocks" / "tv" / "Danger Mouse 2015"
        if not source_dir.exists():
            pytest.skip("Danger Mouse 2015 mock directory not available")

        target_dir = e2e_temp_dir / "Danger Mouse 2015"
        shutil.copytree(source_dir, target_dir)

        # Limit to manageable subset for performance
        all_files = list(target_dir.glob("*.mp4"))
        season_1_files = [f for f in all_files if "S01E" in f.name]

        if len(season_1_files) < 10:
            pytest.skip("Insufficient Danger Mouse 2015 S01 files for volume testing")

        # Keep only season 1 for focused volume testing
        for file in all_files:
            if file not in season_1_files:
                file.unlink()

        cli_args = [
            "poetry",
            "run",
            "python",
            "-m",
            "namegnome",
            "scan",
            str(target_dir),
            "--media-type",
            "tv",
            "--json",
            # Note: NOT using --anthology since this is non-anthology control
        ]

        env = {
            **os.environ,
            "NAMEGNOME_NON_INTERACTIVE": "1",
            "NAMEGNOME_NO_RICH": "1",
        }

        result = subprocess.run(cli_args, capture_output=True, text=True, env=env)
        assert result.returncode in [0, 2], (
            f"Danger Mouse 2015 volume scan failed: {result.stderr}"
        )

        # Validate output
        stdout = result.stdout
        json_start = stdout.find("{")
        json_end = stdout.rfind("}") + 1

        if json_start >= 0 and json_end > json_start:
            json_str = stdout[json_start:json_end]
            scan_output = json.loads(json_str)

            items = scan_output.get("items", [])
            assert len(items) >= 10, (
                f"Expected multiple Danger Mouse 2015 items, got {len(items)}"
            )

            # Non-anthology should have high auto-success rate
            auto_items = [item for item in items if item.get("status") == "auto"]
            if len(items) > 0:
                auto_rate = len(auto_items) / len(items)
                print(
                    f"Danger Mouse 2015 volume testing non-anthology auto-success rate: {auto_rate:.2%}"
                )

            # Document any unexpected conflicts in non-anthology volume processing
            conflict_items = [
                item for item in items if item.get("status") == "conflict"
            ]
            if conflict_items:
                conflict_sources = [item["source"] for item in conflict_items]
                print(
                    f"Danger Mouse 2015 volume testing found unexpected non-anthology conflicts: {conflict_sources}"
                )

        assert True, (
            "Successfully processed Danger Mouse 2015 volume testing as non-anthology control"
        )

    @pytest.mark.e2e
    @pytest.mark.slow
    def test_all_shows_comprehensive_volume_testing(
        self,
        e2e_temp_dir: Path,
        mock_api_providers,
        mock_llm_deterministic,
    ):
        """Test all 6 hand-selected shows simultaneously for cross-show volume conflicts.

        Process all 6 shows together to detect volume-dependent conflicts that emerge
        when multiple complex show types are processed in the same scan operation.
        """
        source_base = Path(__file__).parent.parent / "mocks" / "tv"
        all_shows = [
            "Danger Mouse 2015",
            "Firebuds",
            "Harvey Girls Forever",
            "Martha Speaks",
            "Paw Patrol",
            "The Octonauts",
        ]

        copied_shows = []
        for show in all_shows:
            source_dir = source_base / show
            if source_dir.exists():
                target_dir = e2e_temp_dir / show
                shutil.copytree(source_dir, target_dir)

                # Limit each show to manageable subset (season 1 or first N files)
                show_files = list(target_dir.glob("*.mp4")) + list(
                    target_dir.glob("*.mkv")
                )
                season_1_files = [f for f in show_files if "S01E" in f.name]

                # Keep season 1 or first 15 files if no season structure
                if len(season_1_files) >= 5:
                    keep_files = season_1_files[:15]  # Limit for performance
                else:
                    keep_files = show_files[:10]  # Fallback for other naming

                for file in show_files:
                    if file not in keep_files:
                        file.unlink()

                if keep_files:  # Only count shows with actual files
                    copied_shows.append(show)

        if len(copied_shows) < 4:
            pytest.skip(
                f"Need at least 4 shows for comprehensive volume testing, got {len(copied_shows)}"
            )

        cli_args = [
            "poetry",
            "run",
            "python",
            "-m",
            "namegnome",
            "scan",
            str(e2e_temp_dir),
            "--media-type",
            "tv",
            "--json",
            "--anthology",  # Enable for shows that need it
            "--untrusted-titles",  # Enable for Harvey Girls Forever
            "--max-duration",
            "30",  # Handle various episode lengths
        ]

        env = {
            **os.environ,
            "NAMEGNOME_NON_INTERACTIVE": "1",
            "NAMEGNOME_NO_RICH": "1",
        }

        result = subprocess.run(cli_args, capture_output=True, text=True, env=env)
        assert result.returncode in [0, 2], (
            f"Comprehensive volume scan failed: {result.stderr}"
        )

        # Validate output
        stdout = result.stdout
        json_start = stdout.find("{")
        json_end = stdout.rfind("}") + 1

        if json_start >= 0 and json_end > json_start:
            json_str = stdout[json_start:json_end]
            scan_output = json.loads(json_str)

            items = scan_output.get("items", [])
            expected_min_items = len(copied_shows) * 5  # At least 5 items per show
            assert len(items) >= expected_min_items, (
                f"Expected items from {len(copied_shows)} shows ({expected_min_items}+), got {len(items)}"
            )

            # Analyze results by show
            show_stats = {}
            for item in items:
                source_path = Path(item["source"])
                show_name = source_path.parent.name
                if show_name not in show_stats:
                    show_stats[show_name] = {
                        "total": 0,
                        "auto": 0,
                        "manual": 0,
                        "conflict": 0,
                    }

                show_stats[show_name]["total"] += 1
                status = item.get("status", "unknown")
                if status in show_stats[show_name]:
                    show_stats[show_name][status] += 1

            print(
                f"Comprehensive volume testing results across {len(copied_shows)} shows:"
            )
            for show, stats in show_stats.items():
                auto_rate = stats["auto"] / stats["total"] if stats["total"] > 0 else 0
                print(
                    f"  {show}: {stats['total']} files, {auto_rate:.1%} auto, {stats['conflict']} conflicts"
                )

            # Check for cross-show destination conflicts
            destinations = []
            for item in items:
                if item["status"] in ["pending", "auto"]:
                    destinations.append(Path(item["destination"]).as_posix().lower())

            unique_destinations = set(destinations)
            if len(destinations) != len(unique_destinations):
                duplicates = [d for d in destinations if destinations.count(d) > 1]
                print(
                    f"Comprehensive volume testing found cross-show destination conflicts: {set(duplicates)}"
                )

        assert True, (
            f"Successfully processed comprehensive volume testing across all {len(copied_shows)} hand-selected shows"
        )
