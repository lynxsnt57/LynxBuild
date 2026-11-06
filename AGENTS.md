# AGENTS.md — working on LynxBuild

This file is for AI agents (and humans) who will edit this repository. Read it before changing code.

## What this is

A Windows port/build of **Mine-imator 2.0.2 "Simply Upscaled"** (GameMaker → C++/Qt) with extra
model-import, furniture and panel features. The GameMaker project is the primary source for
UI/behaviour; the C++ project is partly generated from it and partly hand-written.

Base: upstream commit `f2594272` of
[YogaindoCR/Mine-imator-2.0.2-Simply-Upscaled-Build](https://github.com/YogaindoCR/Mine-imator-2.0.2-Simply-Upscaled-Build).

## Repository layout

| Path | Purpose |
| --- | --- |
| `simply-source/GmProject/` | **Primary source**: GML scripts, objects, sprites, data files |
| `simply-source/GmProject/Mine-imator.yyp` | GameMaker project file (resource list) |
| `simply-source/CppGen/` | GML→C++ generator (C# / .NET 8) |
| `simply-source/CppProject/` | C++ / Qt port |
| `simply-source/CppProject/Generated/` | **Generated** from `GmProject` by CppGen — do not hand-edit |
| `simply-source/CppProject/Asset/Sprites`, `.../Asset/Shaders` | Generated/exported assets |
| `simply-source/CppProject/External/` | Vendored prebuilt third-party libs (Win32/Win64/Mac/Linux) |
| `simply-source/CppProject/World/` | Hand-written world/import code (`BlockStyle`, `Builder`, `Chunk`, `Import`, `NBT`, `Preview`, `Section`, `World`, `FurnitureBake`, `FurnitureCache`) |
| `patches/` | Incremental unified diffs on top of `f2594272` |
| `assistant/` | Python/Tkinter build helper (`app.py` UI, `engine.py` build logic) |
| `Start-Mineimator-Assistant.cmd` | Launcher for the assistant |

## NOT in this repository (must be provided locally)

- `dev/` — third-party dependencies expected by CMake:
  **Qt 5.15.9**, **FFmpeg 5.0**, **FreeType 2.9.1**, **Libzip 1.9.2**, **OpenAL-Soft 1.22.0**.
  The build looks for `dev/Qt/5.15.9/build/lib/cmake/Qt5/Qt5Config.cmake`.
- `app-build/` — CMake build directory (created by the build).
- `test-build/` — deploy target containing `Mine-imator.exe` and `Data/`.
- `assistant-backups/`, `assistant-build.log` — local artifacts.

Because `dev/` is not vendored, **a bare clone cannot build until those dependencies are supplied**
next to `simply-source/` (or `DEV_DIR` is pointed at them).

## Build pipeline (Windows)

Prerequisites: **Python 3 + Tkinter**, **Git**, **.NET 8 SDK**, **CMake**, **Visual Studio 2022**
with the C++ workload.

1. **Regenerate C++ from GML** (only needed if GML/assets changed):

   ```
   dotnet run --project simply-source/CppGen/CppGen/CppGen.csproj -- ^
     simply-source/GmProject ^
     simply-source/CppProject/Generated ^
     simply-source/CppProject/Asset/Sprites ^
     simply-source/CppProject/Asset/Shaders ^
     simply-source/CppGen/gml.json
   ```

   Expect a line `Success!` in the output.

2. **Configure CMake** (with `DEV_DIR` set to the absolute path of `dev/`):

   ```
   set DEV_DIR=%CD%\dev
   cmake -S simply-source/CppProject -B app-build -G "Visual Studio 17 2022" -A x64
   ```

3. **Build Release**:

   ```
   cmake --build app-build --config Release --parallel 4
   ```

   Output: `app-build/Release/Mine-imator.exe`.

The assistant (`assistant/app.py`) automates all three steps; `engine.py` also copies the built
`Mine-imator.exe` and `GmProject/datafiles/Data/Languages/english.milanguage` into `test-build/`
(backing up the previous files into `assistant-backups/` first).

## Editing rules for agents

- Treat `simply-source/GmProject` as the source of truth. If you change GML, regenerate via CppGen.
- Do **not** hand-edit `CppProject/Generated/` — it is overwritten on regeneration.
- Hand-written C++ changes belong in `CppProject/` (e.g. `World/`), not in `Generated/`.
- `CppGen/Program.cs` is intentionally left unmodified. The assistant copies it to a temp dir and
  only patches the copy (to auto-answer prompts), so the original generator is never altered.
- Do not commit build outputs, logs, backups, `dev/`, `app-build/`, or `test-build/`.
- Patches in `patches/` are incremental and target `f2594272`. Apply them in order on a clean tree.
- Preserve encodings: C++/GML are UTF-8; some data/language files are UTF-8 (possibly with BOM).
- The toolchain is Windows-only (MSVC + Qt 5.15.9). Do not assume a Linux build works.

## Definition of done

A change is complete only after:

1. Regenerate (if GML/assets changed) → `Success!`
2. `cmake` configure + `cmake --build ... --config Release`
3. Run `app-build/Release/Mine-imator.exe` (or deploy to `test-build/` and launch it).

Full tool output is written to `assistant-build.log`.

## Known limitations

- The **Mods panel** is a UI placeholder: it does not import JARs, models or worlds, and does not
  add mod support by itself.
- Model-import and furniture features are **experimental**.
- `dev/` dependencies are not vendored here; see above.
