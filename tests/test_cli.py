"""
Integration tests for apple-translate CLI.

Requires:
    - The CLI binary built at .build/release/apple-translate
    - Run: swift build -c release
    - Run: python -m pytest tests/ -v
"""

import os
import subprocess
import pytest

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CLI = os.path.join(PROJECT_ROOT, ".build", "release", "apple-translate")


def run_cli(args: list[str] = [], input_text: str | None = None, timeout: int = 30) -> subprocess.CompletedProcess:
    return subprocess.run(
        [CLI] + args,
        input=input_text,
        capture_output=True,
        text=True,
        timeout=timeout,
    )


@pytest.fixture(autouse=True)
def check_binary():
    if not os.path.isfile(CLI):
        pytest.skip(f"CLI binary not found: {CLI}. Run 'swift build -c release' first.")


# ── --help / --version ──


class TestMeta:
    def test_help(self):
        result = run_cli(["--help"])
        assert result.returncode == 0
        assert "Usage: apple-translate" in result.stdout
        assert "--from" in result.stdout
        assert "--to" in result.stdout

    def test_help_short(self):
        result = run_cli(["-h"])
        assert result.returncode == 0
        assert "Usage: apple-translate" in result.stdout

    def test_version(self):
        result = run_cli(["--version"])
        assert result.returncode == 0
        assert "apple-translate" in result.stdout
        # Version string should match semver-like pattern
        parts = result.stdout.strip().split()
        assert len(parts) == 2
        assert parts[1].count(".") == 2  # e.g. "1.0.0"

    def test_version_short(self):
        result = run_cli(["-v"])
        assert result.returncode == 0
        assert "apple-translate" in result.stdout


# ── --list-languages ──


class TestListLanguages:
    def test_list_languages(self):
        result = run_cli(["--list-languages"])
        assert result.returncode == 0
        lines = result.stdout.strip().splitlines()
        assert len(lines) > 0
        # Each line should have a language code and name
        for line in lines:
            parts = line.split()
            assert len(parts) >= 2, f"Unexpected line format: {line}"

    def test_list_languages_short(self):
        result = run_cli(["-l"])
        assert result.returncode == 0
        assert len(result.stdout.strip().splitlines()) > 0

    def test_list_languages_contains_common(self):
        result = run_cli(["-l"])
        output = result.stdout
        # Should contain common languages
        assert "en-" in output  # English
        assert "ja-" in output  # Japanese


# ── Plain text translation ──


class TestPlainText:
    def test_empty_input(self):
        result = run_cli([], input_text="")
        assert result.returncode == 0
        assert result.stdout == ""

    def test_single_line(self):
        result = run_cli(["--from", "en", "--to", "ja"], input_text="Hello")
        assert result.returncode == 0
        output = result.stdout.strip()
        assert len(output) > 0
        # Should NOT be JSON
        assert not output.startswith("{")

    def test_multiple_lines(self):
        result = run_cli(
            ["--from", "en", "--to", "ja"],
            input_text="Hello\nGoodbye\n",
        )
        assert result.returncode == 0
        lines = result.stdout.strip().splitlines()
        assert len(lines) == 2

    def test_default_is_en_to_ja(self):
        """Default --from en --to ja should work without flags."""
        result = run_cli([], input_text="Thank you")
        assert result.returncode == 0
        assert len(result.stdout.strip()) > 0


# ── Edge cases ──


class TestEdgeCases:
    def test_whitespace_only_input(self):
        result = run_cli([], input_text="   \n  \n   ")
        assert result.returncode == 0
        assert result.stdout.strip() == ""

    def test_help_ignores_stdin(self):
        """--help should print help even if stdin has data."""
        result = run_cli(["--help"], input_text="Hello")
        assert result.returncode == 0
        assert "Usage:" in result.stdout


# ── Translation: all-pairs (every language → every other language) ──


def _available_language_codes() -> list[str]:
    """Return language codes reported by --list-languages."""
    result = subprocess.run(
        [CLI, "--list-languages"], capture_output=True, text=True, timeout=15
    )
    codes = []
    for line in result.stdout.strip().splitlines():
        parts = line.split()
        if parts:
            codes.append(parts[0])
    return codes


def _konnichiwa_in_all_languages() -> dict[str, str]:
    """Translate 「こんにちは」 from Japanese into every other language.

    Returns a dict of {lang_code: translated_text}.
    """
    codes = _available_language_codes()
    targets = [c for c in codes if not c.startswith("ja-")]

    translations: dict[str, str] = {"ja-Jpan-JP": "こんにちは"}
    for lang in targets:
        r = subprocess.run(
            [CLI, "--from", "ja", "--to", lang],
            input="こんにちは",
            capture_output=True,
            text=True,
            timeout=30,
        )
        text = r.stdout.strip() if r.returncode == 0 and r.stdout.strip() else "こんにちは"
        translations[lang] = text
    return translations


# Compute once at collection time
_TRANSLATIONS: dict[str, str] = {}
_ALL_CODES: list[str] = []


def _ensure_translations():
    global _TRANSLATIONS, _ALL_CODES
    if not _TRANSLATIONS:
        _ALL_CODES = _available_language_codes()
        _TRANSLATIONS = _konnichiwa_in_all_languages()


def _all_pairs() -> list[tuple[str, str, str]]:
    """Return (from_lang, hello_text, to_lang) for every source→target pair."""
    _ensure_translations()
    pairs = []
    for src in _ALL_CODES:
        src_text = _TRANSLATIONS.get(src, "こんにちは")
        for tgt in _ALL_CODES:
            if src != tgt:
                pairs.append((src, src_text, tgt))
    return pairs


def pytest_generate_tests(metafunc):
    if "translation_pair" in metafunc.fixturenames:
        pairs = _all_pairs()
        ids = [f"{s}->{t}" for s, _, t in pairs]
        metafunc.parametrize("translation_pair", pairs, ids=ids)


class TestAllLanguagePairs:
    def test_konnichiwa_all_pairs(self, translation_pair: tuple[str, str, str]):
        """Translate each language's 'hello' into every other available language."""
        from_lang, input_text, to_lang = translation_pair
        result = run_cli(
            ["--from", from_lang, "--to", to_lang],
            input_text=input_text,
            timeout=30,
        )
        assert result.returncode == 0, (
            f"[{from_lang}->{to_lang}] exit={result.returncode} "
            f"stderr={result.stderr.strip()}"
        )
        output = result.stdout.strip()
        assert len(output) > 0, f"[{from_lang}->{to_lang}] Empty output"
