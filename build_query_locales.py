#!/usr/bin/env python3
"""Build the exact-50 query-localized Aim990 support and privacy pages."""

from __future__ import annotations

import html
import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parent
METADATA_ROOT = ROOT.parent / "Metadata" / "aso" / "loc"
BASE_URL = "https://alice51849.github.io/aim990-support/"
EMAIL = "hourstag.app@gmail.com"
APP_STORE_URL = "https://apps.apple.com/app/id6784974530"
OFFICIAL_LOCALES = (
    "ar-SA", "bn-BD", "ca", "zh-Hans", "zh-Hant", "hr", "cs", "da",
    "nl-NL", "en-AU", "en-CA", "en-GB", "en-US", "fi", "fr-CA",
    "fr-FR", "de-DE", "el", "gu-IN", "he", "hi", "hu", "id", "it",
    "ja", "kn-IN", "ko", "ms", "ml-IN", "mr-IN", "no", "or-IN", "pl",
    "pt-BR", "pt-PT", "pa-IN", "ro", "ru", "sk", "sl-SI", "es-MX",
    "es-ES", "sv", "ta-IN", "te-IN", "th", "tr", "uk", "ur-PK", "vi",
)
GENERATED_LOCALES = frozenset(("en-AU", "en-CA", "en-GB", "en-US", "or-IN"))


def metadata(locale: str) -> dict:
    return json.loads((METADATA_ROOT / f"{locale}.json").read_text(encoding="utf-8"))


def legal_notice(locale: str) -> str:
    paragraphs = metadata(locale)["description"].split("\n\n")
    for paragraph in reversed(paragraphs):
        if "ETS" in paragraph and "TOEIC" in paragraph:
            return paragraph.strip()
    raise ValueError(f"{locale}: metadata description has no ETS/TOEIC notice")


def match(pattern: str, text: str, label: str) -> str:
    found = re.search(pattern, text, flags=re.DOTALL)
    if not found:
        raise ValueError(f"cannot extract {label}")
    return found.group(1)


def normalized_body(text: str, notice: str) -> str:
    body = match(r"<body[^>]*>(.*)</body>", text, "body").strip()
    body = body.replace('src="../logo.png"', 'src="logo.png"')
    body = body.replace('href="../help.', 'href="help.')
    body = re.sub(
        r'(<div class="language-panel">).*?(</div></details>)',
        r"\1\2",
        body,
        count=1,
        flags=re.DOTALL,
    )
    footer_end = body.rfind("</footer>")
    if footer_end < 0:
        raise ValueError("localized page has no footer")
    notice_html = (
        '<p class="legal-notice">'
        + html.escape(notice, quote=False)
        + "</p>"
    )
    return body[:footer_end] + notice_html + body[footer_end:]


def source_entry(locale: str) -> dict:
    pages = {}
    for page in ("support", "privacy"):
        text = (ROOT / locale / f"{page}.html").read_text(encoding="utf-8")
        pages[f"{page}Title"] = html.unescape(
            match(r"<title>(.*?)</title>", text, f"{locale} {page} title")
        )
        pages[f"{page}Description"] = html.unescape(
            match(
                r'<meta name="description" content="(.*?)">',
                text,
                f"{locale} {page} description",
            )
        )
        pages[f"{page}Body"] = normalized_body(text, legal_notice(locale))
        if page == "support":
            pages["languageName"] = html.unescape(
                match(
                    r'<details class="language"><summary[^>]*>.*?<span>(.*?)</span>',
                    text,
                    f"{locale} language name",
                )
            )
            html_attributes = match(
                r"<html([^>]*)>",
                text,
                f"{locale} html attributes",
            )
            direction = re.search(r'\sdir="([^"]+)"', html_attributes)
            pages["direction"] = direction.group(1) if direction else "ltr"
    return {
        "locale": locale,
        "sourceLocale": locale,
        "supportUrl": f"{BASE_URL}?lang={locale}",
        "privacyPolicyUrl": f"{BASE_URL}privacy.html?lang={locale}",
        **pages,
        "legalNotice": legal_notice(locale),
    }


