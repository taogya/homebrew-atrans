"""
Integration tests for atrans CLI v2.0.0.

Requires:
    - The CLI binary built at .build/release/atrans
    - Run: swift build -c release
    - Run: python -m pytest tests/ -v
"""

import os
import pty
import subprocess
import tempfile
import pytest

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CLI = os.path.join(PROJECT_ROOT, ".build", "release", "atrans")

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
        assert result.stdout == "atrans 2.0.0\n"

    def test_version_short(self):
        result = run_cli(["-v"])
        assert result.returncode == 0
        assert result.stdout == "atrans 2.0.0\n"

    def test_help_ignores_stdin(self):
        result = run_cli(["--help"], input_text="Hello")
        assert result.returncode == 0
        assert "Usage:" in result.stdout

    def test_help_shows_text_option(self):
        result = run_cli(["--help"])
        assert "--text" in result.stdout

    def test_help_shows_file_option(self):
        result = run_cli(["--help"])
        assert "--file" in result.stdout


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
        lines = result.stdout.splitlines()
        assert len(lines) >= 21
        for line in lines:
            parts = line.split()
            assert len(parts) >= 2, f"Unexpected format: {line}"

    def test_list_languages_short(self):
        result = run_cli(["-l"])
        assert result.returncode == 0
        assert len(result.stdout.splitlines()) >= 21

    @pytest.mark.parametrize("lang", SUPPORTED_LANGUAGES)
    def test_list_contains(self, lang: str):
        result = run_cli(["-l"])
        assert lang in result.stdout


# ── Plain text translation (stdin) ──


class TestPlainText:
    def test_empty_input(self):
        result = run_cli(["--from", "en", "--to", "ja"], input_text="")
        assert result.returncode == 0
        assert result.stdout == ""

    def test_single_line(self):
        result = run_cli(["--from", "en", "--to", "ja"], input_text="Hello")
        assert result.returncode == 0
        assert result.stdout == "こんにちは\n"

    def test_multiple_lines(self):
        result = run_cli(
            ["--from", "en", "--to", "ja"],
            input_text="Hello\nGoodbye\n",
        )
        assert result.returncode == 0
        assert result.stdout == "こんにちは\nさようなら\n"

    def test_whitespace_only_input(self):
        result = run_cli(
            ["--from", "en", "--to", "ja"],
            input_text="   \n  \n   ",
        )
        assert result.returncode == 0
        assert result.stdout == "   \n  \n   \n"

    def test_stdin_with_blank_lines(self):
        """Blank lines in stdin should be preserved in output."""
        result = run_cli(
            ["--from", "en", "--to", "ja"],
            input_text="Hello\n\nGoodbye",
        )
        assert result.returncode == 0
        assert result.stdout == "こんにちは\n\nさようなら\n"

    def test_tab_only_lines(self):
        """Tab-only lines should be preserved as-is in output."""
        result = run_cli(
            ["--from", "en", "--to", "ja"],
            input_text="Hello\n\t\t\nGoodbye",
        )
        assert result.returncode == 0
        assert result.stdout == "こんにちは\n\t\t\nさようなら\n"

    def test_mixed_whitespace_and_text(self):
        """Mix of text, blank, and whitespace-only lines."""
        result = run_cli(
            ["--from", "en", "--to", "ja"],
            input_text="Hello\n\n  \t \nGoodbye",
        )
        assert result.returncode == 0
        assert result.stdout == "こんにちは\n\n  \t \nさようなら\n"


# ── Argument text translation ──


class TestArgumentText:
    def test_positional_text(self):
        result = run_cli(["Hello", "--from", "en", "--to", "ja"])
        assert result.returncode == 0
        assert result.stdout == "こんにちは\n"

    def test_text_flag(self):
        result = run_cli(["--text", "Hello", "--from", "en", "--to", "ja"])
        assert result.returncode == 0
        assert result.stdout == "こんにちは\n"

    def test_positional_newline_literal(self):
        """Literal \\n in positional text is passed as-is to translation API."""
        result = run_cli(["Hello\\nGoodbye", "--from", "en", "--to", "ja"])
        assert result.returncode == 0
        assert result.stdout == "こんにちは、さようなら\n"

    def test_text_flag_newline_literal(self):
        """Literal \\n in --text is passed as-is to translation API."""
        result = run_cli(["--text", "Hello\\nGoodbye", "--from", "en", "--to", "ja"])
        assert result.returncode == 0
        assert result.stdout == "こんにちは、さようなら\n"

    def test_positional_with_exclamation(self):
        """atrans 'Hello!\nWorld !' --from en --to ja"""
        result = run_cli(["Hello!\\nWorld !", "--from", "en", "--to", "ja"])
        assert result.returncode == 0
        assert result.stdout == "こんにちは！ 世界！\n"

    def test_tab_literal(self):
        """Literal \\t is passed as-is to translation API."""
        result = run_cli(["Hello\\tWorld", "--from", "en", "--to", "ja"])
        assert result.returncode == 0
        assert result.stdout == "こんにちは\\tWorld\n"

    def test_backslash_literal(self):
        """Literal backslash is passed as-is to translation API."""
        result = run_cli(["Hello \\ World", "--from", "en", "--to", "ja"])
        assert result.returncode == 0
        assert result.stdout == "こんにちは \\ 世界\n"

    def test_quoted_text(self):
        """Quoted text with special chars (shell handles outer quotes)."""
        result = run_cli(['"Hello"', "--from", "en", "--to", "ja"])
        assert result.returncode == 0
        assert result.stdout == "こんにちは\n"

    def test_emoji(self):
        result = run_cli(["I love you 😊", "--from", "en", "--to", "ja"])
        assert result.returncode == 0
        assert result.stdout == "あなたを愛しています 😊\n"

    def test_symbols(self):
        result = run_cli(["Price: $100 & 50% off!", "--from", "en", "--to", "ja"])
        assert result.returncode == 0
        assert result.stdout == "価格：$100、50%オフ！\n"


