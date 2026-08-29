#!/usr/bin/env python3
"""Set only Aim990's exact-50 support and privacy URL fields."""

from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent
METADATA_ROOT = ROOT.parent / "Metadata" / "aso" / "loc"
BASE_URL = "https://alice51849.github.io/aim990-support/"
OFFICIAL_LOCALES = (
    "ar-SA", "bn-BD", "ca", "zh-Hans", "zh-Hant", "hr", "cs", "da",
    "nl-NL", "en-AU", "en-CA", "en-GB", "en-US", "fi", "fr-CA",
    "fr-FR", "de-DE", "el", "gu-IN", "he", "hi", "hu", "id", "it",
    "ja", "kn-IN", "ko", "ms", "ml-IN", "mr-IN", "no", "or-IN", "pl",
    "pt-BR", "pt-PT", "pa-IN", "ro", "ru", "sk", "sl-SI", "es-MX",
    "es-ES", "sv", "ta-IN", "te-IN", "th", "tr", "uk", "ur-PK", "vi",
)
URL_FIELDS = frozenset(("supportUrl", "privacyPolicyUrl"))


def main() -> int:
    files = {path.stem: path for path in METADATA_ROOT.glob("*.json")}
    if set(files) != set(OFFICIAL_LOCALES):
        raise SystemExit("metadata locale set is not Apple official exact-50")
    changed = 0
    for locale in OFFICIAL_LOCALES:
        path = files[locale]
        payload = json.loads(path.read_text(encoding="utf-8"))
        before = {key: value for key, value in payload.items() if key not in URL_FIELDS}
        expected = {
            "supportUrl": f"{BASE_URL}?lang={locale}",
            "privacyPolicyUrl": f"{BASE_URL}privacy.html?lang={locale}",
        }
        if any(payload.get(key) != value for key, value in expected.items()):
            payload.update(expected)
            path.write_text(
                json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )
            changed += 1
        after = {
            key: value
            for key, value in json.loads(path.read_text(encoding="utf-8")).items()
            if key not in URL_FIELDS
        }
        if before != after:
            raise SystemExit(f"{locale}: non-URL metadata changed")
    print(f"Verified 50 locales; updated URL fields in {changed} file(s).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
