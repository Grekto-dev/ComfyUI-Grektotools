import os
import sys
from typing import Any, Tuple, Dict, Union

# Tipo AnyType que aceita conexão com qualquer tipo de nó no ComfyUI
class AnyType(str):
    """Permite que o socket de entrada aceite conexões de qualquer tipo de nó."""
    def __ne__(self, __value: object) -> bool:
        return False
    def __eq__(self, __value: object) -> bool:
        return True

any_type = AnyType("*")


def resolve_path(p: str) -> str:
    """Resolve caminhos relativos, anotações de pasta do ComfyUI e normaliza barras."""
    if not p:
        return ""
    p = str(p).strip().strip('"\'')
    
    # 1. Se já for um arquivo existente absoluto ou relativo direto
    if os.path.isfile(p):
        return os.path.abspath(p).replace("\\", "/")
        
    # 2. Verificar anotações do ComfyUI como "video.mp4 [input]" ou "video.mp4 [output]"
    try:
        import folder_paths
        annotated = folder_paths.get_annotated_filepath(p)
        if annotated and os.path.isfile(annotated):
            return os.path.abspath(annotated).replace("\\", "/")
    except Exception:
        pass
        
    # 3. Tentar encontrar nas pastas padrão do ComfyUI (input, output, temp)
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
        
    # Retorna o caminho absoluto normalizado
    return os.path.abspath(p).replace("\\", "/")


def extract_file_path(obj: Any) -> str:
    """Extrai o caminho de arquivo a partir de praticamente qualquer objeto do ComfyUI."""
    if obj is None:
        return ""
        
    # 1. String ou Path
    if isinstance(obj, (str, os.PathLike)):
        clean = str(obj).strip().strip('"\'')
        if clean:
            return resolve_path(clean)
            
    # 2. Objeto de Vídeo nativo do ComfyUI (ex: VideoFromFile, VideoInput da API moderna)
    if hasattr(obj, "get_stream_source") and callable(obj.get_stream_source):
        try:
            stream_src = obj.get_stream_source()
            if stream_src:
                return resolve_path(str(stream_src))
        except Exception:
            pass

    # Checar atributos comuns onde nós e bibliotecas guardam caminhos
    for attr in [
        "_file", "file", "path", "filename", "filepath", "video_path",
        "audio_path", "source_file", "_VideoFromFile__file"
    ]:
        val = getattr(obj, attr, None)
        if val and isinstance(val, (str, os.PathLike)):
            return resolve_path(str(val))

    # Checar cache interno do comfy_extras.nodes_video se disponível
    try:
        from comfy_extras.nodes_video import _preview_results
        if obj in _preview_results:
            cand = _preview_results[obj][0]
            if cand:
                return resolve_path(str(cand))
    except Exception:
        pass

    # 3. Dicionários (ex: retornos de áudio, metadados de output, wrappers)
    if isinstance(obj, dict):
        for key in ["fullpath", "path", "filename", "file", "video", "audio", "image", "filepath", "source"]:
            if key in obj and obj[key]:
                cand = extract_file_path(obj[key])
                if cand:
                    return cand

        # Formato de imagem/vídeo salvo pelo ComfyUI: {"filename": "...", "subfolder": "...", "type": "output"}
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

    # 4. Listas ou Tuplas (ex: VHS_FILENAMES: (save_output, [paths]), ou listas de arquivos)
    if isinstance(obj, (list, tuple)):
        # Primeiro tenta achar algum item que resulte em arquivo existente
        for item in obj:
            cand = extract_file_path(item)
            if cand and os.path.isfile(cand):
                return cand
        # Se nenhum arquivo existir imediatamente no disco, pega o primeiro caminho não vazio
        for item in obj:
            cand = extract_file_path(item)
            if cand:
                return cand

    return ""


class GetPathNode:
    """
    Nó 'Get Path' do ComfyUI-Grektotools.
    Aceita qualquer entrada referente a um arquivo (VIDEO nativo, AUDIO, IMAGE, VHS_FILENAMES, STRING, etc.)
    e extrai o caminho absoluto do arquivo pronto para conectar no 'Load Video (Path)' ou qualquer nó de arquivo.
    """
    
    @classmethod
    def INPUT_TYPES(cls) -> Dict[str, Any]:
        return {
            "required": {},
            "optional": {
                "source": (
                    any_type,
                    {
                        "tooltip": "Conecte qualquer saída que represente um arquivo (VIDEO nativo, AUDIO, VHS_FILENAMES, STRING, etc.)"
                    }
                ),
                "manual_path": (
                    "STRING",
                    {
                        "default": "",
                        "tooltip": "Ou digite/cole manualmente o caminho ou nome do arquivo aqui (caso não use a conexão)"
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
        # Permite validação dinâmica de qualquer tipo sem travar o prompt antes de rodar
        return True

    def get_path(self, source: Any = None, manual_path: str = "") -> Dict[str, Any]:
        # 1. Prioriza a conexão 'source' se foi conectada
        path = ""
        if source is not None:
            path = extract_file_path(source)
            
        # 2. Se a conexão não gerou caminho ou não foi ligada, usa manual_path
        if not path and manual_path:
            path = extract_file_path(manual_path)

        filename = os.path.basename(path) if path else ""
        directory = os.path.dirname(path) if path else ""
        exists = os.path.isfile(path) if path else False

        if path:
            print(f"[Grektotools - Get Path] Arquivo detectado: {path} (Existe no disco: {exists})")
        else:
            print("[Grektotools - Get Path] Nenhum caminho de arquivo foi identificado na entrada.")

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