def english_copy(locale: str) -> dict:
    is_us = locale == "en-US"
    is_ca = locale == "en-CA"
    centre = "Center" if is_us else "Centre"
    practise = "practice" if is_us or is_ca else "practise"
    device = "device"
    return {
        "languageName": {
            "en-AU": "English (Australia)",
            "en-CA": "English (Canada)",
            "en-GB": "English (United Kingdom)",
            "en-US": "English (United States)",
        }[locale],
        "direction": "ltr",
        "appName": "Aim990",
        "navHome": "Home",
        "navSupport": "Support",
        "navPrivacy": "Privacy",
        "languageLabel": "Language",
        "supportTitle": f"Aim990 Support {centre} — FAQ and troubleshooting",
        "supportDescription": (
            f"Common Aim990 questions, troubleshooting steps, and a direct way "
            f"to contact support for your {device}."
        ),
        "supportEyebrow": f"Support {centre}",
        "supportLead": (
            f"Answers to common Aim990 questions, checks you can try yourself, "
            f"and a direct way to reach support."
        ),
        "faqHeading": "Frequently asked questions",
        "faqs": (
            (
                "Do I need to create an account?",
                "No. Aim990 does not require an account or sign-in. You can start using it after installation.",
            ),
            (
                "Does Aim990 work offline?",
                "Yes. Core diagnosis, prescribed practice, review and progress tracking work on your device. Downloading the app and making or restoring a purchase require the App Store and an internet connection.",
            ),
            (
                "Is Aim990 a subscription?",
                "No. The full unlock is a one-time in-app purchase with no recurring charge.",
            ),
            (
                "What can I use before purchasing?",
                "You can use the included free experience and review the locked feature previews. The one-time purchase unlocks the complete training content.",
            ),
            (
                "How do I restore my purchase on another device?",
                "Sign in with the same Apple Account used for the purchase, open Aim990, go to Profile, and choose Restore Purchases.",
            ),
            (
                "How do I remove my study data?",
                "Delete the relevant content in Aim990 where available. To remove all locally stored app data, delete the app from the device. A device backup may still contain a copy until that backup is replaced or removed.",
            ),
            (
                "How do I update Aim990?",
                "Open the App Store, select your profile picture, refresh the available updates, and choose Update beside Aim990. Automatic app updates can also be enabled in Settings.",
            ),
            (
                "What should I include in a bug report?",
                f"Email {EMAIL} with your device model, iOS version, Aim990 version, steps to reproduce the issue, and a screenshot or screen recording if possible.",
            ),
        ),
        "troubleshootingHeading": "Troubleshooting",
        "troubleshootingIntro": "Try these steps first",
        "steps": (
            "Force quit Aim990, then open it again.",
            "Restart your iPhone or iPad to clear temporary display or performance issues.",
            "Check the App Store for the latest Aim990 update.",
            "Open Settings → General → Software Update and install any available iOS update.",
            f"If a layout looks wrong, temporarily return Display Zoom and larger text to their standard settings, then check again. You can re-enable your preferred accessibility settings after testing and tell us what changed at {EMAIL}.",
        ),
        "contactHeading": "Contact support",
        "contactCopy": (
            f"Email {EMAIL}. Include your device model, iOS version, app version, "
            f"and what you tapped immediately before the issue appeared."
        ),
        "appStoreLabel": "View Aim990 on the App Store",
        "noTracking": "This site uses no third-party tracking, advertising, or analytics.",
        "privacyTitle": "Aim990 Privacy Policy",
        "privacyDescription": (
            "Aim990 requires no account, collects no personal data, and keeps study data on your device."
        ),
        "privacyEyebrow": "Privacy Policy",
        "privacyLead": (
            "This page explains what Aim990 processes, where information stays, and how you control it."
        ),
        "updated": "Last updated: 27 June 2026" if not is_us else "Last updated: June 27, 2026",
        "privacyCards": (
            (
                "Data we collect",
                "None. Aim990 does not collect, transmit, sell, or use personal information for advertising or analytics. There is no developer account or sign-in.",
            ),
            (
                "Data stored on your device",
                "Your answers, accuracy, practice evidence, score goal, test date, streaks, achievements, and settings stay in the app's local storage. The developer cannot see them. Deleting the app removes its local data.",
            ),
            (
                "Speech and audio",
                "Listening practice uses speech provided by iOS on your device. Aim990 does not record or upload your voice or listening audio.",
            ),
            (
                "Purchases",
                "The one-time in-app purchase is processed by Apple through the App Store and StoreKit. The developer never receives your payment details. You can restore the purchase with the same Apple Account.",
            ),
            (
                "Children's privacy",
                "Aim990 does not knowingly collect information from anyone, including children. The app does not request a child's name, birthday, contact details, photos, or health information.",
            ),
            (
                "Changes to this policy",
                "If an Aim990 feature changes in a way that affects this policy, this page and its last-updated date will be revised.",
            ),
            (
                "Contact",
                f"For privacy questions, email {EMAIL}.",
            ),
        ),
        "privacyNote": "",
        "practise": practise,
    }


