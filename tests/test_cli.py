"""
Integration tests for apple-translate CLI v1.0.1.

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

# 21 supported languages (maximalIdentifier) — explicitly listed
SUPPORTED_LANGUAGES = [
    "ar-Arab-AE",
    "de-Latn-DE",
    "en-Latn-GB",
    "en-Latn-US",
    "es-Latn-ES",
    "fr-Latn-FR",
    "hi-Deva-IN",
    "id-Latn-ID",
    "it-Latn-IT",
    "ja-Jpan-JP",
    "ko-Kore-KR",
    "nl-Latn-NL",
    "pl-Latn-PL",
    "pt-Latn-BR",
    "ru-Cyrl-RU",
    "th-Thai-TH",
    "tr-Latn-TR",
    "uk-Cyrl-UA",
    "vi-Latn-VN",
    "zh-Hans-CN",
    "zh-Hant-TW",
]

# Same-languageCode pairs (4 pairs) — these should be rejected
SAME_LANGUAGE_PAIRS = [
    ("en-Latn-GB", "en-Latn-US"),
    ("en-Latn-US", "en-Latn-GB"),
    ("zh-Hans-CN", "zh-Hant-TW"),
    ("zh-Hant-TW", "zh-Hans-CN"),
]

_SAME_LANG_SET = {(s, t) for s, t in SAME_LANGUAGE_PAIRS}


def run_cli(
    args: list[str] = [],
    input_text: str | None = None,
    timeout: int = 30,
) -> subprocess.CompletedProcess:
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
        assert "Usage:" in result.stdout
        assert "--from" in result.stdout
        assert "--to" in result.stdout

    def test_help_short(self):
        result = run_cli(["-h"])
        assert result.returncode == 0
        assert "Usage:" in result.stdout

    def test_version(self):
        result = run_cli(["--version"])
        assert result.returncode == 0
        assert result.stdout.strip() == "apple-translate 1.0.1"

    def test_version_short(self):
        result = run_cli(["-v"])
        assert result.returncode == 0
        assert result.stdout.strip() == "apple-translate 1.0.1"

    def test_help_ignores_stdin(self):
        result = run_cli(["--help"], input_text="Hello")
        assert result.returncode == 0
        assert "Usage:" in result.stdout


# ── Required arguments ──


class TestRequiredArgs:
    def test_missing_both(self):
        result = run_cli([], input_text="Hello")
        assert result.returncode != 0
        assert "--from" in result.stderr

    def test_missing_from(self):
        result = run_cli(["--to", "ja"], input_text="Hello")
        assert result.returncode != 0
        assert "--from" in result.stderr

    def test_missing_to(self):
        result = run_cli(["--from", "en"], input_text="Hello")
        assert result.returncode != 0
        assert "--to" in result.stderr


# ── Same-language pair detection ──


class TestSameLanguagePair:
    @pytest.mark.parametrize(
        "src,tgt",
        SAME_LANGUAGE_PAIRS,
        ids=[f"{s}->{t}" for s, t in SAME_LANGUAGE_PAIRS],
    )
    def test_same_language_maximal(self, src: str, tgt: str):
        result = run_cli(["--from", src, "--to", tgt], input_text="Hello")
        assert result.returncode != 0
        assert "same language" in result.stderr.lower()

    @pytest.mark.parametrize(
        "src,tgt",
        [("en", "en"), ("ja", "ja"), ("ko", "ko")],
        ids=["en->en", "ja->ja", "ko->ko"],
    )
    def test_same_language_short(self, src: str, tgt: str):
        result = run_cli(["--from", src, "--to", tgt], input_text="Hello")
        assert result.returncode != 0
        assert "same language" in result.stderr.lower()


# ── --list-languages ──


class TestListLanguages:
    def test_list_languages(self):
        result = run_cli(["--list-languages"])
        assert result.returncode == 0
        lines = result.stdout.strip().splitlines()
        assert len(lines) >= 21
        for line in lines:
            parts = line.split()
            assert len(parts) >= 2, f"Unexpected format: {line}"

    def test_list_languages_short(self):
        result = run_cli(["-l"])
        assert result.returncode == 0
        assert len(result.stdout.strip().splitlines()) >= 21

    @pytest.mark.parametrize("lang", SUPPORTED_LANGUAGES)
    def test_list_contains(self, lang: str):
        result = run_cli(["-l"])
        assert lang in result.stdout


# ── Plain text translation ──


class TestPlainText:
    def test_empty_input(self):
        result = run_cli(["--from", "en", "--to", "ja"], input_text="")
        assert result.returncode == 0
        assert result.stdout == ""

    def test_single_line(self):
        result = run_cli(["--from", "en", "--to", "ja"], input_text="Hello")
        assert result.returncode == 0
        output = result.stdout.strip()
        assert len(output) > 0
        assert not output.startswith("{")

    def test_multiple_lines(self):
        result = run_cli(
            ["--from", "en", "--to", "ja"],
            input_text="Hello\nGoodbye\n",
        )
        assert result.returncode == 0
        lines = result.stdout.strip().splitlines()
        assert len(lines) == 2

    def test_whitespace_only_input(self):
        result = run_cli(
            ["--from", "en", "--to", "ja"],
            input_text="   \n  \n   ",
        )
        assert result.returncode == 0
        assert result.stdout.strip() == ""


# ── Short-form language keys ──


class TestShortFormKeys:
    @pytest.mark.parametrize(
        "src,tgt,text",
        [
            ("ja", "en", "こんにちは"),
            ("en", "ja", "Hello"),
            ("en", "ko", "Hello"),
            ("ja", "zh-Hans", "こんにちは"),
            ("ja", "zh-Hant", "こんにちは"),
            ("ko", "ja", "안녕하세요"),
            ("fr", "de", "Bonjour"),
            ("es", "pt", "Hola"),
        ],
        ids=[
            "ja->en", "en->ja", "en->ko", "ja->zh-Hans",
            "ja->zh-Hant", "ko->ja", "fr->de", "es->pt",
        ],
    )
    def test_short_form(self, src: str, tgt: str, text: str):
        result = run_cli(["--from", src, "--to", tgt], input_text=text)
        assert result.returncode == 0, f"stderr: {result.stderr}"
        assert len(result.stdout.strip()) > 0


# ── Translation: all valid pairs (maximalIdentifier) ──


def _valid_pairs() -> list[tuple[str, str]]:
    """416 valid translation pairs (all combinations minus same-languageCode)."""
    pairs = []
    for src in SUPPORTED_LANGUAGES:
        for tgt in SUPPORTED_LANGUAGES:
            if src != tgt and (src, tgt) not in _SAME_LANG_SET:
                pairs.append((src, tgt))
    return pairs


class TestAllLanguagePairs:
    @pytest.mark.parametrize(
        "src,tgt",
        _valid_pairs(),
        ids=[f"{s}->{t}" for s, t in _valid_pairs()],
    )
    def test_translation_pair(self, src: str, tgt: str):
        result = run_cli(
            ["--from", src, "--to", tgt],
            input_text="Hello",
            timeout=30,
        )
        assert result.returncode == 0, (
            f"[{src}->{tgt}] exit={result.returncode} "
            f"stderr={result.stderr.strip()}"
        )
        assert len(result.stdout.strip()) > 0, f"[{src}->{tgt}] Empty output"
