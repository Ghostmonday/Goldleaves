"""
Tests for the integrity check system.

This module tests the integrity_check.py script to ensure it works correctly
and can be safely used in CI environments.
"""

import os
import sys
import json
import subprocess
import tempfile
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add scripts directory to path so we can import the integrity checker
REPO_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(REPO_ROOT / "scripts"))

try:
    from integrity_check import IntegrityChecker, CheckStatus, CheckSeverity, CheckResult, IntegrityReport
except ImportError:
    # If imports fail, skip these tests
    pytestmark = pytest.mark.skip(reason="integrity_check module not available")


class TestIntegrityChecker:
    """Test the IntegrityChecker class and its methods."""

    def setup_method(self):
        """Set up test fixtures."""
        self.checker = IntegrityChecker(skip_heavy=True)

    def test_checker_initialization(self):
        """Test that checker initializes correctly."""
        assert self.checker.repo_root == REPO_ROOT
        assert self.checker.skip_heavy == True
        assert isinstance(self.checker.config, dict)
        assert isinstance(self.checker.results, list)

    def test_config_loading(self):
        """Test configuration loading."""
        # Test with default config
        checker = IntegrityChecker()
        assert isinstance(checker.config, dict)

        # Test with non-existent config file
        checker = IntegrityChecker(config_path="/nonexistent/config.yaml")
        assert isinstance(checker.config, dict)

    def test_check_result_creation(self):
        """Test CheckResult creation and serialization."""
        result = CheckResult(
            name="test_check",
            status=CheckStatus.PASSED,
            severity=CheckSeverity.INFO,
            message="Test message",
            details=["detail1", "detail2"]
        )

        assert result.name == "test_check"
        assert result.status == CheckStatus.PASSED
        assert result.severity == CheckSeverity.INFO
        assert result.message == "Test message"
        assert len(result.details) == 2

    def test_integrity_report_creation(self):
        """Test IntegrityReport creation and JSON serialization."""
        results = [
            CheckResult(
                name="test1",
                status=CheckStatus.PASSED,
                severity=CheckSeverity.INFO,
                message="Test 1 passed"
            ),
            CheckResult(
                name="test2",
                status=CheckStatus.FAILED,
                severity=CheckSeverity.CRITICAL,
                message="Test 2 failed"
            )
        ]

        report = IntegrityReport(
            timestamp="2023-01-01T00:00:00",
            total_checks=2,
            passed_checks=1,
            failed_checks=1,
            skipped_checks=0,
            warnings=0,
            critical_failures=1,
            duration_ms=1000,
            results=results
        )

        # Test dictionary conversion
        report_dict = report.to_dict()
        assert isinstance(report_dict, dict)
        assert report_dict["summary"]["total_checks"] == 2
        assert report_dict["summary"]["success"] == False
        assert len(report_dict["checks"]) == 2

        # Test JSON serialization
        json_str = json.dumps(report_dict)
        assert isinstance(json_str, str)
        parsed = json.loads(json_str)
        assert parsed["summary"]["total_checks"] == 2


class TestIntegrityScript:
    """Test the integrity check script execution."""

    def test_script_help(self):
        """Test that script shows help."""
        result = subprocess.run(
            [sys.executable, str(REPO_ROOT / "scripts" / "integrity_check.py"), "--help"],
            capture_output=True,
            text=True
        )

        assert result.returncode == 0
        assert "Goldleaves Full-Scope Integrity Check" in result.stdout
        assert "--json" in result.stdout
        assert "--skip-heavy" in result.stdout

    def test_script_execution_skip_heavy(self):
        """Test script execution with skip-heavy flag."""
        # Set environment variable to ensure heavy checks are skipped
        env = os.environ.copy()
        env["INTEGRITY_SKIP_HEAVY"] = "1"

        result = subprocess.run(
            [sys.executable, str(REPO_ROOT / "scripts" / "integrity_check.py"), "--skip-heavy"],
            capture_output=True,
            text=True,
            env=env,
            timeout=30  # Reasonable timeout for light checks
        )

        # Script should run to completion (exit code may be non-zero due to findings)
        assert result.returncode in [0, 1]  # 0 = success, 1 = issues found
        assert "Goldleaves Integrity Check Report" in result.stdout
        assert "Summary:" in result.stdout

    def test_script_json_output(self):
        """Test script JSON output format."""
        env = os.environ.copy()
        env["INTEGRITY_SKIP_HEAVY"] = "1"

        result = subprocess.run(
            [sys.executable, str(REPO_ROOT / "scripts" / "integrity_check.py"), "--skip-heavy", "--json"],
            capture_output=True,
            text=True,
            env=env,
            timeout=30
        )

        # Should produce valid JSON
        assert result.returncode in [0, 1, 2]

        try:
            output_data = json.loads(result.stdout)
            assert isinstance(output_data, dict)
            assert "timestamp" in output_data
            assert "summary" in output_data
            assert "checks" in output_data
            assert isinstance(output_data["summary"]["total_checks"], int)
            assert isinstance(output_data["checks"], list)
        except json.JSONDecodeError:
            pytest.fail(f"Script did not produce valid JSON. Output: {result.stdout}")

    def test_script_with_config_file(self):
        """Test script execution with custom config file."""
        # Create a temporary config file
        config_content = """
auth:
  public_endpoints:
    - "test_public.py"

frontend:
  coverage_baseline: 90
"""

        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write(config_content)
            config_path = f.name

        try:
            env = os.environ.copy()
            env["INTEGRITY_SKIP_HEAVY"] = "1"

            result = subprocess.run(
                [sys.executable, str(REPO_ROOT / "scripts" / "integrity_check.py"),
                 "--skip-heavy", "--config", config_path],
                capture_output=True,
                text=True,
                env=env,
                timeout=30
            )

            # Should run successfully with custom config
            assert result.returncode in [0, 1]
            assert "Goldleaves Integrity Check Report" in result.stdout

        finally:
            os.unlink(config_path)