ODIA_COPY = {
    "languageName": "ଓଡ଼ିଆ",
    "direction": "ltr",
    "appName": "Aim990: ଇଂରାଜୀ କୋଚ୍",
    "navHome": "ମୁଖ୍ୟ ପୃଷ୍ଠା",
    "navSupport": "ସହାୟତା",
    "navPrivacy": "ଗୋପନୀୟତା",
    "languageLabel": "ଭାଷା",
    "supportTitle": "Aim990 ସହାୟତା — ସାଧାରଣ ପ୍ରଶ୍ନ ଓ ସମସ୍ୟା ସମାଧାନ",
    "supportDescription": "Aim990 ବିଷୟରେ ସାଧାରଣ ପ୍ରଶ୍ନ, ନିଜେ ଯାଞ୍ଚ କରିବା ପଦକ୍ଷେପ ଏବଂ ସିଧାସଳଖ ସହାୟତା ପାଇବାର ଉପାୟ।",
    "supportEyebrow": "ସହାୟତା କେନ୍ଦ୍ର",
    "supportLead": "Aim990 ବିଷୟରେ ଆମେ ସର୍ବାଧିକ ପାଉଥିବା ପ୍ରଶ୍ନ, ଆପଣ ନିଜେ କରିପାରିବା ଯାଞ୍ଚ ଏବଂ ସହାୟତା ସହ ସିଧାସଳଖ ଯୋଗାଯୋଗର ଉପାୟ।",
    "faqHeading": "ସାଧାରଣ ପ୍ରଶ୍ନ",
    "faqs": (
        ("ଖାତା ଖୋଲିବା ଦରକାର କି?", "ନା। Aim990 ବ୍ୟବହାର ପାଇଁ ଖାତା କିମ୍ବା ସାଇନ୍-ଇନ୍ ଦରକାର ନାହିଁ। ଇନ୍‌ଷ୍ଟଲ୍ କରିବା ପରେ ସିଧାସଳଖ ଆରମ୍ଭ କରିପାରିବେ।"),
        ("ଇଣ୍ଟରନେଟ୍ ଛଡ଼ା Aim990 କାମ କରେ କି?", "ହଁ। ମୁଖ୍ୟ ନିଦାନ, ନିର୍ଦ୍ଦିଷ୍ଟ ଅଭ୍ୟାସ, ପୁନରାବୃତ୍ତି ଏବଂ ପ୍ରଗତି ରେକର୍ଡ ଆପଣଙ୍କ ଡିଭାଇସ୍‌ରେ କାମ କରେ। App Store ରୁ ଡାଉନଲୋଡ୍ ଏବଂ କିଣା କିମ୍ବା ପୁନରୁଦ୍ଧାର ପାଇଁ ଇଣ୍ଟରନେଟ୍ ଦରକାର।"),
        ("ଏହା ସଦସ୍ୟତା ନା?", "ନା। ସମ୍ପୂର୍ଣ୍ଣ ଅନଲକ୍ ହେଉଛି ଏକଥରିଆ App ମଧ୍ୟର କିଣା; ପୁନରାବୃତ୍ତି ଶୁଳ୍କ ନାହିଁ।"),
        ("କିଣିବା ପୂର୍ବରୁ କ’ଣ ବ୍ୟବହାର କରିପାରିବି?", "ମାଗଣାରେ ଥିବା ଅନୁଭବକୁ ବ୍ୟବହାର କରିପାରିବେ ଏବଂ ଲକ୍ ଥିବା ବୈଶିଷ୍ଟ୍ୟର ପୂର୍ବଦର୍ଶନ ଦେଖିପାରିବେ। ଏକଥରିଆ କିଣା ସମ୍ପୂର୍ଣ୍ଣ ଅଭ୍ୟାସ ବିଷୟବସ୍ତୁ ଖୋଲିଦେଏ।"),
        ("ଅନ୍ୟ ଡିଭାଇସ୍‌ରେ କିଣାକୁ କିପରି ପୁନରୁଦ୍ଧାର କରିବି?", "କିଣିବାବେଳେ ବ୍ୟବହାର କରିଥିବା ସେହି Apple Account ରେ ସାଇନ୍-ଇନ୍ କରନ୍ତୁ, Aim990 ରେ Profile ଖୋଲନ୍ତୁ ଏବଂ Restore Purchases ବାଛନ୍ତୁ।"),
        ("ମୋର ଅଧ୍ୟୟନ ତଥ୍ୟ କିପରି ମିଟାଇବି?", "Aim990 ଭିତରେ ଯେଉଁଠି ବିକଳ୍ପ ଅଛି ସେଠାରେ ସମ୍ପର୍କିତ ବିଷୟବସ୍ତୁ ମିଟାନ୍ତୁ। ସମସ୍ତ ସ୍ଥାନୀୟ App ତଥ୍ୟ ହଟାଇବାକୁ ଡିଭାଇସ୍‌ରୁ App କୁ ଡିଲିଟ୍ କରନ୍ତୁ। ପୁରୁଣା ଡିଭାଇସ୍ ବ୍ୟାକଅପ୍‌ରେ ଏକ ପ୍ରତିଲିପି ରହିପାରେ।"),
        ("Aim990 କୁ କିପରି ଅଦ୍ୟତନ କରିବି?", "App Store ଖୋଲନ୍ତୁ, ଆପଣଙ୍କ ପ୍ରୋଫାଇଲ୍ ଚିତ୍ର ବାଛନ୍ତୁ, ଉପଲବ୍ଧ ଅଦ୍ୟତନକୁ ପୁନଃତାଜା କରନ୍ତୁ ଏବଂ Aim990 ପାଖରେ Update ବାଛନ୍ତୁ।"),
        ("ତ୍ରୁଟି ରିପୋର୍ଟରେ କ’ଣ ଦେବି?", f"{EMAIL} କୁ ଆପଣଙ୍କ ଡିଭାଇସ୍ ମଡେଲ୍, iOS ସଂସ୍କରଣ, Aim990 ସଂସ୍କରଣ, ସମସ୍ୟା ପୁଣି ଘଟାଇବାର ପଦକ୍ଷେପ ଏବଂ ସମ୍ଭବ ହେଲେ ସ୍କ୍ରିନ୍‌ଶଟ୍ କିମ୍ବା ସ୍କ୍ରିନ୍ ରେକର୍ଡିଂ ପଠାନ୍ତୁ।"),
    ),
    "troubleshootingHeading": "ସମସ୍ୟା ସମାଧାନ",
    "troubleshootingIntro": "ପ୍ରଥମେ ଏହି ପଦକ୍ଷେପଗୁଡ଼ିକ ଚେଷ୍ଟା କରନ୍ତୁ",
    "steps": (
        "Aim990 କୁ ସମ୍ପୂର୍ଣ୍ଣ ବନ୍ଦ କରି ପୁଣି ଖୋଲନ୍ତୁ।",
        "ସାମୟିକ ଦେଖାଯିବା କିମ୍ବା କାର୍ଯ୍ୟଦକ୍ଷତା ସମସ୍ୟା ସଫା କରିବାକୁ iPhone କିମ୍ବା iPad ପୁନରାରମ୍ଭ କରନ୍ତୁ।",
        "App Store ରେ Aim990 ର ସବୁଠୁ ନୂଆ ଅଦ୍ୟତନ ଅଛି କି ଯାଞ୍ଚ କରନ୍ତୁ।",
        "Settings → General → Software Update ଖୋଲି ଉପଲବ୍ଧ iOS ଅଦ୍ୟତନ ଇନ୍‌ଷ୍ଟଲ୍ କରନ୍ତୁ।",
        f"ଲେଆଉଟ୍ ଭୁଲ ଦେଖାଲେ Display Zoom ଏବଂ ବଡ଼ ଅକ୍ଷରକୁ ସାମୟିକ ଭାବେ ସାଧାରଣ ସେଟିଂକୁ ଫେରାଇ ଯାଞ୍ଚ କରନ୍ତୁ; ପରେ ଆପଣଙ୍କ ପସନ୍ଦର ସୁଲଭତା ସେଟିଂ ପୁଣି ଚାଲୁ କରି {EMAIL} କୁ ଫଳାଫଳ ଜଣାନ୍ତୁ।",
    ),
    "contactHeading": "ସହାୟତା ସହ ଯୋଗାଯୋଗ",
    "contactCopy": f"{EMAIL} କୁ ଇମେଲ୍ କରନ୍ତୁ। ଡିଭାଇସ୍ ମଡେଲ୍, iOS ସଂସ୍କରଣ, App ସଂସ୍କରଣ ଏବଂ ସମସ୍ୟା ଦେଖାଯିବା ପୂର୍ବରୁ କ’ଣ ଟ୍ୟାପ୍ କରିଥିଲେ ଲେଖନ୍ତୁ।",
    "appStoreLabel": "App Store ରେ Aim990 ଦେଖନ୍ତୁ",
    "noTracking": "ଏହି ସାଇଟ୍ ତୃତୀୟ ପକ୍ଷ ଟ୍ରାକିଂ, ବିଜ୍ଞାପନ କିମ୍ବା ଆନାଲିଟିକ୍ସ ବ୍ୟବହାର କରେ ନାହିଁ।",
    "privacyTitle": "Aim990 ଗୋପନୀୟତା ନୀତି",
    "privacyDescription": "Aim990 ପାଇଁ ଖାତା ଦରକାର ନାହିଁ, ବ୍ୟକ୍ତିଗତ ତଥ୍ୟ ସଂଗ୍ରହ କରେ ନାହିଁ ଏବଂ ଅଧ୍ୟୟନ ତଥ୍ୟ ଆପଣଙ୍କ ଡିଭାଇସ୍‌ରେ ରଖେ।",
    "privacyEyebrow": "ଗୋପନୀୟତା ନୀତି",
    "privacyLead": "Aim990 କେଉଁ ତଥ୍ୟ ପ୍ରକ୍ରିୟା କରେ, ସେହି ତଥ୍ୟ କେଉଁଠି ରହେ ଏବଂ ଆପଣ ତାହାକୁ କିପରି ନିୟନ୍ତ୍ରଣ କରନ୍ତି—ଏହି ପୃଷ୍ଠାରେ ସେଥିର ବ୍ୟାଖ୍ୟା ଅଛି।",
    "updated": "ଶେଷ ଅଦ୍ୟତନ: ୨୭ ଜୁନ୍ ୨୦୨୬",
    "privacyCards": (
        ("ଆମେ କେଉଁ ତଥ୍ୟ ସଂଗ୍ରହ କରୁ", "କିଛି ନୁହେଁ। Aim990 ବ୍ୟକ୍ତିଗତ ତଥ୍ୟ ସଂଗ୍ରହ, ପଠାଇବା କିମ୍ବା ବିକ୍ରି କରେ ନାହିଁ ଏବଂ ବିଜ୍ଞାପନ କିମ୍ବା ଆନାଲିଟିକ୍ସ ପାଇଁ ତାହା ବ୍ୟବହାର କରେ ନାହିଁ। ଡେଭେଲପର୍ ଖାତା କିମ୍ବା ସାଇନ୍-ଇନ୍ ନାହିଁ।"),
        ("ତଥ୍ୟ କେଉଁଠି ରହେ", "ଆପଣଙ୍କ ଉତ୍ତର, ସଠିକତା, ଅଭ୍ୟାସ ପ୍ରମାଣ, ଲକ୍ଷ୍ୟ ନମ୍ବର, ପରୀକ୍ଷା ତାରିଖ, ଧାରାବାହିକତା, ସଫଳତା ଏବଂ ସେଟିଂ App ର ସ୍ଥାନୀୟ ସ୍ଟୋରେଜ୍‌ରେ ରହେ। ଡେଭେଲପର୍ ସେଗୁଡ଼ିକୁ ଦେଖିପାରେ ନାହିଁ। App ଡିଲିଟ୍ କଲେ ସ୍ଥାନୀୟ ତଥ୍ୟ ମିଟିଯାଏ।"),
        ("କଣ୍ଠସ୍ୱର ଏବଂ ଅଡିଓ", "ଶୁଣିବା ଅଭ୍ୟାସ ଆପଣଙ୍କ ଡିଭାଇସ୍‌ରେ iOS ପ୍ରଦାନ କରୁଥିବା କଣ୍ଠସ୍ୱର ବ୍ୟବହାର କରେ। Aim990 ଆପଣଙ୍କ କଣ୍ଠସ୍ୱର କିମ୍ବା ଶୁଣିବା ଅଡିଓ ରେକର୍ଡ କିମ୍ବା ଅପଲୋଡ୍ କରେ ନାହିଁ।"),
        ("କିଣା", "ଏକଥରିଆ App ମଧ୍ୟର କିଣା Apple ଦ୍ୱାରା App Store ଏବଂ StoreKit ମାଧ୍ୟମରେ ପ୍ରକ୍ରିୟା କରାଯାଏ। ଡେଭେଲପର୍ ଆପଣଙ୍କ ପେମେଣ୍ଟ ତଥ୍ୟ ପାଏ ନାହିଁ। ସେହି Apple Account ବ୍ୟବହାର କରି କିଣାକୁ ପୁନରୁଦ୍ଧାର କରିପାରିବେ।"),
        ("ଶିଶୁଙ୍କ ଗୋପନୀୟତା", "Aim990 ଶିଶୁ ସହିତ କାହାରି ତଥ୍ୟ ଜାଣିଶୁଣି ସଂଗ୍ରହ କରେ ନାହିଁ। App ଶିଶୁର ନାମ, ଜନ୍ମତାରିଖ, ଯୋଗାଯୋଗ ତଥ୍ୟ, ଫଟୋ କିମ୍ବା ସ୍ୱାସ୍ଥ୍ୟ ତଥ୍ୟ ମାଗେ ନାହିଁ।"),
        ("ଏହି ନୀତିର ପରିବର୍ତ୍ତନ", "Aim990 ର କୌଣସି ବୈଶିଷ୍ଟ୍ୟ ଏହି ନୀତିକୁ ପ୍ରଭାବିତ କରିବା ଭଳି ବଦଳିଲେ, ଏହି ପୃଷ୍ଠା ଏବଂ ଶେଷ ଅଦ୍ୟତନ ତାରିଖ ସଂଶୋଧନ କରାଯିବ।"),
        ("ଯୋଗାଯୋଗ", f"ଗୋପନୀୟତା ସମ୍ବନ୍ଧୀୟ ପ୍ରଶ୍ନ ପାଇଁ {EMAIL} କୁ ଇମେଲ୍ କରନ୍ତୁ।"),
    ),
    "privacyNote": "ଏହି ଓଡ଼ିଆ ପୃଷ୍ଠାଟି ଇଂରାଜୀ ଗୋପନୀୟତା ନୀତିର ଅନୁବାଦ। ଅର୍ଥରେ ତଫାତ ଥିଲେ ଇଂରାଜୀ ସଂସ୍କରଣ ପ୍ରାଧାନ୍ୟ ପାଇବ।",
}


