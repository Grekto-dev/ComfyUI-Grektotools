# ComfyUI-Grektotools

A modular collection of custom utility nodes and compatibility bridges for **ComfyUI**, created by **Grekto** ([@Grekto-dev](https://github.com/Grekto-dev)).

Designed to streamline workflows, bridge format mismatches between native nodes and community extensions, and provide lightweight, dependable utility nodes.

---

## 📦 Installation

### Option 1: Via ComfyUI-Manager (Recommended)
1. Open the ComfyUI **Manager** from the side menu.
2. Click **"Install via Git URL"**.
3. Paste the repository URL:
   ```text
   https://github.com/Grekto-dev/ComfyUI-Grektotools.git
   ```
4. Click **OK** and restart ComfyUI.

### Option 2: Manual Installation (Git Clone)
Navigate to the `custom_nodes` folder in your ComfyUI installation and clone the repository:
```bash
cd ComfyUI/custom_nodes
git clone https://github.com/Grekto-dev/ComfyUI-Grektotools.git
```
Restart ComfyUI after cloning.

---

## 🛠️ Included Nodes

All nodes are located under the **`Grektotools`** category in the ComfyUI node menu.

### 1. `Get Path`
Automatically extracts the verified absolute file path on disk from virtually any ComfyUI data type or node output.

#### Problem Solved:
Native ComfyUI video loaders output modern `VIDEO` objects. However, many community extensions (such as VideoHelperSuite's `Load Video (Path)`) expect a `STRING` containing the actual filesystem path. **`Get Path`** acts as a universal bridge: it takes native video outputs (or audio/image metadata, VHS filenames, or relative strings) and outputs the absolute path string.

* **Inputs:**
  * **`source` (`*` wildcard):** Connects to any node output:
    * Native `VIDEO` (extracts stream source path)
    * `VHS_FILENAMES` (extracts saved output paths)
    * `AUDIO` / `IMAGE` (extracts metadata paths)
    * `STRING` (resolves relative names such as `video.mp4 [input]` to absolute disk paths)
  * **`manual_path` (`STRING`, optional):** Enter or paste a path directly into the widget when not using an input connection.
* **Outputs:**
  * **`path` (`STRING`):** Full normalized absolute file path (e.g. `E:/ComfyUI/input/sample.mp4`).
  * **`filename` (`STRING`):** File name with extension (e.g. `sample.mp4`).
  * **`directory` (`STRING`):** Directory containing the file.
  * **`exists` (`BOOLEAN`):** `True` if the file exists on disk.

---

### 2. `Get Width`
Extracts the width (in pixels) from any media source — seamlessly supporting **both images and videos**.

* **Supported Media Sources:**
  * **ComfyUI `IMAGE` batch:** PyTorch tensor `[B, H, W, C]`
  * **ComfyUI native `VIDEO` object:** `VideoFromFile`, `VideoInput`, or custom video streams
  * **ComfyUI `MASK` batch:** PyTorch tensor `[B, H, W]` or `[H, W]`
  * **ComfyUI `LATENT`:** Extracts corresponding pixel width (`latent.samples.shape[-1] * 8`)
  * **Media File Paths (`STRING`):** Resolves video files (`.mp4`, `.webm`, `.mkv`, `.mov`, etc.) or image files (`.png`, `.jpg`, `.webp`, etc.)
  * **PIL Images & NumPy Arrays**
* **Inputs:**
  * **`media` (`*` wildcard, optional):** Connect any IMAGE, native VIDEO, MASK, file path, or media node output.
  * **`manual_path` (`STRING`, optional):** Enter or paste an image/video file path directly.
* **Outputs:**
  * **`width` (`INT`):** Width in pixels as an integer (primary output, connects directly to Empty Latent, Resize, Crop, etc.).
  * **`width_float` (`FLOAT`):** Width in pixels as a float (for aspect ratio and mathematical calculations).
  * **`width_str` (`STRING`):** Width as text (for prompts, captioning, logging, or dynamic filename prefixes).

---

### 3. `Get Height`
Extracts the height (in pixels) from any media source — seamlessly supporting **both images and videos**.

* **Supported Media Sources:**
  * **ComfyUI `IMAGE` batch:** PyTorch tensor `[B, H, W, C]`
  * **ComfyUI native `VIDEO` object:** `VideoFromFile`, `VideoInput`, or custom video streams
  * **ComfyUI `MASK` batch:** PyTorch tensor `[B, H, W]` or `[H, W]`
  * **ComfyUI `LATENT`:** Extracts corresponding pixel height (`latent.samples.shape[-2] * 8`)
  * **Media File Paths (`STRING`):** Resolves video files (`.mp4`, `.webm`, `.mkv`, `.mov`, etc.) or image files (`.png`, `.jpg`, `.webp`, etc.)
  * **PIL Images & NumPy Arrays**
* **Inputs:**
  * **`media` (`*` wildcard, optional):** Connect any IMAGE, native VIDEO, MASK, file path, or media node output.
  * **`manual_path` (`STRING`, optional):** Enter or paste an image/video file path directly.
* **Outputs:**
  * **`height` (`INT`):** Height in pixels as an integer (primary output, connects directly to Empty Latent, Resize, Crop, etc.).
  * **`height_float` (`FLOAT`):** Height in pixels as a float (for aspect ratio and mathematical calculations).
  * **`height_str` (`STRING`):** Height as text (for prompts, captioning, logging, or dynamic filename prefixes).

---

## 💡 Example Workflows

### Native Video to Path Loader
```text
[Load Video (Native)]
         │ (VIDEO output)
         ▼
     [Get Path]
         │ ('path' string output)
         ▼
[Load Video (Path)] (VideoHelperSuite)
```

### Auto-Size Empty Latent from Video or Image
```text
[Load Video / Load Image]
       │             │
       ▼             ▼
  [Get Width]   [Get Height]
   (width: INT)  (height: INT)
       │             │
       ▼             ▼
    [Empty Latent Image]
```

---

## 🚀 Adding New Nodes

This pack uses an **automatic modular loader**. To add new nodes:

1. Create a new `.py` file inside the `nodes/` directory (e.g., `nodes/my_new_node.py`).
2. Define your node class and register `NODE_CLASS_MAPPINGS` and `NODE_DISPLAY_NAME_MAPPINGS`.
3. The root `__init__.py` automatically discovers and loads all modules in `nodes/`.

---

## 📄 License

Distributed under the **MIT License**. See [LICENSE](LICENSE) for more details.
