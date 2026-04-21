// SPDX-License-Identifier: MIT
// Copyright (c) 2026 Alex Conesa

#include "i18n.h"

namespace i18n {

  // Built-in language display names (in their own script). Never changes.
  static const char* const s_langNames[] = {
      "English",                               // Lang::English
      "\xe4\xb8\xad\xe6\x96\x87",              // Lang::Chinese      中文
      "\xe6\x97\xa5\xe6\x9c\xac\xe8\xaa\x9e",  // Lang::Japanese     日本語
      "Espa\xc3\xb1ol",                        // Lang::Spanish      Español
      "Ti\xe1\xba\xbfng Vi\xe1\xbb\x87t"       // Lang::Vietnamese   Tiếng Việt
  };

  // Registered languages for this project
  struct RegisteredLang {
      const char* const* strings;
      Lang id;
      int8_t yOffset;
      uint16_t stringCount;
  };

  static RegisteredLang s_languages[MAX_LANGUAGES];
  static uint8_t s_langCount = 0;
  static uint8_t s_activeLang = 0;

  const char* langName(Lang lang) {
    auto idx = static_cast<uint8_t>(lang);
    if (idx >= static_cast<uint8_t>(Lang::LANG_COUNT)) {
      return "?";
    }
    return s_langNames[idx];
  }

  uint8_t addLanguage(Lang lang, const char* const* strings, uint16_t stringCount, int8_t yOffset) {
    if (s_langCount >= MAX_LANGUAGES) {
      return 0xFF;
    }
    s_languages[s_langCount] = {strings, lang, yOffset, stringCount};
    return s_langCount++;
  }

  const char* str(uint16_t index) {
    if (s_activeLang >= s_langCount) {
      return "?";
    }
    const auto& lang = s_languages[s_activeLang];
    if (index >= lang.stringCount) {
      return "?";
    }
    return lang.strings[index];
  }

  void setLanguage(uint8_t langIndex) {
    if (langIndex < s_langCount) {
      s_activeLang = langIndex;
    }
  }

  uint8_t getLanguage() {
    return s_activeLang;
  }

  uint8_t languageCount() {
    return s_langCount;
  }

  const char* languageName(uint8_t langIndex) {
    if (langIndex >= s_langCount) {
      return "?";
    }
    return s_langNames[static_cast<uint8_t>(s_languages[langIndex].id)];
  }

  Lang languageId(uint8_t langIndex) {
    if (langIndex >= s_langCount) {
      return Lang::English;
    }
    return s_languages[langIndex].id;
  }

  int8_t fontYOffset() {
    if (s_activeLang >= s_langCount) {
      return 0;
    }
    return s_languages[s_activeLang].yOffset;
  }

  int8_t fontYOffset(uint8_t langIndex) {
    if (langIndex >= s_langCount) {
      return 0;
    }
    return s_languages[langIndex].yOffset;
  }

#ifdef I18N_TESTING
  void reset() {
    s_langCount = 0;
    s_activeLang = 0;
    for (auto& lang : s_languages) {
      lang = {};
    }
  }
#endif

}  // namespace i18n