# ── File input (--file) ──


class TestFileInput:
    def test_file_single_line(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            f.write("Hello\n")
            f.flush()
            result = run_cli(["--file", f.name, "--from", "en", "--to", "ja"])
        os.unlink(f.name)
        assert result.returncode == 0
        assert result.stdout == "こんにちは\n"

    def test_file_multiple_lines(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            f.write("Hello\nGoodbye\n")
            f.flush()
            result = run_cli(["--file", f.name, "--from", "en", "--to", "ja"])
        os.unlink(f.name)
        assert result.returncode == 0
        assert result.stdout == "こんにちは\nさようなら\n"

    def test_file_not_found(self):
        result = run_cli(["--file", "/nonexistent/path.txt", "--from", "en", "--to", "ja"])
        assert result.returncode != 0
        assert "Cannot read file" in result.stderr or "Error" in result.stderr

    def test_file_empty(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            f.write("")
            f.flush()
            result = run_cli(["--file", f.name, "--from", "en", "--to", "ja"])
        os.unlink(f.name)
        assert result.returncode == 0
        assert result.stdout == ""

    def test_file_crlf(self):
        """CRLF line endings should be handled correctly."""
        with tempfile.NamedTemporaryFile(mode="wb", suffix=".txt", delete=False) as f:
            f.write(b"Hello\r\nGoodbye\r\n")
            f.flush()
            result = run_cli(["--file", f.name, "--from", "en", "--to", "ja"])
        os.unlink(f.name)
        assert result.returncode == 0
        assert result.stdout == "こんにちは\nさようなら\n"

    def test_file_no_extension(self):
        """Files without extension should work."""
        with tempfile.NamedTemporaryFile(mode="w", suffix="", delete=False) as f:
            f.write("Hello\n")
            f.flush()
            result = run_cli(["--file", f.name, "--from", "en", "--to", "ja"])
        os.unlink(f.name)
        assert result.returncode == 0
        assert result.stdout == "こんにちは\n"

    def test_file_with_blank_lines(self):
        """Blank lines in file should be preserved in output."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            f.write("Hello\n\nGoodbye\n")
            f.flush()
            result = run_cli(["--file", f.name, "--from", "en", "--to", "ja"])
        os.unlink(f.name)
        assert result.returncode == 0
        assert result.stdout == "こんにちは\n\nさようなら\n"

    def test_file_binary_content(self):
        """Binary (non-UTF-8) content should produce an error."""
        with tempfile.NamedTemporaryFile(mode="wb", suffix=".bin", delete=False) as f:
            f.write(b"\x80\x81\x82\xff\xfe")
            f.flush()
            result = run_cli(["--file", f.name, "--from", "en", "--to", "ja"])
        os.unlink(f.name)
        assert result.returncode != 0
        assert "Error" in result.stderr


# ── Input source conflict detection ──


class TestInputConflict:
    def test_text_flag_and_file(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            f.write("Hello\n")
            f.flush()
            result = run_cli(
                ["--text", "World", "--file", f.name, "--from", "en", "--to", "ja"],
            )
        os.unlink(f.name)
        assert result.returncode != 0
        assert "Multiple input sources" in result.stderr

    def test_positional_and_text_flag(self):
        result = run_cli(
            ["Hello", "--text", "World", "--from", "en", "--to", "ja"],
        )
        assert result.returncode != 0
        assert "Multiple input sources" in result.stderr

    def test_positional_and_file(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            f.write("Hello\n")
            f.flush()
            result = run_cli(
                ["World", "--file", f.name, "--from", "en", "--to", "ja"],
            )
        os.unlink(f.name)
        assert result.returncode != 0
        assert "Multiple input sources" in result.stderr

    def test_no_input(self):
        """No explicit source and stdin is a TTY → error."""
        master, slave = pty.openpty()
        try:
            result = subprocess.run(
                [CLI, "--from", "en", "--to", "ja"],
                stdin=slave,
                capture_output=True,
                text=True,
                timeout=10,
            )
        finally:
            os.close(master)
            os.close(slave)
        assert result.returncode != 0
        assert "No input" in result.stderr

    def test_explicit_source_ignores_stdin(self):
        """When --text is given, stdin data should be ignored (no conflict)."""
        result = run_cli(
            ["--text", "Hello", "--from", "en", "--to", "ja"],
            input_text="World",
        )
        assert result.returncode == 0
        assert result.stdout == "こんにちは\n"


# ── Short-form language keys ──


class TestShortFormKeys:
    @pytest.mark.parametrize(
        "src,tgt,text,expected",
        [
            ("ja", "en", "こんにちは", "Hello"),
            ("en", "ja", "Hello", "こんにちは"),
            ("en", "ko", "Hello", "안녕"),
            ("ja", "zh-Hans", "こんにちは", "你好"),
            ("ja", "zh-Hant", "こんにちは", "你好"),
            ("ko", "ja", "안녕하세요", "こんにちは"),
            ("fr", "de", "Bonjour", "Guten Morgen"),
            ("es", "pt", "Hola", "Olá"),
        ],
        ids=[
            "ja->en", "en->ja", "en->ko", "ja->zh-Hans",
            "ja->zh-Hant", "ko->ja", "fr->de", "es->pt",
        ],
    )
    def test_short_form(self, src: str, tgt: str, text: str, expected: str):
        result = run_cli(["--from", src, "--to", tgt], input_text=text)
        assert result.returncode == 0, f"stderr: {result.stderr}"
        assert result.stdout == expected + "\n"
