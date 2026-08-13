# UngulaI18n

Lightweight runtime i18n engine for embedded C++ projects. The host project
defines string IDs and per-language translation tables; the library stores
references to those tables, switches the active language at runtime, and
serves translated strings by numeric index. It also stores per-language
display names (in their own script) and a per-language vertical font offset
for baseline correction.

No heap, no string copies, no formatting. The engine holds only pointers to
caller-owned `const char*` arrays.

---

## LLM quick map

- **Primary include**: `#include <ungula/i18n.h>`.
- **Arduino discovery include**: `#include <ungula_i18n.h>` (forwarder only; host code should keep using the real header).
- **Namespace root**: `ungula::i18n`.
- **Own source minimum**: `C++17`.
- **Effective minimum for consumers**: `C++17`.
- **Dependency impact**: None (no declared internal dependencies).
- **Supported architectures**: `*`.
- **Read order for coding agents**: `Usage` (working patterns) -> `API` (symbols/signatures) -> `Lifecycle`/`Error handling`/`Threading` notes in this file.

### Use-case index

- [Use case: register languages and look up strings (Arduino)](#use-case-register-languages-and-look-up-strings-arduino)
- [Use case: enumerate registered languages for a settings menu](#use-case-enumerate-registered-languages-for-a-settings-menu)
- [Use case: query any language's display name (registered or not)](#use-case-query-any-languages-display-name-registered-or-not)
- [Use case: per-language baseline correction when mixing fonts](#use-case-per-language-baseline-correction-when-mixing-fonts)

### LLM rules

- Use only symbols and include paths documented in this file; do not infer extra public API from implementation files.
- Prefer the use-case patterns here over ad-hoc rewrites; keep dependency wiring and lifecycle order identical unless the task explicitly changes API design.
- `src/ungula/i18n/fonts/*.h` are data blobs for the host renderer, not API. `src/pgmspace.h` is a build shim (see below).
- If required behavior is missing from the documented API, report the gap explicitly instead of inventing new public symbols.


## Usage

### Use case: register languages and look up strings (Arduino)

```cpp
#include <Arduino.h>
#include <ungula/i18n.h>

enum class StringId : uint16_t {
  BTN_START = 0,
  BTN_STOP,
  STRING_COUNT
};

static constexpr uint16_t N = static_cast<uint16_t>(StringId::STRING_COUNT);

static const char* const strings_en[N] = {
    /* BTN_START */ "START",
    /* BTN_STOP  */ "STOP",
};
static const char* const strings_es[N] = {
    /* BTN_START */ "INICIAR",
    /* BTN_STOP  */ "PARAR",
};

inline const char* tr(StringId sid) {
  return ungula::i18n::str(static_cast<uint16_t>(sid));
}

void setup() {
  Serial.begin(115200);
  ungula::i18n::addLanguage(ungula::i18n::Lang::English, strings_en, N);
  ungula::i18n::addLanguage(ungula::i18n::Lang::Spanish, strings_es, N, -3);
  ungula::i18n::setLanguage(0);            // English
  Serial.println(tr(StringId::BTN_START));   // "START"
  ungula::i18n::setLanguage(1);            // Spanish
  Serial.println(tr(StringId::BTN_START));   // "INICIAR"
}

void loop() {}
```

When to use this: any embedded UI that must render text in more than one
language. The host owns the string tables; the library keeps a stable
numeric interface to them.

### Use case: enumerate registered languages for a settings menu

```cpp
#include <ungula/i18n.h>

void drawLanguagePicker() {
  for (uint8_t i = 0; i < ungula::i18n::languageCount(); ++i) {
    const char* label = ungula::i18n::languageName(i);   // "English", "Espanol", ...
    ungula::i18n::Lang   id    = ungula::i18n::languageId(i);    // enum value, if needed
    // hand `label` to the GFX code that draws the menu row
    (void)label; (void)id;
  }
}
```

When to use this: building a "Language" screen. The library returns the
display name in the language's own script, so no UTF-8 escapes leak into
the UI code.

### Use case: query any language's display name (registered or not)

```cpp
#include <ungula/i18n.h>

const char* a = ungula::i18n::langName(ungula::i18n::Lang::Chinese);     // "中文"
const char* b = ungula::i18n::langName(ungula::i18n::Lang::Vietnamese);  // "Tiếng Việt"
```

When to use this: showing a language name before deciding to register the
language, or for diagnostic logs.

### Use case: per-language baseline correction when mixing fonts

```cpp
#include <ungula/i18n.h>

void render(/* gfx ctx */) {
  int8_t dy = ungula::i18n::fontYOffset();   // active language
  // shift the cursor by `dy` pixels before drawing strings whose font's
  // baseline does not match the GFX-default font's baseline
  (void)dy;
}
```

When to use this: a project mixes Adafruit-GFX text (Latin) with U8g2
subset fonts (CJK, Vietnamese) on the same screen and the baselines differ.

---

## API

All symbols live in namespace `ungula::i18n`. Single public header is
`ungula/i18n.h`, which includes `ungula/i18n/i18n.h`.

### Public types

#### `enum class ungula::i18n::Lang : uint8_t`

Built-in catalog of languages the library knows the display name of.

| Variant | Value | Built-in display name |
| --- | --- | --- |
| `Lang::English`    | 0 | `"English"` |
| `Lang::Chinese`    | 1 | `"中文"` |
| `Lang::Japanese`   | 2 | `"日本語"` |
| `Lang::Spanish`    | 3 | `"Español"` |
| `Lang::Vietnamese` | 4 | `"Tiếng Việt"` |
| `Lang::LANG_COUNT` | 5 | sentinel; not a real language |

A project does not have to register every variant; register only what the
project ships.

#### `static constexpr uint8_t ungula::i18n::MAX_LANGUAGES = 5`

Hard cap on how many languages a project can register. `addLanguage`
returns `0xFF` once this is reached.

### Public functions

All declarations from `src/ungula/i18n/i18n.h`:

#### `const char* ungula::i18n::langName(Lang lang)`

- **Purpose**: built-in display name of a `Lang` variant, in its own script.
- **Parameters**: `lang` - any `Lang` value.
- **Returns**: pointer to a static string. Returns `"?"` if `lang` is out of
  range (e.g. `LANG_COUNT` or a cast of an unknown integer).
- **Side effects**: none.
- **Failure behavior**: never returns null.

#### `uint8_t ungula::i18n::addLanguage(Lang lang, const char* const* strings, uint16_t stringCount, int8_t yOffset = 0)`

- **Purpose**: register a translation table at boot. Records pointer, count
  and per-language Y-offset. Does not copy the table.
- **Parameters**:
  - `lang` - identifies which catalog entry (used for display name lookup).
    Must be a real variant (`English`..`Vietnamese`). **Not validated** -
    see failure behavior.
  - `strings` - caller-owned array of `const char*`, length `stringCount`.
    Lifetime must outlive any call into the library (place it in
    `static const` / PROGMEM). **Not null-checked.**
  - `stringCount` - number of entries in `strings`. All registered tables
    should agree on this count and on enum-to-index mapping.
  - `yOffset` - vertical pixel correction for the host's text renderer.
    Positive = down, negative = up.
- **Returns**: 0-based registration index of the new language, or `0xFF`
  when `MAX_LANGUAGES` is already reached.
- **Side effects**: writes into a file-static array.
- **Failure behavior**: silently rejects beyond `MAX_LANGUAGES` (signaled
  only by the `0xFF` return). No bounds check on `stringCount` itself.
  Registering `Lang::LANG_COUNT` or a cast of an unknown integer is
  accepted, and a later `languageName()` on that slot then reads past the
  built-in name table and can hand back a garbage or null pointer. Same
  for a null `strings`: `str()` will dereference it. Validate both on the
  host side.
- **Usage notes**: registration order defines the `langIndex` used by
  `setLanguage`, `languageName`, etc. Call before `setLanguage`. The same
  `Lang` may be registered twice (no duplicate check) - the UI would then
  show the same display name on two rows.

#### `const char* ungula::i18n::str(uint16_t index)`

- **Purpose**: look up a string by index in the active language's table.
- **Returns**: pointer to the static string, or `"?"` if no language is
  active or `index >= stringCount` for the active table.
- **Side effects**: none.
- **Failure behavior**: never returns null. An out-of-range or
  unconfigured call yields `"?"`.
- **Usage notes**: hot path. The host typically wraps this in a
  thin `inline` helper that casts its own `enum class StringId` to
  `uint16_t`.

#### `void ungula::i18n::setLanguage(uint8_t langIndex)`

- **Purpose**: switch the active language to the registration with this
  index.
- **Failure behavior**: out-of-range indices are ignored; the previously
  active language stays.
- **Usage notes**: cheap; safe to call on every settings change.

#### `uint8_t ungula::i18n::getLanguage()`

- **Purpose**: current active registration index. Defaults to 0.

#### `uint8_t ungula::i18n::languageCount()`

- **Purpose**: number of registered languages. Bounded by `MAX_LANGUAGES`.

#### `const char* ungula::i18n::languageName(uint8_t langIndex)`

- **Purpose**: built-in display name for a registered language, looked up
  by registration index.
- **Returns**: static string, or `"?"` if `langIndex >= languageCount()`.
- **Failure behavior**: non-null only while every registration used a real
  `Lang` variant. The `Lang` stored by `addLanguage` indexes the name table
  unchecked.

#### `ungula::i18n::Lang ungula::i18n::languageId(uint8_t langIndex)`

- **Purpose**: get the `Lang` enum that was passed to `addLanguage` for a
  given registration index.
- **Returns**: the enum value, or `Lang::English` on out-of-range index.
- **Usage notes**: prefer `languageCount() == 0` checks before relying on
  the return - `Lang::English` is also a valid registered value.

#### `int8_t ungula::i18n::fontYOffset()`

- **Purpose**: vertical pixel offset stored for the active language.
- **Returns**: `0` if no language is active.

#### `int8_t ungula::i18n::fontYOffset(uint8_t langIndex)`

- **Purpose**: same, for a specific registered language.
- **Returns**: `0` on out-of-range index.

---

## Lifecycle

1. At boot, call `ungula::i18n::addLanguage(...)` once per language the project
   ships, in the order the UI should expose them.
2. Call `ungula::i18n::setLanguage(idx)` to pick the initial language (e.g. from
   the device's NVS / preferences).
3. During run-time, `ungula::i18n::str(...)` reads the active table; `setLanguage`
   may be called any time to switch tables.
4. There is no shutdown / unregister path. Language registrations live for
   the lifetime of the process.

Out-of-order use is benign: calling `str` before any `addLanguage` returns
`"?"`; calling `setLanguage` with an unknown index is a no-op.

---

## Storage and lookup notes

- Storage is a file-static `RegisteredLang s_languages[MAX_LANGUAGES]`.
  Each slot holds: `const char* const* strings`, `Lang id`, `int8_t
  yOffset`, `uint16_t stringCount`. No copies of any string.
- Lookup is `O(1)`: `s_languages[s_activeLang].strings[index]`.
- `str` does not range-check across all tables - only against the active
  table's `stringCount`. If two tables have different counts, switching
  languages can change which IDs resolve and which return `"?"`. Keep all
  tables sized to `STRING_COUNT`.
- The library returns raw pointers it does not own. The host must keep
  the translation arrays alive (typically `static const` in flash /
  PROGMEM).

## Encoding and font notes

- Strings are opaque `const char*`; the library does no decoding. UTF-8 in,
  UTF-8 out.
- Built-in language names in `s_langNames[]` are UTF-8 byte sequences for
  CJK/diacritic scripts (see `i18n.cpp`). The host renderer must support
  those bytes - either by drawing through a Unicode-aware font (U8g2 with
  a glyph subset) or by avoiding non-ASCII names.
- Pre-generated U8g2 subset fonts ship in `src/ungula/i18n/fonts/`:
  `font_cn_{14,20,28}.h`, `font_es_{14,20,28}.h`, `font_ja_{14,20,28}.h`,
  `font_vi_{14,20,28}.h`. They are `const uint8_t ... PROGMEM` arrays;
  including a font header pulls a U8g2-format byte array into flash. The
  library code itself does not reference the fonts - the host wires them
  into U8g2 / `lib_display`.
- Each font array is `const` at namespace scope, so it has internal
  linkage: include a given font header from exactly ONE translation unit.
  Two includes mean two copies in flash (up to ~16 KB each), not a
  duplicate-symbol error, so nothing warns you.
- `src/pgmspace.h` is a build shim, not API. Font headers do
  `#include <pgmspace.h>`; on Arduino it defers to the core header via
  `#include_next`, on pure ESP-IDF it supplies the `PROGMEM` / `pgm_read_*`
  no-ops. It only resolves when `lib_i18n/src` is on the include path.
  It deliberately omits `memcpy_P` / `str*_P` (clashes with LovyanGFX) -
  use plain `memcpy` / `strlen` on ESP32.
- No Korean / French / German fonts ship; the `Lang` enum does not include
  those languages either.

## Threading / timing

- Not thread-safe. Calls mutate file-static state without a lock. Use from
  one task only (e.g. the UI / main loop).
- All calls are non-blocking and allocation-free.
- Safe to call from `setup()` and `loop()`. Do not call from ISRs.

## Internals not part of the public API

- `s_langNames`, `s_languages`, `s_langCount`, `s_activeLang` in
  `i18n.cpp` - file-static state. Mutate only through the public API.
- `struct RegisteredLang` - storage record, defined in `i18n.cpp`. Not
  exported.
- `ungula::i18n::reset()` - exists only when the TU is built with `I18N_TESTING`
  defined. For unit tests; do not call from production code.
- `src/ungula/i18n/fonts/*.h` - data blobs consumed by the host's GFX
  layer, not by the library. Including them is optional.
- `tools/` (`generate_u8g2_font.py`, `generate_font_subset.py`,
  `*_subset.map`) - build-time utilities for regenerating subset fonts.
  Not runtime API.

## Known gaps

Real behavior of the shipped API. Guard against these host-side; do not
invent library symbols to fix them.

- `addLanguage` validates neither `lang`, `strings`, nor `stringCount`
  consistency across registrations.
- `languageId` returns `Lang::English` both for a registered English and
  for an out-of-range index. Check `languageCount()` first.
- `str` falls back to `"?"`, never to another language's table.

---

## LLM usage rules

- Use only the documented public API. The single include is
  `<ungula/i18n.h>`.
- Wrap `ungula::i18n::str(uint16_t)` in a host-side inline that takes the host's
  own `enum class StringId` - do not scatter raw casts.
- Always size every translation array to the host's `STRING_COUNT` and
  pass that same value as `stringCount` to `addLanguage`. Asymmetric
  tables silently produce `"?"` on switch.
- Never assume more than `MAX_LANGUAGES` (5) registrations succeed; check
  the return value of `addLanguage` if registering dynamically.
- Only ever pass a real `Lang` variant to `addLanguage` - never
  `Lang::LANG_COUNT`, never a cast from a stored integer that was not
  range-checked first.
- Do not read or write `s_languages`, `s_activeLang`, `s_langNames`, or
  any symbol from `i18n.cpp` directly.
- Do not call `ungula::i18n::reset()` outside a `I18N_TESTING` build.
- The library is single-threaded; do not call any function from an ISR or
  a second RTOS task.
- Treat all returned `const char*` as borrowed, immutable, and valid for
  the lifetime of the registered table. Do not free them.
