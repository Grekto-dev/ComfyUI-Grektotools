import os
import sys
from typing import Any, Tuple, Dict, Union
from PIL import Image

try:
    import torch
except ImportError:
    torch = None

try:
    import numpy as np
except ImportError:
    np = None

from .get_path import any_type, resolve_path, extract_file_path


def get_media_dimensions(obj: Any) -> Tuple[int, int]:
    """
    Extracts (width, height) in pixels from virtually any media representation in ComfyUI:
    - ComfyUI IMAGE tensor: torch.Tensor with shape [B, H, W, C]
    - ComfyUI MASK tensor: torch.Tensor with shape [B, H, W] or [H, W]
    - Native VIDEO object: VideoFromFile, VideoInput with get_dimensions() or components
    - PIL.Image: Image.Image
    - NumPy arrays: ndarray with shapes [B, H, W, C], [H, W, C], or [H, W]
    - ComfyUI LATENT dictionary: {"samples": torch.Tensor [B, C, H//8, W//8]}
    - Dictionaries containing images, video, dimensions, or file paths
    - File paths (string or PathLike) pointing to video (.mp4, .webm, etc.) or image files
    - Lists or tuples of the above
    Returns (width, height) as integers. Returns (0, 0) if undetermined.
    """
    if obj is None:
        return 0, 0

    # 1. PyTorch Tensor (IMAGE, MASK, etc.)
    if torch is not None and isinstance(obj, torch.Tensor):
        if obj.ndim == 4:
            # ComfyUI standard IMAGE batch: [B, H, W, C]
            return int(obj.shape[2]), int(obj.shape[1])
        elif obj.ndim == 3:
            # Check if unbatched image [H, W, C] vs mask batch [B, H, W]
            if obj.shape[2] in (1, 3, 4) and obj.shape[0] > 4:
                return int(obj.shape[1]), int(obj.shape[0])
            else:
                # Standard ComfyUI MASK batch [B, H, W]
                return int(obj.shape[2]), int(obj.shape[1])
        elif obj.ndim == 2:
            # Single 2D mask [H, W]
            return int(obj.shape[1]), int(obj.shape[0])

    # 2. Native ComfyUI Video object (VideoFromFile, VideoInput)
    if hasattr(obj, "get_dimensions") and callable(obj.get_dimensions):
        try:
            dims = obj.get_dimensions()
            if dims and len(dims) >= 2 and dims[0] and dims[1]:
                return int(dims[0]), int(dims[1])
        except Exception:
            pass

    if hasattr(obj, "_get_display_dimensions") and callable(obj._get_display_dimensions):
        try:
            dims = obj._get_display_dimensions()
            if dims and len(dims) >= 2 and dims[0] and dims[1]:
                return int(dims[0]), int(dims[1])
        except Exception:
            pass

    if hasattr(obj, "get_components") and callable(obj.get_components):
        try:
            comp = obj.get_components()
            if hasattr(comp, "images") and comp.images is not None:
                w, h = get_media_dimensions(comp.images)
                if w > 0 and h > 0:
                    return w, h
        except Exception:
            pass

    if hasattr(obj, "width") and hasattr(obj, "height"):
        try:
            w, h = obj.width, obj.height
            if isinstance(w, (int, float)) and isinstance(h, (int, float)) and w > 0 and h > 0:
                return int(w), int(h)
        except Exception:
            pass

    # 3. PIL Image
    if isinstance(obj, Image.Image):
        return int(obj.width), int(obj.height)

    # 4. NumPy Array
    if np is not None and isinstance(obj, np.ndarray):
        if obj.ndim == 4:
            return int(obj.shape[2]), int(obj.shape[1])
        elif obj.ndim == 3:
            if obj.shape[2] in (1, 3, 4) and obj.shape[0] > 4:
                return int(obj.shape[1]), int(obj.shape[0])
            else:
                return int(obj.shape[2]), int(obj.shape[1])
        elif obj.ndim == 2:
            return int(obj.shape[1]), int(obj.shape[0])

    # 5. Dictionaries (Latents, custom wrappers, metadata)
    if isinstance(obj, dict):
        if "samples" in obj and torch is not None and isinstance(obj["samples"], torch.Tensor):
            # ComfyUI Latent dictionary [B, C, H//8, W//8]
            return int(obj["samples"].shape[-1] * 8), int(obj["samples"].shape[-2] * 8)

        for key in ["images", "image", "video"]:
            if key in obj and obj[key] is not None:
                w, h = get_media_dimensions(obj[key])
                if w > 0 and h > 0:
                    return w, h

        if "width" in obj and "height" in obj:
            try:
                w, h = int(obj["width"]), int(obj["height"])
                if w > 0 and h > 0:
                    return w, h
            except Exception:
                pass

        cand_path = extract_file_path(obj)
        if cand_path:
            w, h = get_media_dimensions(cand_path)
            if w > 0 and h > 0:
                return w, h

    # 6. Lists or Tuples
    if isinstance(obj, (list, tuple)):
        for item in obj:
            w, h = get_media_dimensions(item)
            if w > 0 and h > 0:
                return w, h

    # 7. File Paths (Strings or PathLike)
    if isinstance(obj, (str, os.PathLike)):
        path = extract_file_path(obj)
        if not path:
            path = resolve_path(str(obj))

        if path and os.path.isfile(path):
            # 7.1 Try PIL (fast for image files)
            try:
                with Image.open(path) as img:
                    return int(img.width), int(img.height)
            except Exception:
                pass

            # 7.2 Try PyAV (fast for video containers)
            try:
                import av
                with av.open(path) as container:
                    if len(container.streams.video) > 0:
                        stream = container.streams.video[0]
                        w = stream.codec_context.width or stream.width
                        h = stream.codec_context.height or stream.height
                        if w and h:
                            return int(w), int(h)
            except Exception:
                pass

            # 7.3 Try OpenCV (fallback for video files)
            try:
                import cv2
                cap = cv2.VideoCapture(path)
                if cap.isOpened():
                    w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
                    h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
                    cap.release()
                    if w > 0 and h > 0:
                        return w, h
            except Exception:
                pass

    return 0, 0