def esc(value: str) -> str:
    return html.escape(value, quote=False)


def generated_body(copy: dict, notice: str, page: str) -> str:
    current_support = ' aria-current="page"' if page == "support" else ""
    current_privacy = ' aria-current="page"' if page == "privacy" else ""
    header = f"""
<div class="shell">
<header class="site-header">
  <a class="brand" href="index.html"><img src="logo.png" alt="" width="34" height="34"><span>{esc(copy["appName"])}</span></a>
  <nav class="primary-nav"><a href="index.html">{esc(copy["navHome"])}</a><a href="support.html"{current_support}>{esc(copy["navSupport"])}</a><a href="privacy.html"{current_privacy}>{esc(copy["navPrivacy"])}</a></nav>
  <details class="language"><summary aria-label="{esc(copy["languageLabel"])}">🌐 <span>{esc(copy["languageName"])}</span></summary><div class="language-panel"></div></details>
</header>"""
    footer = f"""
<footer class="site-footer">
  <span>© 2026 {esc(copy["appName"])}</span>
  <span class="footer-links"><a href="{APP_STORE_URL}">{esc(copy["appStoreLabel"])}</a><a href="mailto:{EMAIL}">{EMAIL}</a><span>{esc(copy["noTracking"])}</span></span>
  <p class="legal-notice">{esc(notice)}</p>
</footer>
</div>"""
    if page == "support":
        faqs = "".join(
            f'<details class="faq"><summary>{esc(question)}</summary><p>{esc(answer)}</p></details>'
            for question, answer in copy["faqs"]
        )
        steps = "".join(f"<li>{esc(step)}</li>" for step in copy["steps"])
        content = f"""
<main>
<section class="page-hero"><p class="eyebrow">{esc(copy["supportEyebrow"])}</p><h1><span class="gradient-text">{esc(copy["appName"])}</span></h1><p class="lead">{esc(copy["supportLead"])}</p></section>
<div class="grid">
<section class="card wide"><h2>{esc(copy["faqHeading"])}</h2>{faqs}</section>
<section class="card"><h2>{esc(copy["troubleshootingHeading"])}</h2><h3>{esc(copy["troubleshootingIntro"])}</h3><ol>{steps}</ol></section>
<section class="card"><h2>{esc(copy["contactHeading"])}</h2><p>{esc(copy["contactCopy"])}</p><p style="margin-top:12px"><a class="cta" href="{APP_STORE_URL}">{esc(copy["appStoreLabel"])}</a></p><p><a href="mailto:{EMAIL}">{EMAIL}</a></p></section>
</div>
</main>"""
    else:
        cards = "".join(
            f'<section class="card"><h2>{esc(title)}</h2><p>{esc(body)}</p></section>'
            for title, body in copy["privacyCards"]
        )
        note = (
            f'<p class="note"><a href="privacy.html?lang=en-US">{esc(copy["privacyNote"])}</a></p>'
            if copy["privacyNote"]
            else ""
        )
        content = f"""
<main>
<section class="page-hero"><p class="eyebrow">{esc(copy["privacyEyebrow"])}</p><h1><span class="gradient-text">{esc(copy["appName"])}</span></h1><p class="lead">{esc(copy["privacyLead"])}</p><p class="updated">{esc(copy["updated"])}</p></section>
<div class="grid">{cards}</div>
{note}
</main>"""
    return (header + content + footer).strip()


