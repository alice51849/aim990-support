#!/usr/bin/env python3
"""Fail-closed checks for Aim990 exact-50 query-localized web pages."""

from __future__ import annotations

import hashlib
import html
import json
import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent
METADATA_ROOT = ROOT.parent / "Metadata" / "aso" / "loc"
BASE_URL = "https://alice51849.github.io/aim990-support/"
EMAIL = "hourstag.app@gmail.com"
OFFICIAL_LOCALES = (
    "ar-SA", "bn-BD", "ca", "zh-Hans", "zh-Hant", "hr", "cs", "da",
    "nl-NL", "en-AU", "en-CA", "en-GB", "en-US", "fi", "fr-CA",
    "fr-FR", "de-DE", "el", "gu-IN", "he", "hi", "hu", "id", "it",
    "ja", "kn-IN", "ko", "ms", "ml-IN", "mr-IN", "no", "or-IN", "pl",
    "pt-BR", "pt-PT", "pa-IN", "ro", "ru", "sk", "sl-SI", "es-MX",
    "es-ES", "sv", "ta-IN", "te-IN", "th", "tr", "uk", "ur-PK", "vi",
)
REQUIRED_FIELDS = frozenset(
    (
        "locale",
        "sourceLocale",
        "languageName",
        "direction",
        "supportTitle",
        "supportDescription",
        "supportUrl",
        "supportBody",
        "privacyTitle",
        "privacyDescription",
        "privacyPolicyUrl",
        "privacyBody",
        "legalNotice",
    )
)
RAW_KEY_PATTERN = re.compile(
    r"\{\{[^{}]+\}\}|"
    r"\b(?:supportTitle|privacyTitle|supportDescription|privacyDescription|"
    r"contactLabel|languageName|translation[_ -]?missing|missing[_ -]?key)\b|"
    r"data-(?:i18n|l10n)=",
    flags=re.IGNORECASE,
)
SCRIPT_RULES = {
    "ar-SA": r"[\u0600-\u06ff]",
    "bn-BD": r"[\u0980-\u09ff]",
    "zh-Hans": r"[\u4e00-\u9fff]",
    "zh-Hant": r"[\u4e00-\u9fff]",
    "el": r"[\u0370-\u03ff]",
    "gu-IN": r"[\u0a80-\u0aff]",
    "he": r"[\u0590-\u05ff]",
    "hi": r"[\u0900-\u097f]",
    "ja": r"[\u3040-\u30ff\u4e00-\u9fff]",
    "kn-IN": r"[\u0c80-\u0cff]",
    "ko": r"[\uac00-\ud7af]",
    "ml-IN": r"[\u0d00-\u0d7f]",
    "mr-IN": r"[\u0900-\u097f]",
    "or-IN": r"[\u0b00-\u0b7f]",
    "pa-IN": r"[\u0a00-\u0a7f]",
    "ru": r"[\u0400-\u04ff]",
    "ta-IN": r"[\u0b80-\u0bff]",
    "te-IN": r"[\u0c00-\u0c7f]",
    "th": r"[\u0e00-\u0e7f]",
    "uk": r"[\u0400-\u04ff]",
    "ur-PK": r"[\u0600-\u06ff]",
}
PROHIBITED_POSITIVE_CLAIMS = (
    "hit your score goal",
    "ace the toeic",
    "your path to toeic success",
    "achieve your target score",
    "achieve a score of 990",
    "score of 990 in just 30 days",
    "official toeic app",
    "official toeic coach",
    "official toeic course",
)


def catalog() -> dict:
    text = (ROOT / "locales.js").read_text(encoding="utf-8")
    prefix = "window.AIM990_LOCALES = "
    if not text.startswith(prefix) or not text.rstrip().endswith(";"):
        raise ValueError("locales.js is not a JSON-backed AIM990_LOCALES assignment")
    return json.loads(text[len(prefix):].rstrip()[:-1])


def visible_text(markup: str) -> str:
    text = re.sub(r"<!--.*?-->", " ", markup, flags=re.DOTALL)
    text = re.sub(r"<(?:script|style)\b.*?</(?:script|style)>", " ", text, flags=re.DOTALL)
    text = re.sub(r"<[^>]+>", " ", text)
    return " ".join(html.unescape(text).split())


