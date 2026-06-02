// SPDX-License-Identifier: MIT
// Copyright (c) 2026 Alex Conesa
// See LICENSE file for details.
#pragma once

// Arduino <pgmspace.h> compatibility. Required by pure ESP-IDF (Arduino-free)
// projects.
//
// The U8g2 subset fonts in this library are generated with Arduino's
// `PROGMEM` attribute and `#include <pgmspace.h>`. This file sits at the
// library's include root (lib_i18n/src), so that include resolves here for
// any project that puts lib_i18n on its include path. On the ESP32 family
// flash is memory-mapped, so PROGMEM is a no-op and pgm_read_* are plain
// dereferences.
//
// Under an Arduino build the real core header still exists later on the
// include path, so we defer to it (#include_next) and shadow nothing.

#if defined(ARDUINO)
#  include_next <pgmspace.h>
#else

#include <stdint.h>
#include <string.h>

#ifndef PROGMEM
#define PROGMEM
#endif
#ifndef PGM_P
#define PGM_P const char *
#endif
#ifndef PGM_VOID_P
#define PGM_VOID_P const void *
#endif
#ifndef PSTR
#define PSTR(s) (s)
#endif

// C-style casts so the shim is valid in both C and C++ translation units
// (matches the real pgmspace.h, which is C-compatible).
#ifndef pgm_read_byte
#define pgm_read_byte(addr) (*(const uint8_t *)(addr))
#endif
#ifndef pgm_read_word
#define pgm_read_word(addr) (*(const uint16_t *)(addr))
#endif
#ifndef pgm_read_dword
#define pgm_read_dword(addr) (*(const uint32_t *)(addr))
#endif
#ifndef pgm_read_float
#define pgm_read_float(addr) (*(const float *)(addr))
#endif
#ifndef pgm_read_ptr
#define pgm_read_ptr(addr) (*(void *const *)(addr))
#endif
#ifndef pgm_read_byte_near
#define pgm_read_byte_near(addr) pgm_read_byte(addr)
#endif
#ifndef pgm_read_word_near
#define pgm_read_word_near(addr) pgm_read_word(addr)
#endif

// NOTE: deliberately no memcpy_P / str*_P here. LovyanGFX's own
// utility/pgmspace.h defines memcpy_P as an inline FUNCTION under
// `#ifndef ARDUINO`. If a same-named macro is already defined when both
// headers meet in one translation unit, the preprocessor rewrites that
// function's signature into garbage and the whole color-type header
// (colortype.hpp) fails to parse. On ESP32 these _P helpers are just the
// plain libc calls anyway, so consumers use memcpy/strlen directly.

#endif // ARDUINO
