Вот полностью обновлённый комплект файлов для проекта **fuckbr tools**:

---

## ✅ `README.md`

```markdown
# fuckbr tools

A Blender add-on for importing GTA San Andreas maps, cleaning `.dff` files, and exporting models for use in Unity, Unreal, and other game engines.

Install it like any regular Blender add-on — no setup required.

---

## 🧩 Features

### 🗺️ Map Importer
- Scans folders for `.ipl` map files
- Auto-detects related `.dff` models and textures
- Automatically places objects in the scene
- Correctly restores world positions **and** rotations (fixed W rotation)
- Optional: keep native world transform

### 📦 Export System
- Exports selected objects + used textures to `.zip`
- Supports `.fbx` and `.dff` formats
- Textures are auto-converted to `.png`
- Simple one-click export

### 🧹 DFF Cleaner
- Removes:
  - Collision meshes (`colmesh`, `colsphere`)
  - LODs
  - Dummy empties
  - Unused wheels
- Regenerates wheel meshes from placeholders (e.g. `wheel_rf`)
- Keeps clean scale, rotation, and position

---

## 🛠 How to Use

1. Open Blender and go to `Edit > Preferences > Add-ons`
2. Install the ZIP or place this folder into `scripts/addons/`
3. Enable **fuckbr tools**
4. Open the "fuckbr" tab in the right-side N-panel
5. Set the root folder containing `.ipl`, `.dff`, and textures
6. Import, clean, export — done.

---

## 📁 Asset Rules

- `.dff` models must be inside a folder under your root directory
- All textures **must be placed in the same folder as the corresponding `.dff`**
- Supported texture formats: `.png`, `.bmp`, `.jpg`, etc.
- Texture names must match the texture names used in `.dff`

```

example/
├─ map.ipl
├─ objects/
│  ├─ building.dff
│  ├─ building.png
│  ├─ road.dff
│  ├─ road.png

```

---

## ✅ Compatibility

- Blender 4.4+
- Tested with GTA SA mod assets
- Exports clean meshes to Unity / Unreal Engine

---

## 📜 License

See [`LICENSE_EN.md`](LICENSE_EN.md) and [`LICENSE_RU.md`](LICENSE_RU.md)  
This software requires attribution.  
