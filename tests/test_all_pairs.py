"""
All language pair combination tests for atrans CLI.

This test file covers 416 valid translation pairs (21 languages × 20 targets
minus same-languageCode pairs). Separated from main tests for faster
iteration during development.

Requires:
    - The CLI binary built at .build/release/atrans
    - Run: swift build -c release
    - Run: python -m pytest tests/test_all_pairs.py -v
"""

import os
import subprocess
import pytest

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CLI = os.path.join(PROJECT_ROOT, ".build", "release", "atrans")

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

SAME_LANGUAGE_PAIRS = {
    ("en-Latn-GB", "en-Latn-US"),
    ("en-Latn-US", "en-Latn-GB"),
    ("zh-Hans-CN", "zh-Hant-TW"),
    ("zh-Hant-TW", "zh-Hans-CN"),
}


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


def _valid_pairs() -> list[tuple[str, str]]:
    """416 valid translation pairs (all combinations minus same-languageCode)."""
    pairs = []
    for src in SUPPORTED_LANGUAGES:
        for tgt in SUPPORTED_LANGUAGES:
            if src != tgt and (src, tgt) not in SAME_LANGUAGE_PAIRS:
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