class TestIndividualChecks:
    """Test individual integrity checks."""

    def setup_method(self):
        """Set up test fixtures."""
        self.checker = IntegrityChecker(skip_heavy=True)

    def test_environment_variables_check(self):
        """Test environment variables check."""
        result = self.checker.check_environment_variables()

        assert isinstance(result, CheckResult)
        assert result.name == "environment_variables"
        assert result.status in [CheckStatus.PASSED, CheckStatus.FAILED, CheckStatus.WARNING]
        assert isinstance(result.message, str)
        assert isinstance(result.details, list)

    def test_architecture_conventions_check(self):
        """Test architecture conventions check."""
        result = self.checker.check_architecture_conventions()

        assert isinstance(result, CheckResult)
        assert result.name == "architecture_conventions"
        assert result.status in [CheckStatus.PASSED, CheckStatus.FAILED, CheckStatus.SKIPPED]
        assert isinstance(result.message, str)

    def test_route_contracts_check(self):
        """Test route contracts check."""
        result = self.checker.check_route_contracts()

        assert isinstance(result, CheckResult)
        assert result.name == "route_contracts"
        assert result.status in [CheckStatus.PASSED, CheckStatus.FAILED, CheckStatus.WARNING]
        assert isinstance(result.message, str)

    def test_frontend_build_check(self):
        """Test frontend build check."""
        result = self.checker.check_frontend_build()

        assert isinstance(result, CheckResult)
        assert result.name == "frontend_build"
        # Should be skipped since there's no frontend in this project
        assert result.status == CheckStatus.SKIPPED
        assert "No frontend package.json found" in result.message

    def test_python_linting_check(self):
        """Test Python linting check."""
        result = self.checker.check_python_linting()

        assert isinstance(result, CheckResult)
        assert result.name == "python_linting"
        assert result.status in [CheckStatus.PASSED, CheckStatus.FAILED, CheckStatus.SKIPPED]
        assert isinstance(result.message, str)


class TestFullIntegration:
    """Integration tests for the complete integrity check."""

    def test_run_all_checks(self):
        """Test running all checks together."""
        checker = IntegrityChecker(skip_heavy=True)
        report = checker.run_all_checks()

        assert isinstance(report, IntegrityReport)
        assert report.total_checks > 0
        assert len(report.results) == report.total_checks
        assert report.passed_checks + report.failed_checks + report.skipped_checks + report.warnings == report.total_checks
        assert report.duration_ms > 0
        assert isinstance(report.timestamp, str)

        # Test that report can be converted to dict and JSON
        report_dict = report.to_dict()
        json_str = json.dumps(report_dict)
        parsed = json.loads(json_str)
        assert parsed["summary"]["total_checks"] == report.total_checks

    def test_controlled_mode_execution(self):
        """Test execution in controlled mode for CI."""
        # This simulates how the test would be run in CI
        env = os.environ.copy()
        env["INTEGRITY_SKIP_HEAVY"] = "1"

        checker = IntegrityChecker(skip_heavy=True)
        report = checker.run_all_checks()

        # In controlled mode, we expect the script to complete
        assert isinstance(report, IntegrityReport)
        assert report.total_checks > 0

        # Even if there are failures, the script should generate a proper report
        assert report.passed_checks >= 0
        assert report.failed_checks >= 0
        assert report.skipped_checks >= 0

    def test_graceful_error_handling(self):
        """Test that checks handle errors gracefully."""
        checker = IntegrityChecker(skip_heavy=True)

        # Mock a check to raise an exception
        original_check = checker.check_python_linting

        def failing_check():
            raise Exception("Simulated failure")

        checker.check_python_linting = failing_check

        # The checker should handle the exception gracefully
        result = checker._run_check("python_linting", failing_check)

        assert isinstance(result, CheckResult)
        assert result.status == CheckStatus.FAILED
        assert result.severity == CheckSeverity.CRITICAL
        assert "Check failed with exception" in result.message

        # Restore original check
        checker.check_python_linting = original_check


def test_config_file_exists():
    """Test that the configuration file exists and is valid."""
    config_file = REPO_ROOT / "scripts" / "integrity_config.yaml"
    assert config_file.exists(), "integrity_config.yaml should exist"

    # Try to load the config
    import yaml
    with open(config_file, 'r') as f:
        config = yaml.safe_load(f)

    assert isinstance(config, dict)
    assert 'auth' in config
    assert 'architecture' in config


def test_script_file_executable():
    """Test that the script file is properly structured."""
    script_file = REPO_ROOT / "scripts" / "integrity_check.py"
    assert script_file.exists(), "integrity_check.py should exist"

    # Check that file has main function and can be imported
    with open(script_file, 'r') as f:
        content = f.read()

    assert 'def main():' in content
    assert 'if __name__ == "__main__":' in content
    assert 'class IntegrityChecker:' in content


if __name__ == "__main__":
    # Run tests when script is executed directly
    pytest.main([__file__, "-v"])
