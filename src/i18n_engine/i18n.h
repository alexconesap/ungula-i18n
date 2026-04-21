// SPDX-License-Identifier: MIT
// Copyright (c) 2026 Alex Conesa

#pragma once

#include <cstdint>

namespace i18n {

  /// Maximum number of languages a project can register
  static constexpr uint8_t MAX_LANGUAGES = 5;

  /// Supported languages. The library knows each language's display name.
  /// Projects pick which ones they need — no need to remember encodings.
  enum class Lang : uint8_t {
    English = 0,
    Chinese,     // 1 中文
    Japanese,    // 2 日本語
    Spanish,     // 3 Español
    Vietnamese,  // 4 Tiếng Việt
    // ...
    LANG_COUNT  // 5 (not a real language, just a count)
  };

  /// Get the display name of a language in its own script (built-in, always available)
  const char* langName(Lang lang);

  /// Register a language for this project. Call at boot.
  /// The string table is the project's translated strings array.
  /// yOffset: vertical pixel correction for text rendering (positive = down).
  /// Returns the assigned index (0-based registration order), or 0xFF if full.
  uint8_t addLanguage(Lang lang, const char* const* strings, uint16_t stringCount, int8_t yOffset = 0);

  /// Get translated string for the current language by index
  const char* str(uint16_t index);

  /// Set the active language by registration order (0-based)
  void setLanguage(uint8_t langIndex);

  /// Get the active language index (registration order)
  uint8_t getLanguage();

  /// Get the number of registered languages
  uint8_t languageCount();

  /// Get the display name of a registered language (by registration index)
  const char* languageName(uint8_t langIndex);

  /// Get the Lang enum value of a registered language (by registration index)
  Lang languageId(uint8_t langIndex);

  /// Get the vertical offset for the active language (pixels, positive = down)
  int8_t fontYOffset();

  /// Get the vertical offset for a specific registered language
  int8_t fontYOffset(uint8_t langIndex);

#ifdef I18N_TESTING
  /// Reset all state (for unit tests only)
  void reset();
#endif

}  // namespace i18n
