/**
 * Minimal i18n utility for English + Hindi.
 * Phase 0: simple key lookup with fallback to English.
 * Phase 1+: replace with next-intl or react-i18next for full locale support.
 */

export type Lang = "en" | "hi";

type Translations = Record<string, Record<Lang, string>>;

const T: Translations = {
  "app.name": { en: "CleanBreath AI", hi: "क्लीनब्रेथ AI" },
  "app.tagline": {
    en: "Breathe safer. Live smarter.",
    hi: "सुरक्षित सांस लें। स्मार्ट जिएं।",
  },
  "nav.today": { en: "Today", hi: "आज" },
  "nav.indoor": { en: "Indoor", hi: "घर के अंदर" },
  "nav.chat": { en: "Chat", hi: "चैट" },
  "nav.community": { en: "Community", hi: "समुदाय" },
  "risk.green": { en: "Good", hi: "अच्छा" },
  "risk.yellow": { en: "Satisfactory", hi: "संतोषजनक" },
  "risk.orange": { en: "Moderate", hi: "मध्यम" },
  "risk.red": { en: "Poor", hi: "खराब" },
  "risk.maroon": { en: "Severe", hi: "गंभीर" },
  "data.stale": {
    en: "Live data unavailable – showing last known reading.",
    hi: "लाइव डेटा उपलब्ध नहीं – अंतिम ज्ञात रीडिंग दिखाई जा रही है।",
  },
  "disclaimer.medical": {
    en: "This is general guidance, not medical advice. For symptoms like breathlessness or chest pain, see a doctor immediately.",
    hi: "यह सामान्य मार्गदर्शन है, चिकित्सा सलाह नहीं। सांस की तकलीफ या सीने में दर्द के लिए तुरंत डॉक्टर से मिलें।",
  },
  "onboarding.title": {
    en: "Tell us about your household",
    hi: "अपने परिवार के बारे में बताएं",
  },
  "consent.title": {
    en: "Your privacy matters",
    hi: "आपकी गोपनीयता महत्वपूर्ण है",
  },
  "consent.body": {
    en: "We use your coarse location (~1 km) to fetch air quality data. Health information is optional, encrypted, and never sold. You can delete all your data at any time.",
    hi: "हम वायु गुणवत्ता डेटा के लिए आपके मोटे स्थान (~1 किमी) का उपयोग करते हैं। स्वास्थ्य जानकारी वैकल्पिक, एन्क्रिप्टेड है और कभी नहीं बेची जाती। आप किसी भी समय अपना डेटा हटा सकते हैं।",
  },
};

export function t(key: string, lang: Lang = "en"): string {
  const entry = T[key];
  if (!entry) return key;
  return entry[lang] ?? entry["en"] ?? key;
}

/** Detect browser language and return supported app language. */
export function detectLang(): Lang {
  if (typeof navigator === "undefined") return "en";
  const browserLang = navigator.language?.slice(0, 2).toLowerCase();
  return browserLang === "hi" ? "hi" : "en";
}
