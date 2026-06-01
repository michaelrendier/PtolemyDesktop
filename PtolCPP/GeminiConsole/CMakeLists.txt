cmake_minimum_required(VERSION 3.10)
project(GeminiNcursesChat CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED True)
set(CMAKE_POSITION_INDEPENDENT_CODE ON)

# Add cpr as a subdirectory
add_subdirectory(externals/cpr)

# Add nlohmann/json as a subdirectory
add_subdirectory(externals/json)

# Find ncurses (CURSES for CMake)
find_package(Curses REQUIRED)

add_executable(gemini_ncurses_chat main.cpp)

target_link_libraries(gemini_ncurses_chat PRIVATE
    cpr::cpr # This links cpr and its curl dependency
    nlohmann_json::nlohmann_json # This links nlohmann/json
    ${CURSES_LIBRARIES} # Links ncurses
)
