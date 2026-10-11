"""
ComfyUI-Grektotools
Modular collection of custom nodes for ComfyUI developed by Grekto.
"""

import importlib
import os

NODE_CLASS_MAPPINGS = {}
NODE_DISPLAY_NAME_MAPPINGS = {}

# Directory where node modules are located
nodes_dir = os.path.join(os.path.dirname(__file__), "nodes")

if os.path.exists(nodes_dir):
    # Automatically scan and import all .py modules within 'nodes'
    for root, _, files in os.walk(nodes_dir):
        for file in sorted(files):
            if file.endswith(".py") and not file.startswith("__"):
                rel_path = os.path.relpath(os.path.join(root, file), os.path.dirname(__file__))
                mod_name = "." + rel_path[:-3].replace(os.sep, ".")
                try:
                    module = importlib.import_module(mod_name, package=__name__)
                    if hasattr(module, "NODE_CLASS_MAPPINGS"):
                        NODE_CLASS_MAPPINGS.update(module.NODE_CLASS_MAPPINGS)
                    if hasattr(module, "NODE_DISPLAY_NAME_MAPPINGS"):
                        NODE_DISPLAY_NAME_MAPPINGS.update(module.NODE_DISPLAY_NAME_MAPPINGS)
                except Exception as e:
                    print(f"[ComfyUI-Grektotools] Error loading module {mod_name}: {e}")

__all__ = ["NODE_CLASS_MAPPINGS", "NODE_DISPLAY_NAME_MAPPINGS"]
