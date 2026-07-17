cmake_minimum_required(VERSION 3.18)
project(ptolem C)

set(CMAKE_C_STANDARD 11)

set(SRC ${CMAKE_CURRENT_SOURCE_DIR}/../../..)

add_library(ptolem SHARED
    ${SRC}/src/ptolemy_ffi.c
    ${SRC}/src/monad.c
    ${SRC}/src/checkpoint.c
    ${SRC}/src/tokenizer.c
)

target_compile_options(ptolem PRIVATE -O2 -DNDEBUG -fvisibility=hidden)
target_link_libraries(ptolem android log m)
