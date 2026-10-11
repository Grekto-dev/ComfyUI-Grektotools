# ComfyUI-Grektotools

Coleção modular de nós personalizados e pontes de compatibilidade para o **ComfyUI**, desenvolvida por **Grekto** ([@Grekto-dev](https://github.com/Grekto-dev)).

Criado para simplificar fluxos de trabalho, resolver incompatibilidades entre nós nativos e extensões da comunidade, e servir como base extensível para novas ferramentas.

---

## 📦 Instalação

### Opção 1: Via ComfyUI-Manager (Recomendado)
1. No menu lateral do ComfyUI, abra o **Manager**.
2. Clique no botão **"Install via Git URL"** (ou "Custom Nodes Manager" -> "Install via Git URL").
3. Cole a URL do repositório:
   ```text
   https://github.com/Grekto-dev/ComfyUI-Grektotools.git
   ```
4. Clique em **OK** e reinicie o ComfyUI.

### Opção 2: Instalação Manual (Git Clone)
Navegue até a pasta `custom_nodes` da sua instalação do ComfyUI e clone o repositório:
```bash
cd ComfyUI/custom_nodes
git clone https://github.com/Grekto-dev/ComfyUI-Grektotools.git
```
Reinicie o ComfyUI após o clone.

---

## 🛠️ Nós Incluídos

### 1. `Get Path` (Categoria: `Grektotools`)

Extrai automaticamente o caminho absoluto no disco a partir de praticamente qualquer tipo de dado ou nó do ComfyUI.

#### Problema que resolve:
O novo nó nativo **`Load Video`** do ComfyUI cospe um tipo de dados moderno (`VIDEO`). No entanto, muitos nós consagrados da comunidade (como o **`Load Video (Path)`** do VideoHelperSuite) esperam receber uma `STRING` contendo o caminho real do arquivo no disco. 

O **`Get Path`** atua como uma ponte universal: recebe a saída do nó nativo (ou qualquer outro dado de arquivo) e cospe a `STRING` com o caminho absoluto verificado.

#### Entradas (Inputs):
* **`source` (Coringa `*`):** Aceita conexões de qualquer nó do ComfyUI:
  * **`VIDEO` (Nativo):** Extrai o caminho absoluto do arquivo carregado no player do `Load Video` nativo.
  * **`VHS_FILENAMES`:** Extrai o caminho do vídeo salvo pelo `VHS_VideoCombine`.
  * **`AUDIO` / `IMAGE` (Dicionários):** Extrai o caminho contido em metadados.
  * **`STRING`:** Resolve nomes relativos (ex.: `video.mp4`, `video.mp4 [input]`) para o caminho absoluto no disco.
* **`manual_path` (`STRING` opcional):** Permite digitar ou colar um caminho diretamente pelo widget se a conexão `source` não estiver ligada.

#### Saídas (Outputs):
* **`path` (`STRING`):** Caminho absoluto completo e normalizado (ex.: `E:/ComfyUI/input/video.mp4`). Conecte diretamente no slot `video` do nó `Load Video (Path)`.
* **`filename` (`STRING`):** Nome do arquivo com extensão (ex.: `video.mp4`).
* **`directory` (`STRING`):** Diretório onde o arquivo está localizado.
* **`exists` (`BOOLEAN`):** `True` se o arquivo foi verificado no disco.

#### Exemplo de Uso:
```text
[Load Video (Nativo)] 
         │ (saída VIDEO)
         ▼
     [Get Path]
         │ (saída 'path')
         ▼
[Load Video (Path)] (VideoHelperSuite)
         │ (entrada 'video')
         ▼
(Restante do seu workflow)
```

---

## 🚀 Como Adicionar Novos Nós ao Pack no Futuro

Este pack utiliza um **carregador modular automático**. Para criar e adicionar novos nós:

1. Vá até a pasta `nodes/` dentro de `ComfyUI-Grektotools`.
2. Crie um novo arquivo Python para a sua ferramenta (ex.: `nodes/meu_novo_no.py`).
3. No arquivo, defina a sua classe e inclua os dicionários padrão do ComfyUI:
   ```python
   class MeuNovoNo:
       # ...
       pass

   NODE_CLASS_MAPPINGS = {
       "MeuNovoNo": MeuNovoNo,
   }

   NODE_DISPLAY_NAME_MAPPINGS = {
       "MeuNovoNo": "Meu Novo Nó",
   }
   ```
4. **Pronto!** O `__init__.py` na raiz detecta e registra automaticamente qualquer arquivo `.py` adicionado na pasta `nodes/`. Você não precisa editar o arquivo principal.
5. Para publicar suas atualizações no GitHub:
   ```bash
   git add .
   git commit -m "Adiciona MeuNovoNo"
   git push
   ```

---

## 📄 Licença

Distribuído sob a licença **MIT**. Consulte o arquivo [LICENSE](LICENSE) para mais detalhes.
