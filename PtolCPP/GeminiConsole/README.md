# GeminiConsole

ncurses-based terminal chat client for the Gemini API.

## Dependencies
- libcpr (HTTP)
- nlohmann/json
- ncursesw

## Build
```bash
mkdir build && cd build
cmake ..
make
```

## Runtime
Set `GEMINI_API_KEY` environment variable before running.

## Status
Working. Threading is stubbed — synchronous API calls block UI during response.
TODO: Async API call on separate thread, mutex-guarded UI update on return.