def generated_entry(locale: str) -> dict:
    copy = ODIA_COPY if locale == "or-IN" else english_copy(locale)
    notice = legal_notice(locale)
    return {
        "locale": locale,
        "sourceLocale": locale,
        "languageName": copy["languageName"],
        "direction": copy["direction"],
        "supportTitle": copy["supportTitle"],
        "supportDescription": copy["supportDescription"],
        "supportUrl": f"{BASE_URL}?lang={locale}",
        "supportBody": generated_body(copy, notice, "support"),
        "privacyTitle": copy["privacyTitle"],
        "privacyDescription": copy["privacyDescription"],
        "privacyPolicyUrl": f"{BASE_URL}privacy.html?lang={locale}",
        "privacyBody": generated_body(copy, notice, "privacy"),
        "legalNotice": notice,
    }


def alternate_links(page: str) -> str:
    prefix = BASE_URL if page == "support" else f"{BASE_URL}privacy.html"
    links = [
        f'<link rel="alternate" hreflang="{locale}" href="{prefix}?lang={locale}">'
        for locale in OFFICIAL_LOCALES
    ]
    links.append(
        f'<link rel="alternate" hreflang="x-default" href="{prefix}?lang=en-US">'
    )
    return "\n".join(links)


def page_html(page: str) -> str:
    is_support = page == "support"
    title = "Aim990 Support Center" if is_support else "Aim990 Privacy Policy"
    description = (
        "Aim990 support, troubleshooting, privacy information, and direct contact."
        if is_support
        else "Aim990 privacy disclosures for local study data, StoreKit, and on-device audio."
    )
    path = BASE_URL if is_support else f"{BASE_URL}privacy.html"
    filename = "privacy.html" if is_support else "index.html"
    link_label = "Privacy Policy" if is_support else "Support"
    return f"""<!doctype html>
<html lang="en-US" dir="ltr">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
  <title>{title}</title>
  <meta name="description" content="{description}">
  <meta name="robots" content="index,follow,max-image-preview:large">
  <link rel="canonical" href="{path}?lang=en-US">
  {alternate_links(page)}
  <link rel="icon" href="logo.png">
  <link rel="stylesheet" href="style.css">
  <script src="locales.js"></script>
  <script src="site.js" defer></script>
</head>
<body data-page="{page}">
  <div id="localized-page"></div>
  <noscript>
    <main class="noscript-card">
      <h1>{title}</h1>
      <p>JavaScript is required to select one of the 50 localized pages.</p>
      <p><a href="mailto:{EMAIL}">{EMAIL}</a> · <a href="{filename}?lang=en-US">{link_label}</a></p>
    </main>
  </noscript>
</body>
</html>
"""


