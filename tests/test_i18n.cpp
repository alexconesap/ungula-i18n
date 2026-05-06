// Unit tests for lib_i18n (ungula::i18n:: namespace)

#include <gtest/gtest.h>
#include <ungula/i18n/i18n.h>

// --- Test string tables ---

static const char* const strings_en[] = {
        "START",
        "STOP",
        "HOME",
};
static constexpr uint16_t EN_COUNT = 3;

static const char* const strings_es[] = {
        "INICIAR",
        "PARAR",
        "ORIGEN",
};
static constexpr uint16_t ES_COUNT = 3;

static const char* const strings_cn[] = {
        "\xe5\xbc\x80\xe5\xa7\x8b",  // 开始
        "\xe5\x81\x9c\xe6\xad\xa2",  // 停止
        "\xe5\x8e\x9f\xe4\xbd\x8d",  // 原位
};
static constexpr uint16_t CN_COUNT = 3;

// --- Fixture: resets state before each test ---

class I18nTest : public ::testing::Test {
    protected:
        void SetUp() override {
            ungula::i18n::reset();
        }
};

// --- Registration ---

TEST_F(I18nTest, AddLanguageReturnsIndex) {
    EXPECT_EQ(ungula::i18n::addLanguage(ungula::i18n::Lang::English, strings_en, EN_COUNT), 0);
    EXPECT_EQ(ungula::i18n::addLanguage(ungula::i18n::Lang::Spanish, strings_es, ES_COUNT), 1);
    EXPECT_EQ(ungula::i18n::addLanguage(ungula::i18n::Lang::Chinese, strings_cn, CN_COUNT), 2);
}

TEST_F(I18nTest, LanguageCountMatchesRegistrations) {
    EXPECT_EQ(ungula::i18n::languageCount(), 0);
    ungula::i18n::addLanguage(ungula::i18n::Lang::English, strings_en, EN_COUNT);
    EXPECT_EQ(ungula::i18n::languageCount(), 1);
    ungula::i18n::addLanguage(ungula::i18n::Lang::Spanish, strings_es, ES_COUNT);
    EXPECT_EQ(ungula::i18n::languageCount(), 2);
}

TEST_F(I18nTest, AddLanguageRejectsWhenFull) {
    for (uint8_t idx = 0; idx < ungula::i18n::MAX_LANGUAGES; ++idx) {
        EXPECT_NE(ungula::i18n::addLanguage(ungula::i18n::Lang::English, strings_en, EN_COUNT), 0xFF);
    }
    // One more should fail
    EXPECT_EQ(ungula::i18n::addLanguage(ungula::i18n::Lang::English, strings_en, EN_COUNT), 0xFF);
}

// --- String lookup ---

TEST_F(I18nTest, StrReturnsEnglishByDefault) {
    ungula::i18n::addLanguage(ungula::i18n::Lang::English, strings_en, EN_COUNT);
    EXPECT_STREQ(ungula::i18n::str(0), "START");
    EXPECT_STREQ(ungula::i18n::str(1), "STOP");
    EXPECT_STREQ(ungula::i18n::str(2), "HOME");
}

TEST_F(I18nTest, StrReturnsQuestionMarkForInvalidIndex) {
    ungula::i18n::addLanguage(ungula::i18n::Lang::English, strings_en, EN_COUNT);
    EXPECT_STREQ(ungula::i18n::str(99), "?");
}

TEST_F(I18nTest, StrReturnsQuestionMarkWhenNoLanguagesRegistered) {
    EXPECT_STREQ(ungula::i18n::str(0), "?");
}

// --- Language switching ---

TEST_F(I18nTest, SetLanguageSwitchesStrings) {
    ungula::i18n::addLanguage(ungula::i18n::Lang::English, strings_en, EN_COUNT);
    ungula::i18n::addLanguage(ungula::i18n::Lang::Spanish, strings_es, ES_COUNT);

    ungula::i18n::setLanguage(0);
    EXPECT_STREQ(ungula::i18n::str(0), "START");

    ungula::i18n::setLanguage(1);
    EXPECT_STREQ(ungula::i18n::str(0), "INICIAR");
    EXPECT_STREQ(ungula::i18n::str(1), "PARAR");
}

TEST_F(I18nTest, SetLanguageIgnoresInvalidIndex) {
    ungula::i18n::addLanguage(ungula::i18n::Lang::English, strings_en, EN_COUNT);
    ungula::i18n::setLanguage(0);
    ungula::i18n::setLanguage(99);  // should be ignored
    EXPECT_EQ(ungula::i18n::getLanguage(), 0);
    EXPECT_STREQ(ungula::i18n::str(0), "START");
}

TEST_F(I18nTest, GetLanguageReturnsActiveIndex) {
    ungula::i18n::addLanguage(ungula::i18n::Lang::English, strings_en, EN_COUNT);
    ungula::i18n::addLanguage(ungula::i18n::Lang::Spanish, strings_es, ES_COUNT);
    EXPECT_EQ(ungula::i18n::getLanguage(), 0);
    ungula::i18n::setLanguage(1);
    EXPECT_EQ(ungula::i18n::getLanguage(), 1);
}

// --- Language names ---

