import os
import sys
from typing import Any, Tuple, Dict, Union

# AnyType accepts connections from any ComfyUI node type
class AnyType(str):
    """Allows the input socket to accept connections from any ComfyUI node type."""
    def __ne__(self, __value: object) -> bool:
        return False
    def __eq__(self, __value: object) -> bool:
        return True

any_type = AnyType("*")


def resolve_path(p: str) -> str:
    """Resolves relative paths, ComfyUI folder annotations, and normalizes path separators."""
    if not p:
        return ""
    p = str(p).strip().strip('"\'')
    
    # 1. Direct existing file check (absolute or relative)
    if os.path.isfile(p):
        return os.path.abspath(p).replace("\\", "/")
        
    # 2. Check ComfyUI annotations like "video.mp4 [input]" or "video.mp4 [output]"
    try:
        import folder_paths
        annotated = folder_paths.get_annotated_filepath(p)
        if annotated and os.path.isfile(annotated):
            return os.path.abspath(annotated).replace("\\", "/")
    except Exception:
        pass
        
    # 3. Check default ComfyUI directories (input, output, temp)
    try:
        import folder_paths
        for base in [
            folder_paths.get_input_directory(),
            folder_paths.get_output_directory(),
            folder_paths.get_temp_directory()
        ]:
            if base:
                cand = os.path.join(base, p)
                if os.path.isfile(cand):
                    return os.path.abspath(cand).replace("\\", "/")
    except Exception:
        pass
        
    # Return normalized absolute path
    return os.path.abspath(p).replace("\\", "/")


def extract_file_path(obj: Any) -> str:
    """Extracts a file path from virtually any ComfyUI object representation."""
    if obj is None:
        return ""
        
    # 1. String or PathLike
    if isinstance(obj, (str, os.PathLike)):
        clean = str(obj).strip().strip('"\'')
        if clean:
            return resolve_path(clean)
            
    # 2. Native ComfyUI Video object (e.g. VideoFromFile, VideoInput)
    if hasattr(obj, "get_stream_source") and callable(obj.get_stream_source):
        try:
            stream_src = obj.get_stream_source()
            if stream_src:
                return resolve_path(str(stream_src))
        except Exception:
            pass

    # Check common attributes where nodes and libraries store file paths
    for attr in [
        "_file", "file", "path", "filename", "filepath", "video_path",
        "audio_path", "source_file", "_VideoFromFile__file"
    ]:
        val = getattr(obj, attr, None)
        if val and isinstance(val, (str, os.PathLike)):
            return resolve_path(str(val))

    # Check internal cache of comfy_extras.nodes_video if available
    try:
        from comfy_extras.nodes_video import _preview_results
        if obj in _preview_results:
            cand = _preview_results[obj][0]
            if cand:
                return resolve_path(str(cand))
    except Exception:
        pass

    # 3. Dictionaries (e.g. audio returns, output metadata, wrappers)
    if isinstance(obj, dict):
        for key in ["fullpath", "path", "filename", "file", "video", "audio", "image", "filepath", "source"]:
            if key in obj and obj[key]:
                cand = extract_file_path(obj[key])
                if cand:
                    return cand

        # ComfyUI image/video save metadata: {"filename": "...", "subfolder": "...", "type": "output"}
        if "filename" in obj and ("subfolder" in obj or "type" in obj):
            fn = obj["filename"]
            sf = obj.get("subfolder", "")
            tp = obj.get("type", "output")
            try:
                import folder_paths
                if tp == "output":
                    base = folder_paths.get_output_directory()
                elif tp == "temp":
                    base = folder_paths.get_temp_directory()
                else:
                    base = folder_paths.get_input_directory()
                cand = os.path.join(base, sf, fn)
                return resolve_path(cand)
            except Exception:
                pass

    # 4. Lists or Tuples (e.g. VHS_FILENAMES: (save_output, [paths]), or lists of files)
    if isinstance(obj, (list, tuple)):
        # First try to find any item that immediately resolves to an existing file
        for item in obj:
            cand = extract_file_path(item)
            if cand and os.path.isfile(cand):
                return cand
        # If no file exists immediately on disk, return the first non-empty path
        for item in obj:
            cand = extract_file_path(item)
            if cand:
                return cand

    return ""


class GetPathNode:
    """
    'Get Path' node for ComfyUI-Grektotools.
    Accepts any input referring to a file (native VIDEO, AUDIO, IMAGE, VHS_FILENAMES, STRING, etc.)
    and extracts the verified absolute file path ready to connect into 'Load Video (Path)' or file loaders.
    """
    
    @classmethod
    def INPUT_TYPES(cls) -> Dict[str, Any]:
        return {
            "required": {},
            "optional": {
                "source": (
                    any_type,
                    {
                        "tooltip": "Connect any output representing a file (native VIDEO, AUDIO, VHS_FILENAMES, STRING, etc.)"
                    }
                ),
                "manual_path": (
                    "STRING",
                    {
                        "default": "",
                        "tooltip": "Or manually enter/paste the file path or filename here (if not using the connection)"
                    }
                ),
            }
        }

    RETURN_TYPES = ("STRING", "STRING", "STRING", "BOOLEAN")
    RETURN_NAMES = ("path", "filename", "directory", "exists")
    FUNCTION = "get_path"
    CATEGORY = "Grektotools"

    @classmethod
    def VALIDATE_INPUTS(cls, **kwargs) -> bool:
        return True

    def get_path(self, source: Any = None, manual_path: str = "") -> Dict[str, Any]:
        # 1. Prioritize 'source' connection if connected
        path = ""
        if source is not None:
            path = extract_file_path(source)
            
        # 2. If connection yielded no path or was not connected, use manual_path
        if not path and manual_path:
            path = extract_file_path(manual_path)

        filename = os.path.basename(path) if path else ""
        directory = os.path.dirname(path) if path else ""
        exists = os.path.isfile(path) if path else False

        if path:
            print(f"[Grektotools - Get Path] Detected file: {path} (Exists on disk: {exists})")
        else:
            print("[Grektotools - Get Path] No valid file path was identified from input.")

        return {
            "ui": {"text": [path]},
            "result": (path, filename, directory, exists)
        }


NODE_CLASS_MAPPINGS = {
    "GetPath": GetPathNode,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "GetPath": "Get Path",
}
