"""Tests for the CLI module."""

import os
import subprocess
import sys
import tempfile

import pytest


SKILL_DIR = os.path.join(os.path.dirname(__file__), "..")
SAMPLE_FILE = os.path.join(SKILL_DIR, "assets", "sample-functions.py")


def run_cli(*args):
    """Run the CLI as a subprocess and return the result."""
    cmd = [sys.executable, os.path.join(SKILL_DIR, "scripts", "cli.py")] + list(args)
    return subprocess.run(cmd, capture_output=True, text=True, cwd=SKILL_DIR)


class TestCLI:
    def test_help(self):
        result = run_cli("--help")
        assert result.returncode == 0
        assert "Generate pytest unit tests" in result.stdout

    def test_missing_file(self):
        result = run_cli("nonexistent.py")
        assert result.returncode != 0
        assert "does not exist" in result.stderr

    def test_generate_from_sample(self):
        with tempfile.NamedTemporaryFile(suffix=".py", delete=False) as f:
            output_path = f.name
        try:
            result = run_cli(SAMPLE_FILE, "-o", output_path)
            assert result.returncode == 0
            with open(output_path) as f:
                content = f.read()
            assert "import pytest" in content
            assert "def test_add_basic" in content
        finally:
            os.unlink(output_path)

    def test_verbose_flag(self):
        with tempfile.NamedTemporaryFile(suffix=".py", delete=False) as f:
            output_path = f.name
        try:
            result = run_cli(SAMPLE_FILE, "-o", output_path, "-v")
            assert result.returncode == 0
            assert "Reading file" in result.stdout
            assert "Found" in result.stdout
        finally:
            os.unlink(output_path)

    def test_coverage_flag(self):
        with tempfile.NamedTemporaryFile(suffix=".py", delete=False) as f:
            output_path = f.name
        try:
            result = run_cli(SAMPLE_FILE, "-o", output_path, "--coverage")
            assert result.returncode == 0
            with open(output_path) as f:
                content = f.read()
            assert "pragma: no cover" in content
        finally:
            os.unlink(output_path)

    def test_syntax_error_file(self):
        with tempfile.NamedTemporaryFile(suffix=".py", mode="w", delete=False) as f:
            f.write("def broken(:\n    pass\n")
            bad_file = f.name
        try:
            result = run_cli(bad_file)
            assert result.returncode == 2
            assert "yntax" in result.stderr
        finally:
            os.unlink(bad_file)

    def test_directory_input(self):
        result = run_cli(".")
        assert result.returncode != 0
        assert "not a file" in result.stderr

    def test_default_output_filename(self):
        """Test that default output is test_<input>.py in current directory."""
        with tempfile.NamedTemporaryFile(suffix=".py", mode="w", delete=False, dir=SKILL_DIR) as f:
            f.write("def hello():\n    pass\n")
            temp_input = f.name

        expected_output = os.path.join(SKILL_DIR, f"test_{os.path.basename(temp_input)}")
        try:
            result = run_cli(temp_input)
            assert result.returncode == 0
            assert os.path.exists(expected_output)
            with open(expected_output) as f:
                content = f.read()
            assert "import pytest" in content
        finally:
            os.unlink(temp_input)
            if os.path.exists(expected_output):
                os.unlink(expected_output)

    def test_generated_output_is_valid_python(self):
        # Use a file with a valid Python module name (no hyphens)
        with tempfile.NamedTemporaryFile(
            suffix=".py", prefix="sample_funcs_", mode="w", delete=False
        ) as f:
            f.write("def add(a: int, b: int) -> int:\n    return a + b\n")
            input_path = f.name
        with tempfile.NamedTemporaryFile(suffix=".py", delete=False) as f:
            output_path = f.name
        try:
            result = run_cli(input_path, "-o", output_path)
            assert result.returncode == 0
            with open(output_path) as f:
                content = f.read()
            compile(content, output_path, "exec")
        finally:
            os.unlink(input_path)
            os.unlink(output_path)