TEST_F(I18nTest, LangNameReturnsBuiltInNames) {
    EXPECT_STREQ(ungula::i18n::langName(ungula::i18n::Lang::English), "English");
    EXPECT_STREQ(ungula::i18n::langName(ungula::i18n::Lang::Spanish), "Espa\xc3\xb1ol");
    EXPECT_STREQ(ungula::i18n::langName(ungula::i18n::Lang::Vietnamese), "Ti\xe1\xba\xbfng Vi\xe1\xbb\x87t");
}

TEST_F(I18nTest, LangNameReturnsQuestionMarkForInvalid) {
    EXPECT_STREQ(ungula::i18n::langName(static_cast<ungula::i18n::Lang>(99)), "?");
}

TEST_F(I18nTest, LanguageNameReturnsRegisteredNames) {
    ungula::i18n::addLanguage(ungula::i18n::Lang::English, strings_en, EN_COUNT);
    ungula::i18n::addLanguage(ungula::i18n::Lang::Chinese, strings_cn, CN_COUNT);

    EXPECT_STREQ(ungula::i18n::languageName(0), "English");
    EXPECT_STREQ(ungula::i18n::languageName(1), "\xe4\xb8\xad\xe6\x96\x87");  // 中文
}

TEST_F(I18nTest, LanguageNameReturnsQuestionMarkForInvalidIndex) {
    ungula::i18n::addLanguage(ungula::i18n::Lang::English, strings_en, EN_COUNT);
    EXPECT_STREQ(ungula::i18n::languageName(5), "?");
}

// --- Language ID ---

TEST_F(I18nTest, LanguageIdReturnsCorrectEnum) {
    ungula::i18n::addLanguage(ungula::i18n::Lang::English, strings_en, EN_COUNT);
    ungula::i18n::addLanguage(ungula::i18n::Lang::Chinese, strings_cn, CN_COUNT);
    ungula::i18n::addLanguage(ungula::i18n::Lang::Spanish, strings_es, ES_COUNT);

    EXPECT_EQ(ungula::i18n::languageId(0), ungula::i18n::Lang::English);
    EXPECT_EQ(ungula::i18n::languageId(1), ungula::i18n::Lang::Chinese);
    EXPECT_EQ(ungula::i18n::languageId(2), ungula::i18n::Lang::Spanish);
}

TEST_F(I18nTest, LanguageIdDefaultsToEnglishForInvalidIndex) {
    EXPECT_EQ(ungula::i18n::languageId(0), ungula::i18n::Lang::English);
}

// --- Vertical offset ---

TEST_F(I18nTest, FontYOffsetDefaultsToZero) {
    ungula::i18n::addLanguage(ungula::i18n::Lang::English, strings_en, EN_COUNT);
    EXPECT_EQ(ungula::i18n::fontYOffset(), 0);
}

TEST_F(I18nTest, FontYOffsetReturnsRegisteredValue) {
    ungula::i18n::addLanguage(ungula::i18n::Lang::English, strings_en, EN_COUNT, 0);
    ungula::i18n::addLanguage(ungula::i18n::Lang::Spanish, strings_es, ES_COUNT, -3);
    ungula::i18n::addLanguage(ungula::i18n::Lang::Chinese, strings_cn, CN_COUNT, 2);

    ungula::i18n::setLanguage(0);
    EXPECT_EQ(ungula::i18n::fontYOffset(), 0);

    ungula::i18n::setLanguage(1);
    EXPECT_EQ(ungula::i18n::fontYOffset(), -3);

    ungula::i18n::setLanguage(2);
    EXPECT_EQ(ungula::i18n::fontYOffset(), 2);
}

TEST_F(I18nTest, FontYOffsetByIndexReturnsCorrectValue) {
    ungula::i18n::addLanguage(ungula::i18n::Lang::English, strings_en, EN_COUNT, 0);
    ungula::i18n::addLanguage(ungula::i18n::Lang::Spanish, strings_es, ES_COUNT, -5);

    EXPECT_EQ(ungula::i18n::fontYOffset(0), 0);
    EXPECT_EQ(ungula::i18n::fontYOffset(1), -5);
    EXPECT_EQ(ungula::i18n::fontYOffset(99), 0);  // invalid index returns 0
}

// --- CJK string content ---

TEST_F(I18nTest, ChineseStringsAreReturnedCorrectly) {
    ungula::i18n::addLanguage(ungula::i18n::Lang::Chinese, strings_cn, CN_COUNT);
    ungula::i18n::setLanguage(0);

    // Verify the raw UTF-8 bytes are returned as-is
    const char* start = ungula::i18n::str(0);
    EXPECT_EQ(static_cast<unsigned char>(start[0]), 0xE5);
    EXPECT_EQ(static_cast<unsigned char>(start[1]), 0xBC);
    EXPECT_EQ(static_cast<unsigned char>(start[2]), 0x80);
}

// --- Registration order independence ---

TEST_F(I18nTest, RegistrationOrderDoesNotAffectLookup) {
    // Register in reverse order: Chinese first, English second
    ungula::i18n::addLanguage(ungula::i18n::Lang::Chinese, strings_cn, CN_COUNT);
    ungula::i18n::addLanguage(ungula::i18n::Lang::English, strings_en, EN_COUNT);

    ungula::i18n::setLanguage(0);  // Chinese (registered first)
    EXPECT_STREQ(ungula::i18n::str(0), "\xe5\xbc\x80\xe5\xa7\x8b");

    ungula::i18n::setLanguage(1);  // English (registered second)
    EXPECT_STREQ(ungula::i18n::str(0), "START");
}
