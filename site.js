(function () {
  "use strict";

  const DEFAULT_LOCALE = "en-US";
  const locales = window.AIM990_LOCALES;
  const page = document.body.dataset.page;
  const requested = new URLSearchParams(window.location.search).get("lang");
  const locale = requested && Object.hasOwn(locales, requested)
    ? requested
    : DEFAULT_LOCALE;
  const copy = locales[locale];
  const bodyKey = page === "privacy" ? "privacyBody" : "supportBody";
  const titleKey = page === "privacy" ? "privacyTitle" : "supportTitle";
  const descriptionKey = page === "privacy"
    ? "privacyDescription"
    : "supportDescription";

  if (
    !copy
    || copy.locale !== locale
    || copy.sourceLocale !== locale
    || typeof copy[bodyKey] !== "string"
    || !copy[bodyKey].trim()
  ) {
    throw new Error(`Incomplete Aim990 locale: ${locale}`);
  }

  const pageUrl = (kind, code) => (
    kind === "privacy"
      ? `privacy.html?lang=${encodeURIComponent(code)}`
      : `./?lang=${encodeURIComponent(code)}`
  );
  const absoluteUrl = (kind, code) => (
    kind === "privacy"
      ? `https://alice51849.github.io/aim990-support/privacy.html?lang=${encodeURIComponent(code)}`
      : `https://alice51849.github.io/aim990-support/?lang=${encodeURIComponent(code)}`
  );

  document.documentElement.lang = locale;
  document.documentElement.dir = copy.direction;
  document.title = copy[titleKey];
  const description = document.querySelector('meta[name="description"]');
  if (description) description.content = copy[descriptionKey];
  const canonical = document.querySelector('link[rel="canonical"]');
  if (canonical) canonical.href = absoluteUrl(page, locale);

  document.getElementById("localized-page").innerHTML = copy[bodyKey];

  document.querySelectorAll("a[href]").forEach((link) => {
    const raw = link.getAttribute("href");
    if (!raw || raw.startsWith("#") || raw.startsWith("mailto:")) return;
    let target;
    try {
      target = new URL(raw, window.location.href);
    } catch {
      return;
    }
    const path = target.pathname.replace(/\/+$/, "/");
    if (/\/aim990-support\/(?:[^/]+\/)?privacy\.html$/.test(path)) {
      const targetLocale = link.closest(".note") ? DEFAULT_LOCALE : locale;
      link.href = pageUrl("privacy", targetLocale);
    } else if (
      /\/aim990-support\/(?:[^/]+\/)?(?:index\.html|support\.html)?$/.test(path)
      || raw === "index.html"
      || raw === "support.html"
      || raw === "./"
    ) {
      link.href = pageUrl("support", locale);
    }
  });

  document.querySelectorAll(".language-panel").forEach((panel) => {
    panel.replaceChildren();
    Object.keys(locales).forEach((code) => {
      const link = document.createElement("a");
      link.href = pageUrl(page, code);
      link.hreflang = code;
      link.lang = code;
      link.textContent = `${locales[code].languageName} — ${code}`;
      if (code === locale) link.setAttribute("aria-current", "true");
      panel.appendChild(link);
    });
  });
})();
