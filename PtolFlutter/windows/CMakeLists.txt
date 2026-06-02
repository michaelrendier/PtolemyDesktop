cmake_minimum_required(VERSION 3.18)
project(ptolemy_windows VERSION 1.0.0 LANGUAGES CXX C)

# Flutter boilerplate
cmake_policy(VERSION 3.14...3.25)
set(BINARY_NAME "ptolemy")

# Include Flutter generated plugins
include(flutter/generated_plugins.cmake OPTIONAL)

add_subdirectory("flutter")

set(SRC_DIR "${CMAKE_CURRENT_SOURCE_DIR}/..")

# ── ptolem native library ──────────────────────────────────────────────────────
add_library(ptolem SHARED
    ${SRC_DIR}/src/ptolemy_ffi.c
    ${SRC_DIR}/src/monad.c
    ${SRC_DIR}/src/checkpoint.c
    ${SRC_DIR}/src/tokenizer.c
)

set_target_properties(ptolem PROPERTIES
    C_STANDARD 11
    OUTPUT_NAME "ptolem"
)

target_compile_definitions(ptolem PRIVATE _CRT_SECURE_NO_WARNINGS _USE_MATH_DEFINES)
target_compile_options(ptolem PRIVATE /O2)

# math is in CRT on Windows — no -lm needed

# ── Flutter runner ────────────────────────────────────────────────────────────
add_executable(${BINARY_NAME} WIN32
    "runner/main.cpp"
    "runner/win32_window.cpp"
    "runner/flutter_window.cpp"
    "runner/utils.cpp"
    "runner/run_loop.cpp"
    "runner/Runner.rc"
)

target_compile_definitions(${BINARY_NAME} PRIVATE
    FLUTTER_VERSION="${FLUTTER_VERSION}"
    FLUTTER_VERSION_MAJOR=${FLUTTER_VERSION_MAJOR}
    FLUTTER_VERSION_MINOR=${FLUTTER_VERSION_MINOR}
    FLUTTER_VERSION_PATCH=${FLUTTER_VERSION_PATCH}
    FLUTTER_VERSION_BUILD=${FLUTTER_VERSION_BUILD}
)

apply_standard_settings(${BINARY_NAME})

target_compile_definitions(${BINARY_NAME} PRIVATE NOMINMAX)
target_link_libraries(${BINARY_NAME} PRIVATE flutter flutter_wrapper_app)
target_link_libraries(${BINARY_NAME} PRIVATE ptolem)
target_include_directories(${BINARY_NAME} PRIVATE "${CMAKE_SOURCE_DIR}")

add_dependencies(${BINARY_NAME} flutter_assemble)

# Copy ptolem.dll to output
add_custom_command(TARGET ${BINARY_NAME} POST_BUILD
    COMMAND ${CMAKE_COMMAND} -E copy
        $<TARGET_FILE:ptolem>
        $<TARGET_FILE_DIR:${BINARY_NAME}>
)

# Copy checkpoint to output
add_custom_command(TARGET ${BINARY_NAME} POST_BUILD
    COMMAND ${CMAKE_COMMAND} -E copy
        "${SRC_DIR}/assets/monad_wordnet.bin"
        "${CMAKE_BINARY_DIR}/runner/Release/monad_wordnet.bin"
    COMMAND_EXPAND_LISTS
)

set(INSTALL_BUNDLE_DATA_DIR "${CMAKE_INSTALL_PREFIX}/data")
set(INSTALL_BUNDLE_LIB_DIR "${CMAKE_INSTALL_PREFIX}")

install(TARGETS ${BINARY_NAME} RUNTIME DESTINATION "${CMAKE_INSTALL_PREFIX}"
    COMPONENT Runtime)
install(FILES $<TARGET_FILE:ptolem> DESTINATION "${CMAKE_INSTALL_PREFIX}"
    COMPONENT Runtime)
install(FILES "${FLUTTER_ICU_DATA_FILE}" DESTINATION "${INSTALL_BUNDLE_DATA_DIR}"
    COMPONENT Runtime)
install(FILES "${FLUTTER_LIBRARY}" DESTINATION "${CMAKE_INSTALL_PREFIX}"
    COMPONENT Runtime)

foreach(bundled_library ${PLUGIN_BUNDLED_LIBRARIES})
    install(FILES "${bundled_library}" DESTINATION "${CMAKE_INSTALL_PREFIX}"
        COMPONENT Runtime)
endforeach(bundled_library)
