(() => {
  const STORAGE_KEY = "agri_lang";
  const SELECT_ID = "languageSelect";
  const TRANSLATE_ELEMENT_ID = "google_translate_element";
  const LANGUAGE_MAP = {
    en: "en",
    hi: "hi",
    od: "or",
    te: "te"
  };

  function ensureTranslateElementNode() {
    let node = document.getElementById(TRANSLATE_ELEMENT_ID);
    if (node) return node;

    node = document.createElement("div");
    node.id = TRANSLATE_ELEMENT_ID;
    node.className = "google-translate-anchor";
    node.setAttribute("aria-hidden", "true");
    document.body.appendChild(node);
    return node;
  }

  function setGoogleLanguage(targetLang) {
    const combo = document.querySelector(".goog-te-combo");
    if (!combo) return false;

    combo.value = targetLang;
    combo.dispatchEvent(new Event("change"));
    return true;
  }

  function applyLanguage(langKey) {
    const targetLang = LANGUAGE_MAP[langKey] || "en";
    localStorage.setItem(STORAGE_KEY, langKey);

    let attempts = 0;
    const maxAttempts = 30;
    const timer = setInterval(() => {
      attempts += 1;
      const applied = setGoogleLanguage(targetLang);
      if (applied || attempts >= maxAttempts) {
        clearInterval(timer);
      }
    }, 200);
  }

  window.googleTranslateElementInit = function googleTranslateElementInit() {
    ensureTranslateElementNode();
    new google.translate.TranslateElement(
      {
        pageLanguage: "en",
        includedLanguages: "en,hi,or,bn,ta,te,mr,gu,kn,ml,pa,ur",
        autoDisplay: false
      },
      TRANSLATE_ELEMENT_ID
    );

    const select = document.getElementById(SELECT_ID);
    const saved = localStorage.getItem(STORAGE_KEY) || "en";
    if (select) {
      select.value = saved;
    }
    applyLanguage(saved);
  };

  function loadGoogleTranslateScript() {
    if (document.querySelector('script[data-google-translate="true"]')) return;
    const script = document.createElement("script");
    script.src = "//translate.google.com/translate_a/element.js?cb=googleTranslateElementInit";
    script.async = true;
    script.setAttribute("data-google-translate", "true");
    document.head.appendChild(script);
  }

  document.addEventListener("DOMContentLoaded", () => {
    ensureTranslateElementNode();

    const select = document.getElementById(SELECT_ID);
    const saved = localStorage.getItem(STORAGE_KEY) || "en";
    if (select) {
      select.value = saved;
      select.addEventListener("change", (event) => {
        applyLanguage(event.target.value);
      });
    }

    loadGoogleTranslateScript();
  });
})();
