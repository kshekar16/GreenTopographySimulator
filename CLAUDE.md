# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project

A minimal C++ project built with CMake. The only source is `main.cpp`, which compiles into a single executable target, `GreenTopographySimulator`.

## Build & Run

The existing `build/` directory is configured with the **Visual Studio 18 2026** generator. It is a multi-config generator, so you pick the configuration at build time with `--config`, not at configure time:

```sh
cmake -S . -B build                      # configure (only needed once, or after CMakeLists.txt changes)
cmake --build build --config Debug       # build
./build/Debug/GreenTopographySimulator.exe             # run (Release: build/Release/GreenTopographySimulator.exe)
```

## Tests

`CMakeLists.txt` includes CTest and calls `enable_testing()`, but no tests are registered yet. Register a test with `add_test(NAME <name> COMMAND <target>)`, then run:

```sh
ctest --test-dir build -C Debug                 # all tests
ctest --test-dir build -C Debug -R <name>       # single test by regex
```

## Packaging

CPack is included and uses the project name and version from `project(...)`. Build a package with `cpack --config build/CPackConfig.cmake -C Debug`.

## Notes

- `build/` and `cmake-build-*/` are gitignored, along with compiled artifacts (`*.exe`, `*.obj`, `*.pdb`, `*.dll`, `*.lib`).
- No C++ standard is set in `CMakeLists.txt`, so the compiler default applies. Add `set(CMAKE_CXX_STANDARD ...)` if newer language features are needed.
