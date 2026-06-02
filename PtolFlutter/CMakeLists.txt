cmake_minimum_required(VERSION 3.18)
project(ptolem VERSION 1.0.0 LANGUAGES C)

set(CMAKE_C_STANDARD 11)
set(CMAKE_C_STANDARD_REQUIRED ON)

set(PTOLEM_SRCS
    src/ptolemy_ffi.c
    src/monad.c
    src/checkpoint.c
    src/tokenizer.c
)

# ── Shared library for Android, macOS, Windows, Linux ─────────────────────────
# iOS uses STATIC (no dynamic loading allowed)
if(IOS)
    add_library(ptolem STATIC ${PTOLEM_SRCS})
else()
    add_library(ptolem SHARED ${PTOLEM_SRCS})
endif()

set_target_properties(ptolem PROPERTIES
    OUTPUT_NAME "ptolem"
    C_VISIBILITY_PRESET hidden
    VISIBILITY_INLINES_HIDDEN ON
)

target_compile_options(ptolem PRIVATE
    -O2
    -DNDEBUG
    -Wall
)

# ── Platform-specific linking ──────────────────────────────────────────────────
if(WIN32)
    # math is in the CRT on Windows
    target_compile_definitions(ptolem PRIVATE _CRT_SECURE_NO_WARNINGS)
else()
    target_link_libraries(ptolem PRIVATE m)
endif()

if(ANDROID)
    target_link_libraries(ptolem PRIVATE android log)
endif()

if(APPLE AND NOT IOS)
    set_target_properties(ptolem PROPERTIES
        INSTALL_RPATH "@loader_path"
        BUILD_WITH_INSTALL_RPATH TRUE
    )
endif()

# ── Install (for Flutter plugin packaging) ────────────────────────────────────
install(TARGETS ptolem
    LIBRARY DESTINATION "${CMAKE_INSTALL_PREFIX}"
    ARCHIVE DESTINATION "${CMAKE_INSTALL_PREFIX}"
    RUNTIME DESTINATION "${CMAKE_INSTALL_PREFIX}"
)