def normalized(value: str) -> str:
    return " ".join(value.split())


def check_catalog(payload: dict) -> list[str]:
    errors = []
    if set(payload) != set(OFFICIAL_LOCALES):
        errors.append(
            "locales.js locale set differs from Apple official exact-50"
        )
        return errors

    hashes = {"supportBody": {}, "privacyBody": {}}
    for locale in OFFICIAL_LOCALES:
        entry = payload.get(locale)
        if not isinstance(entry, dict):
            errors.append(f"{locale}: locale entry is not an object")
            continue
        missing = sorted(REQUIRED_FIELDS - set(entry))
        if missing:
            errors.append(f"{locale}: missing fields {missing}")
            continue
        if entry["locale"] != locale or entry["sourceLocale"] != locale:
            errors.append(f"{locale}: locale/sourceLocale indicates fallback")
        if entry["direction"] not in {"ltr", "rtl"}:
            errors.append(f"{locale}: invalid direction")
        expected_direction = "rtl" if locale in {"ar-SA", "he", "ur-PK"} else "ltr"
        if entry["direction"] != expected_direction:
            errors.append(f"{locale}: direction must be {expected_direction}")
        expected_urls = {
            "supportUrl": f"{BASE_URL}?lang={locale}",
            "privacyPolicyUrl": f"{BASE_URL}privacy.html?lang={locale}",
        }
        for field, expected in expected_urls.items():
            if entry[field] != expected:
                errors.append(f"{locale}: {field} is not the exact query URL")
        for field in REQUIRED_FIELDS:
            if not isinstance(entry[field], str) or not entry[field].strip():
                errors.append(f"{locale}: {field} is empty")

        combined_visible = []
        for field, minimum_marker in (
            ("supportBody", '<details class="faq">'),
            ("privacyBody", '<section class="card">'),
        ):
            body = entry[field]
            visible = visible_text(body)
            combined_visible.append(visible)
            if EMAIL not in visible:
                errors.append(f"{locale}: {field} does not visibly show {EMAIL}")
            if "alice51849@hotmail.com" in body:
                errors.append(f"{locale}: {field} contains the prohibited public email")
            if RAW_KEY_PATTERN.search(body):
                errors.append(f"{locale}: {field} exposes a raw localization key")
            if body.count(minimum_marker) < 6:
                errors.append(f"{locale}: {field} is missing substantive localized sections")
            digest = hashlib.sha256(normalized(visible).encode()).hexdigest()
            hashes[field].setdefault(digest, []).append(locale)

        combined = " ".join(combined_visible)
        if "TOEIC" not in entry["legalNotice"] or "ETS" not in entry["legalNotice"]:
            errors.append(f"{locale}: legal notice does not retain TOEIC/ETS disclosure")
        if normalized(entry["legalNotice"]) not in normalized(combined):
            errors.append(f"{locale}: legal notice is not visibly rendered")
        script = SCRIPT_RULES.get(locale)
        if script and len(re.findall(script, combined)) < 12:
            errors.append(f"{locale}: localized pages do not contain enough native-script text")
        folded_support = visible_text(entry["supportBody"]).casefold()
        for phrase in PROHIBITED_POSITIVE_CLAIMS:
            if phrase in folded_support:
                errors.append(f"{locale}: prohibited score/official claim: {phrase!r}")

    for field, groups in hashes.items():
        duplicates = [locales for locales in groups.values() if len(locales) > 1]
        if duplicates:
            errors.append(f"{field}: duplicated rendered locale bodies {duplicates}")
    return errors


