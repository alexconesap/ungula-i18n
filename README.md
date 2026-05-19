# UngulaI18n

> **High-performance embedded C++ libraries for ESP32, STM32 and other MCUs** — lightweight i18n framework for embedded UIs.

> **LLM usage note:** if this library is consumed from a coding AI workflow, explicitly point the agent to `API.md` first. `API.md` is the LLM-facing contract (public API + examples + constraints) and avoids wasting time/tokens scanning source files and this human-oriented README.

> **Warning - Active Development:** This library is under active architecture work to support multiple projects in parallel. Its structure is not finalized yet and may change without notice while this work is in progress. Updates are currently frequent (often daily). Target for structural freeze and stable `v1.0.0`: **June 2026**.

A small i18n library for embedded projects. Lets you add multi-language support without hardcoding language strings or dealing with UTF-8 encodings in your application code.

The library handles:

- Language registration and switching
- String lookup by numeric (enum based) index
- Built-in language display names (in their own script)
- Per-language vertical text offset for font baseline correction

Your project provides the translated string tables. The library provides the engine.

Use the library in this simple way (Arduino style example):

```cpp
#include <ungula/i18n.h>
#include <emblogx/logger.h>

log_info("%s", str(StringId::BTN_START));
```

## Table of Contents

- [C++ Compatibility](#c-compatibility)
- [How it works](#how-it-works)
- [Quick example](#quick-example)
  - [1. Define your string IDs](#1-define-your-string-ids)
  - [2. Write the translation tables](#2-write-the-translation-tables)
  - [3. Register languages at boot](#3-register-languages-at-boot)
  - [4. Use it](#4-use-it)
- [Language names](#language-names)
- [Vertical text offset](#vertical-text-offset)
- [Supported languages](#supported-languages)
- [API reference](#api-reference)
- [Limits](#limits)
- [Font files](#font-files)
- [Tests](#tests)
  - [Prerequisites](#prerequisites)
  - [Run the tests](#run-the-tests)
  - [Filter tests](#filter-tests)
- [Acknowledgements](#acknowledgements)
- [License](#license)
- [Arduino CLI symlink note (rarely relevant)](#arduino-cli-symlink-note-rarely-relevant)

## C++ Compatibility

- **Own source minimum**: `C++17`.
- **Effective minimum for consumers**: `C++17`.
- **Dependency impact**: None (no declared internal dependencies).

## How it works

Each project defines its own set of string IDs (an enum) and a translation table per language (a `const char*` array). At boot, you register to the library which languages your project supports. The library stores the tables and serves strings based on the active language.

```text
Your project                          lib_i18n
┌────────────────────────┐            ┌─────────────────────┐
│ StringId enum          │            │ addLanguage()       │
│ strings_en[] = {...}   │──register──│ setLanguage()       │
│ strings_es[] = {...}   │            │ str(index) → text   │
│ strings_cn[] = {...}   │            │ languageName(idx)   │
└────────────────────────┘            └─────────────────────┘
```

## Quick example

Say your project has two translatable strings: "START" and "STOP".

### 1. Define your string IDs

```cpp
// Example file: my_strings.h
#pragma once
#include <ungula/i18n/i18n.h>

enum class StringId : uint16_t {
  BTN_START = 0,
  BTN_STOP,
  STRING_COUNT
};

// Convenience wrapper — avoids casting from your own enum to the int everywhere
inline const char* str(StringId sid) {
  return ungula::i18n::str(static_cast<uint16_t>(sid));
}
```

### 2. Write the translation tables

```cpp
// strings_en.h
#pragma once
#include "my_strings.h"

static const char* const strings_en[] = {
    /* BTN_START */ "START",
    /* BTN_STOP  */ "STOP",
};

// strings_es.h
#pragma once
#include "my_strings.h"

static const char* const strings_es[] = {
    /* BTN_START */ "INICIAR",
    /* BTN_STOP  */ "PARAR",
};

// strings_cn.h
#pragma once
#include "my_strings.h"

static const char* const strings_cn[] = {
    /* BTN_START */ "\xe5\xbc\x80\xe5\xa7\x8b",  // 开始
    /* BTN_STOP  */ "\xe5\x81\x9c\xe6\xad\xa2",  // 停止
};
```

Each array must have exactly `STRING_COUNT` entries, in the same order as the enum. To keep the same exact order in all your languages depends entirely on you.

A `static_assert` in each file is a good safety net:

```cpp
#include <ungula/i18n.h>

static_assert(sizeof(strings_en) / sizeof(strings_en[0]) == static_cast<size_t>(StringId::STRING_COUNT),
              "strings_en size mismatch");
```

### 3. Register languages at boot

```cpp
// i18n_config.cpp
#include "my_strings.h"
#include "strings_en.h"
#include "strings_es.h"
#include "strings_cn.h"

static constexpr uint16_t N = static_cast<uint16_t>(StringId::STRING_COUNT);

void setup_languages() {
  ungula::i18n::addLanguage(ungula::i18n::Lang::English, strings_en, N);
  ungula::i18n::addLanguage(ungula::i18n::Lang::Spanish, strings_es, N, -3);  // -3px vertical offset
  ungula::i18n::addLanguage(ungula::i18n::Lang::Chinese, strings_cn, N);
}
```

The registration order defines the language index: English=0, Spanish=1, Chinese=2. This is what you pass to `setLanguage()` and what the settings UI iterates over.

You only register the languages your project needs. If you don't need Japanese, don't register it — it won't appear.

### 4. Use it

Arduino example:

```cpp
#include <ungula/i18n.h>
#include <emblogx/logger.h>
#include <emblogx/sinks/console_sink.h>

static emblogx::ConsoleSink g_console;

void setup() {
  emblogx::register_sink(&g_console);
  emblogx::init();

  setup_languages();
  ungula::i18n::setLanguage(0);  // start in English (or store it in your device's NVS)
}

void printStuff() {
  log_info("%s", str(StringId::BTN_START));
  log_info("%s", str(StringId::BTN_STOP));
}

void onLanguageChanged(uint8_t newLang) {
  ungula::i18n::setLanguage(newLang);
  printStuff(); // now shows the labels based on currently setup language
}
```

## Language names

The library knows the display name of every supported language in its own script. You never need to deal with hex-encoded UTF-8 strings for language names:

```cpp
#include <ungula/i18n.h>

ungula::i18n::langName(ungula::i18n::Lang::English);     // "English"
ungula::i18n::langName(ungula::i18n::Lang::Chinese);     // "中文"
ungula::i18n::langName(ungula::i18n::Lang::Spanish);     // "Español"
ungula::i18n::langName(ungula::i18n::Lang::Vietnamese);  // "Tiếng Việt"
ungula::i18n::langName(ungula::i18n::Lang::Japanese);    // "日本語"
```

For registered languages, use the index-based version:

```cpp
#include <ungula/i18n.h>

for (uint8_t i = 0; i < ungula::i18n::languageCount(); ++i) {
  drawLanguageButton(i, ungula::i18n::languageName(i));
}
```

## Vertical text offset

When mixing font sources (e.g., Adafruit GFX for English, U8g2 for CJK), the text baseline often doesn't match between typefaces. The library stores a per-language vertical pixel offset that your display code can query and apply.

Register the offset when adding a language:

```cpp
#include <ungula/i18n.h>

ungula::i18n::addLanguage(ungula::i18n::Lang::English,    strings_en, N,  0);  // baseline reference
ungula::i18n::addLanguage(ungula::i18n::Lang::Spanish,    strings_es, N, -3);  // 3px up
ungula::i18n::addLanguage(ungula::i18n::Lang::Vietnamese, strings_vi, N, -5);  // 5px up
```

Query it when rendering text:

```cpp
#include <ungula/i18n.h>

int8_t offset = ungula::i18n::fontYOffset();           // active language
int8_t offset = ungula::i18n::fontYOffset(langIndex);  // specific language
```

If you use my library `lib_display`, call `gfx_set_font_y_offset(ungula::i18n::fontYOffset())` after switching languages. The display wrappers (`gfx_setCursor`, `gfx_drawCentreString`, etc.) apply the offset automatically.

## Supported languages

| Enum value | Display name |
| --- | --- |
| `Lang::English` | English |
| `Lang::Chinese` | 中文 |
| `Lang::Japanese` | 日本語 |
| `Lang::Spanish` | Español |
| `Lang::Vietnamese` | Tiếng Việt |

To add a new language, add it to the `Lang` enum in `i18n.h` and its display name to the `s_langNames` array in `i18n.cpp`.

## API reference

| Function | Description |
| --- | --- |
| `addLanguage(lang, strings, count, yOffset)` | Register a language at boot. Returns its index. |
| `str(index)` | Get translated string for the active language. |
| `setLanguage(langIndex)` | Switch the active language (by registration index). |
| `getLanguage()` | Get the active language index. |
| `languageCount()` | Number of registered languages. |
| `languageName(langIndex)` | Display name of a registered language. |
| `languageId(langIndex)` | `Lang` enum value of a registered language. |
| `langName(Lang)` | Display name of any language (registered or not). |
| `fontYOffset()` | Vertical offset for the active language. |
| `fontYOffset(langIndex)` | Vertical offset for a specific language. |

## Limits

- Up to 5 languages per project (`MAX_LANGUAGES`)
- String tables are `const char*` arrays in PROGMEM — no heap allocation
- No runtime string formatting — the library returns pointers to static strings
- Thread safety: not thread-safe. Call from the main loop only.

## Font files

The library includes pre-generated U8g2 subset fonts for non-English languages in `src/ungula/i18n/fonts/`. These are generated from system fonts using `bdfconv` and contain only the characters needed for the translation strings - typically 2-10 KB per font size, not the 1-2 MB a full CJK font would require.

The font generation pipeline (in the project's `tools/` directory):

1. `generate_font_subset.py` — extracts unique codepoints from translation headers
2. `otf2bdf` (system tool) — converts TTF/TTC to BDF format
3. `bdfconv` (from u8g2 project) — generates U8g2 binary font arrays from BDF + subset map
`https://github.com/olikraus/u8g2/wiki/u8g2fontformat`

## Tests

The library includes a Google Test suite that covers registration, string lookup, language switching, built-in names, vertical offset, and CJK content handling.

### Prerequisites

- CMake 3.16+
- A C++17 compiler (GCC, Clang, or MSVC)
- Internet connection (first build fetches Google Test automatically)

### Run the tests

```shell
cd tests
./1_build.sh     # configure cmake (only needed once)
./2_run.sh       # build and run all tests
```

### Filter tests

```shell
./2_run.sh -R FontYOffset   # run only vertical offset tests
./2_run.sh -R LangName      # run only language name tests
./2_run.sh -V               # verbose output
```

## Acknowledgements

Thanks to Claude and ChatGPT for helping on generating this documentation.

## License

MIT License — see [LICENSE](license.txt) file.

---

## Arduino CLI symlink note (rarely relevant)

This library ships a flat forwarder header at `src/ungula_i18n.h` that
just `#include`s `ungula/i18n.h`. `library.properties` `includes=` points
at the forwarder.

It only exists to work around an Arduino CLI quirk: when the library is
consumed through a symlink, the CLI sometimes fails to discover headers
nested under `src/ungula/`. The flat forwarder fixes that scan.

**Host code keeps including the real header**:

```cpp
#include <ungula/i18n.h>
```

PlatformIO, ESP-IDF component builds, and plain CMake setups can ignore
the forwarder.
