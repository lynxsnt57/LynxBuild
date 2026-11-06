# LynxBuild — Mine-imator "Simply Upscaled" port

Experimental Windows build of **Mine-imator 2.0.2 "Simply Upscaled"** with extra model-import,
furniture and panel features, plus a small assistant that applies patches and drives the build.

> Based on [YogaindoCR/Mine-imator-2.0.2-Simply-Upscaled-Build](https://github.com/YogaindoCR/Mine-imator-2.0.2-Simply-Upscaled-Build)
> at commit `f2594272`. All upstream code, assets and trademarks remain the property of their
> respective authors. This repository redistributes the upstream sources together with local
> modifications.

## What's inside

| Path | Contents |
| --- | --- |
| `simply-source/` | GameMaker project (`GmProject/`) and the generated C++ port (`CppProject/`, `CppGen/`), installer assets |
| `patches/` | Incremental `.patch` files (01–19) applied on top of the upstream base commit |
| `assistant/` | Python/Tkinter helper that applies a patch, runs the build and refreshes `test-build` |
| `Start-Mineimator-Assistant.cmd` | Launcher for the assistant (checks Python 3 + Tkinter) |

### Feature patches

The patches are incremental and target the upstream commit `f2594272`. Apply them in order.

| Patch | Feature |
| --- | --- |
| `01-community-recent-search` | Recent-project search on the community/startup screen |
| `02-mods-panel` | Mods panel (UI placeholder; not a mod loader) |
| `03-fabric-inspector` | Fabric inspector |
| `04-acacia-chair-import` | Acacia chair model import |
| `05-static-model-browser` | Static model browser |
| `06-standard-rotation` | Standard rotation handling |
| `07-model-preview` | Model preview |
| `08-acacia-blockbench` | Acacia Blockbench import |
| `09-fabric-model-formats` | Fabric model format support |
| `10-cobblemon-browser` | Cobblemon browser |
| `11-bedrock-bone-import` | Bedrock bone import |
| `12-bedrock-uv-fix` | Bedrock UV fix |
| `13-forge-clean-panel` | Forge clean panel |
| `15-after-13`, `15-after-14`, `15-fix-libzip-static` | Consolidated 15-series updates + static libzip fix |
| `16-furniture-textures` | Furniture textures |
| `17-immersive-furniture-experimental` | Immersive furniture (experimental) |
| `18-immersive-colors-after-17` | Immersive colors follow-up |
| `19-lab-tube-glass-after-18` | Lab tube glass follow-up |

The `simply-source/` tree additionally contains work-in-progress C++ files such as
`CppProject/World/FurnitureBake.*` and `CppProject/World/FurnitureCache.*`.

## Building

Requirements: Windows, **Python 3 with Tkinter**, **Git**, **.NET 8**, **CMake** and
**Visual Studio 2022** with the C++ workload.

1. Clone the repository.
2. Run `Start-Mineimator-Assistant.cmd`.
3. In the assistant: pick a `.patch` → **Check** → **Apply** → **Build** → **Update test-build** → **Launch test-build**.

The assistant keeps a backup of the previous executable and language file in
`assistant-backups/` before replacing them. Projects and an installed Vexel copy are not touched.

## Notes

- These are experimental modifications. Keep backups before applying patches.
- Do not apply third-party patches you do not understand.
- The assistant does not install mods or add mod support by itself; the Mods panel is a UI
  placeholder that does not import JARs, models or worlds.
- Do not overwrite an existing Mine-imator / Vexel installation when testing.

## Credits

- **Mine-imator** — David Norgren and contributors — <https://www.mineimator.com>
- **Simply Upscaled Build** — YogaindoCR and contributors (upstream)
- **Port patches and assistant** — LynxBuild (lynxsnt57)

## License

This repository inherits the upstream project's terms; see the upstream repository for the
applicable license. Upstream code and assets are redistributed here only as part of a
modified build. If you are an upstream author and want something removed, please open an issue.
