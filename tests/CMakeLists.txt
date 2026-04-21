cmake_minimum_required(VERSION 3.16)
project(ungula_i18n_lib_tests)

set(CMAKE_CXX_STANDARD 17)

set(FETCHCONTENT_BASE_DIR ${CMAKE_CURRENT_LIST_DIR}/vendor)

include(FetchContent)

FetchContent_Declare(
    googletest
    GIT_REPOSITORY https://github.com/google/googletest.git
    GIT_TAG v1.14.0
)
FetchContent_MakeAvailable(googletest)

set(LIB_SRC ${CMAKE_CURRENT_LIST_DIR}/../src)

include_directories(
    ${LIB_SRC}
)

add_compile_definitions(
    I18N_TESTING
)

add_executable(test_i18n
    test_i18n.cpp
    ${LIB_SRC}/i18n_engine/i18n.cpp
)
target_link_libraries(test_i18n gtest_main)

enable_testing()
include(GoogleTest)
gtest_discover_tests(test_i18n)