def check_html(page: str) -> list[str]:
    errors = []
    filename = "index.html" if page == "support" else "privacy.html"
    text = (ROOT / filename).read_text(encoding="utf-8")
    prefix = BASE_URL if page == "support" else f"{BASE_URL}privacy.html"
    pairs = re.findall(
        r'<link rel="alternate" hreflang="([^"]+)" href="([^"]+)">',
        text,
    )
    alternates = {locale: url for locale, url in pairs if locale != "x-default"}
    if set(alternates) != set(OFFICIAL_LOCALES):
        errors.append(f"{filename}: hreflang set is not official exact-50")
    for locale in OFFICIAL_LOCALES:
        expected = f"{prefix}?lang={locale}"
        if alternates.get(locale) != expected:
            errors.append(f"{filename}: {locale} hreflang URL is not exact")
    expected_default = f"{prefix}?lang=en-US"
    if ("x-default", expected_default) not in pairs:
        errors.append(f"{filename}: x-default is missing or incorrect")
    if f'<body data-page="{page}">' not in text:
        errors.append(f"{filename}: page identity is missing")
    return errors


def check_runtime() -> list[str]:
    errors = []
    text = (ROOT / "site.js").read_text(encoding="utf-8")
    required = (
        'new URLSearchParams(window.location.search).get("lang")',
        "Object.hasOwn(locales, requested)",
        "copy.sourceLocale !== locale",
        'document.getElementById("localized-page").innerHTML = copy[bodyKey]',
        "panel.replaceChildren()",
    )
    for marker in required:
        if marker not in text:
            errors.append(f"site.js: missing runtime contract {marker!r}")
    if "navigator.language" in text or "fallbackLocale" in text:
        errors.append("site.js: locale fallback/detection is not allowed")
    return errors


def check_help_and_sitemap() -> list[str]:
    errors = []
    legacy_help = sorted(ROOT.glob("help*.html"))
    if legacy_help:
        errors.append(
            "legacy duplicated help pages remain: "
            + ", ".join(path.name for path in legacy_help)
        )
    for path in sorted(ROOT.glob("*/*.html")):
        text = path.read_text(encoding="utf-8")
        if re.search(r"href=\"\.\./help(?:\.[^\"]+)?\.html\"", text):
            errors.append(f"{path.relative_to(ROOT)}: legacy help link remains")
    sitemap = (ROOT / "sitemap.xml").read_text(encoding="utf-8")
    expected = (
        "metadata/aim990-diagnosis-prescription-sitemap.xml"
    )
    if "<sitemapindex" not in sitemap or expected not in sitemap:
        errors.append("sitemap.xml is not the Aim990 diagnostic sitemap index")
    if not (ROOT / expected).is_file():
        errors.append("Aim990 diagnostic sitemap payload is missing")
    robots = (ROOT / "robots.txt").read_text(encoding="utf-8")
    if f"Sitemap: {BASE_URL}sitemap.xml" not in robots:
        errors.append("robots.txt does not reference the canonical sitemap index")
    return errors


def check_metadata() -> list[str]:
    errors = []
    files = {path.stem: path for path in METADATA_ROOT.glob("*.json")}
    if set(files) != set(OFFICIAL_LOCALES):
        return ["metadata locale set differs from Apple official exact-50"]
    for locale in OFFICIAL_LOCALES:
        try:
            payload = json.loads(files[locale].read_text(encoding="utf-8"))
        except (OSError, UnicodeError, json.JSONDecodeError) as error:
            errors.append(f"{locale}: metadata cannot be read: {error}")
            continue
        expected = {
            "supportUrl": f"{BASE_URL}?lang={locale}",
            "privacyPolicyUrl": f"{BASE_URL}privacy.html?lang={locale}",
        }
        for field, value in expected.items():
            if payload.get(field) != value:
                errors.append(f"{locale}: metadata {field} is not the exact query URL")
    return errors


def main() -> int:
    try:
        payload = catalog()
    except (OSError, UnicodeError, json.JSONDecodeError, ValueError) as error:
        print(f"BLOCK: {error}")
        return 1
    errors = (
        check_catalog(payload)
        + check_html("support")
        + check_html("privacy")
        + check_runtime()
        + check_help_and_sitemap()
        + check_metadata()
    )
    if errors:
        print(f"BLOCK ({len(errors)} issue(s))")
        for error in errors:
            print(f"- {error}")
        return 1
    print(
        "PASS: Aim990 support/privacy exact-50 query locales, contact, "
        "legal copy, and metadata URLs"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