class GetWidthNode:
    """
    'Get Width' node for ComfyUI-Grektotools.
    Extracts the pixel width from any media source (IMAGE, native VIDEO, MASK, or file path).
    Returns width as integer, float, and string for maximum workflow compatibility.
    """

    @classmethod
    def INPUT_TYPES(cls) -> Dict[str, Any]:
        return {
            "required": {},
            "optional": {
                "media": (
                    any_type,
                    {
                        "tooltip": "Connect any IMAGE, native VIDEO, MASK, file path, or media node to get its width."
                    }
                ),
                "manual_path": (
                    "STRING",
                    {
                        "default": "",
                        "tooltip": "Or manually enter/paste an image or video file path here (if not using the media connection)."
                    }
                ),
            }
        }

    RETURN_TYPES = ("INT", "FLOAT", "STRING")
    RETURN_NAMES = ("width", "width_float", "width_str")
    OUTPUT_TOOLTIPS = (
        "Width in pixels as an integer (ideal for Empty Latent, Resize, Crop)",
        "Width in pixels as a float (ideal for math, aspect ratio calculations)",
        "Width in pixels as a string (ideal for prompt text, logging, file naming)",
    )
    FUNCTION = "get_width"
    CATEGORY = "Grektotools"

    @classmethod
    def VALIDATE_INPUTS(cls, **kwargs) -> bool:
        return True

    def get_width(self, media: Any = None, manual_path: str = "") -> Dict[str, Any]:
        width, height = 0, 0
        if media is not None:
            width, height = get_media_dimensions(media)

        if width <= 0 and manual_path:
            width, height = get_media_dimensions(manual_path)

        if width > 0:
            print(f"[Grektotools - Get Width] Detected width: {width}px (height: {height}px)")
        else:
            print("[Grektotools - Get Width] Warning: Could not determine width from the provided input (returning 0).")

        return {
            "ui": {"text": [str(width)]},
            "result": (int(width), float(width), str(width))
        }


class GetHeightNode:
    """
    'Get Height' node for ComfyUI-Grektotools.
    Extracts the pixel height from any media source (IMAGE, native VIDEO, MASK, or file path).
    Returns height as integer, float, and string for maximum workflow compatibility.
    """

    @classmethod
    def INPUT_TYPES(cls) -> Dict[str, Any]:
        return {
            "required": {},
            "optional": {
                "media": (
                    any_type,
                    {
                        "tooltip": "Connect any IMAGE, native VIDEO, MASK, file path, or media node to get its height."
                    }
                ),
                "manual_path": (
                    "STRING",
                    {
                        "default": "",
                        "tooltip": "Or manually enter/paste an image or video file path here (if not using the media connection)."
                    }
                ),
            }
        }

    RETURN_TYPES = ("INT", "FLOAT", "STRING")
    RETURN_NAMES = ("height", "height_float", "height_str")
    OUTPUT_TOOLTIPS = (
        "Height in pixels as an integer (ideal for Empty Latent, Resize, Crop)",
        "Height in pixels as a float (ideal for math, aspect ratio calculations)",
        "Height in pixels as a string (ideal for prompt text, logging, file naming)",
    )
    FUNCTION = "get_height"
    CATEGORY = "Grektotools"

    @classmethod
    def VALIDATE_INPUTS(cls, **kwargs) -> bool:
        return True

    def get_height(self, media: Any = None, manual_path: str = "") -> Dict[str, Any]:
        width, height = 0, 0
        if media is not None:
            width, height = get_media_dimensions(media)

        if height <= 0 and manual_path:
            width, height = get_media_dimensions(manual_path)

        if height > 0:
            print(f"[Grektotools - Get Height] Detected height: {height}px (width: {width}px)")
        else:
            print("[Grektotools - Get Height] Warning: Could not determine height from the provided input (returning 0).")

        return {
            "ui": {"text": [str(height)]},
            "result": (int(height), float(height), str(height))
        }


NODE_CLASS_MAPPINGS = {
    "GetWidth": GetWidthNode,
    "GetHeight": GetHeightNode,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "GetWidth": "Get Width",
    "GetHeight": "Get Height",
}