def main() -> int:
    source_locales = {
        path.name
        for path in ROOT.iterdir()
        if path.is_dir()
        and path.name != ".git"
        and (path / "support.html").is_file()
        and (path / "privacy.html").is_file()
    }
    expected_sources = set(OFFICIAL_LOCALES) - set(GENERATED_LOCALES)
    if source_locales != expected_sources:
        missing = sorted(expected_sources - source_locales)
        extra = sorted(source_locales - expected_sources)
        raise SystemExit(f"localized source mismatch; missing={missing}, extra={extra}")

    entries = {}
    for locale in OFFICIAL_LOCALES:
        entries[locale] = (
            generated_entry(locale)
            if locale in GENERATED_LOCALES
            else source_entry(locale)
        )
    serialized = json.dumps(entries, ensure_ascii=False, indent=2)
    serialized = serialized.replace("\u2028", "\\u2028").replace("\u2029", "\\u2029")
    (ROOT / "locales.js").write_text(
        "window.AIM990_LOCALES = " + serialized + ";\n",
        encoding="utf-8",
    )

    source = (ROOT / "zh-Hant" / "support.html").read_text(encoding="utf-8")
    stylesheet = match(r"<style>(.*?)</style>", source, "shared stylesheet").strip()
    stylesheet += """

.legal-notice{flex:1 0 100%;margin:4px 0 0;color:var(--faint);font-size:12.5px;line-height:1.65}
.noscript-card{width:min(760px,calc(100% - 40px));margin:60px auto;padding:28px;border:1px solid var(--line);border-radius:20px;background:#fff}
"""
    (ROOT / "style.css").write_text(stylesheet.strip() + "\n", encoding="utf-8")
    (ROOT / "index.html").write_text(page_html("support"), encoding="utf-8")
    (ROOT / "privacy.html").write_text(page_html("privacy"), encoding="utf-8")
    print("Built exact-50 query-localized support and privacy pages.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
