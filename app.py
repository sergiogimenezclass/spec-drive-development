import os
import json
import logging
from typing import Dict, Any, List, Optional
from fastapi import FastAPI, HTTPException, Header, Request
from fastapi.responses import FileResponse, JSONResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import google.generativeai as genai

# Configuración de logs
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("spec-ide-backend")

# Cargar variables de entorno desde un archivo .env si existe
def load_dotenv():
    dotenv_path = os.path.join(os.path.dirname(__file__), ".env")
    if os.path.exists(dotenv_path):
        logger.info("Cargando variables desde archivo .env local")
        with open(dotenv_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#"):
                    parts = line.split("=", 1)
                    if len(parts) == 2:
                        key = parts[0].strip()
                        val = parts[1].strip().strip('"').strip("'")
                        os.environ[key] = val

import project_manager

load_dotenv()

app = FastAPI(title="Spec IDE Backend")

ROOT_APP_DIR = os.path.abspath(os.path.dirname(__file__))

def register_recent_project(path: str):
    project_manager.register_project(path)

def load_saved_target_project_path() -> str:
    return project_manager.load_active_project_path()

# Estado global de la ruta destino del proyecto activo
TARGET_PROJECT_PATH = load_saved_target_project_path()

def get_target_project_path() -> str:
    global TARGET_PROJECT_PATH
    return TARGET_PROJECT_PATH

def set_target_project_path(path: str) -> str:
    global TARGET_PROJECT_PATH
    abs_path = project_manager.set_active_project(path)
    TARGET_PROJECT_PATH = abs_path
    return TARGET_PROJECT_PATH

def get_project_file() -> str:
    return os.path.join(get_target_project_path(), "project.json")

def get_specs_dir() -> str:
    return os.path.join(get_target_project_path(), "specs")

class SetProjectPathRequest(BaseModel):
    project_path: str

class DeleteProjectRequest(BaseModel):
    project_path: str
    delete_files: bool = False

class IdeaAnalysisRequest(BaseModel):
    idea: str

class NextQuestionsRequest(BaseModel):
    idea: str
    answers: Dict[str, Any]

class SaveProjectRequest(BaseModel):
    project_data: Dict[str, Any]
    force_regenerate: Optional[bool] = False

class PlanFeaturesRequest(BaseModel):
    project_data: Dict[str, Any]
    custom_feature: Optional[str] = None

class DiagramRequest(BaseModel):
    diagram_type: str  # 'er', 'flow', 'architecture'
    answers: Dict[str, Any]

class CopilotRequest(BaseModel):
    prompt: str
    activeFile: str
    projectData: Dict[str, Any]

class CopilotChatRequest(BaseModel):
    message: str
    history: Optional[List[Dict[str, str]]] = []
    project_data: Dict[str, Any]

class ExploreExtractRequest(BaseModel):
    idea: Optional[str] = ""
    history: List[Dict[str, Any]] = []

class AutocompleteFileRequest(BaseModel):
    project_data: Dict[str, Any]
    filename: str

import urllib.request
import urllib.error

def is_quota_error(err_msg: str) -> bool:
    msg_lower = (err_msg or "").lower()
    quota_indicators = [
        "429", "quota", "resourceexhausted", "rate_limit", "rate limit",
        "exceeded your current quota", "too many requests", "limit: 20", "out of credits",
        "over_query_limit", "resource_exhausted"
    ]
    return any(ind in msg_lower for ind in quota_indicators)

def _get_fallback_candidates(current_model: str) -> List[str]:
    all_models = ["gemini-flash-latest", "gemini-2.5-flash", "gemini-2.0-flash", "gemini-2.5-flash-lite", "gemini-3.1-pro-preview"]
    return [m for m in all_models if m != current_model]

def is_deepseek_key_or_model(key: str, model_name: str) -> bool:
    k = (key or "").strip()
    m = (model_name or "").strip().lower()
    return k.startswith("sk-") or "deepseek" in m

class UnifiedResponse:
    def __init__(self, text: str):
        self.text = text

    def __iter__(self):
        yield self

def call_openai_compatible_api(api_key: str, model_name: str, messages: list, json_mode: bool = False, base_url: str = "https://api.deepseek.com/chat/completions") -> str:
    clean_key = (api_key or "").strip()
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {clean_key}"
    }
    m_name = model_name if model_name in ["deepseek-chat", "deepseek-reasoner"] else "deepseek-chat"
    payload = {
        "model": m_name,
        "messages": messages,
        "temperature": 0.3
    }
    if json_mode:
        payload["response_format"] = {"type": "json_object"}
        
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(base_url, data=data, headers=headers, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=120) as response:
            res_json = json.loads(response.read().decode("utf-8"))
            return res_json["choices"][0]["message"]["content"]
    except urllib.error.HTTPError as e:
        err_body = e.read().decode("utf-8")
        logger.error(f"HTTPError desde DeepSeek API ({e.code}): {err_body}")
        if e.code == 429:
            raise HTTPException(status_code=429, detail=f"⚠️ DeepSeek Límite de Cuota Alcanzado (429): {err_body}")
        elif e.code == 401:
            raise HTTPException(status_code=401, detail=f"⚠️ DeepSeek API Key no válida (401): {err_body}")
        else:
            raise HTTPException(status_code=e.code, detail=f"⚠️ Error en servicio DeepSeek ({e.code}): {err_body}")
    except Exception as e:
        logger.error(f"Error conectando con DeepSeek API: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error al conectar con servidor DeepSeek: {str(e)}")

def call_openai_compatible_api_stream(api_key: str, model_name: str, messages: list, base_url: str = "https://api.deepseek.com/chat/completions"):
    clean_key = (api_key or "").strip()
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {clean_key}"
    }
    m_name = model_name if model_name in ["deepseek-chat", "deepseek-reasoner"] else "deepseek-chat"
    payload = {
        "model": m_name,
        "messages": messages,
        "temperature": 0.3,
        "stream": True
    }
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(base_url, data=data, headers=headers, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=120) as response:
            for line in response:
                line_str = line.decode("utf-8").strip()
                if line_str.startswith("data: "):
                    data_body = line_str[6:].strip()
                    if data_body == "[DONE]":
                        break
                    try:
                        res_json = json.loads(data_body)
                        choices = res_json.get("choices", [])
                        if choices:
                            delta = choices[0].get("delta", {})
                            content = delta.get("content", "")
                            if content:
                                yield UnifiedResponse(content)
                    except Exception:
                        pass
    except urllib.error.HTTPError as e:
        err_body = e.read().decode("utf-8")
        logger.error(f"HTTPError desde DeepSeek API ({e.code}): {err_body}")
        if e.code == 429:
            raise HTTPException(status_code=429, detail=f"⚠️ DeepSeek Límite de Cuota Alcanzado (429): {err_body}")
        elif e.code == 401:
            raise HTTPException(status_code=401, detail=f"⚠️ DeepSeek API Key no válida (401): {err_body}")
        else:
            raise HTTPException(status_code=e.code, detail=f"⚠️ Error en servicio DeepSeek ({e.code}): {err_body}")
    except Exception as e:
        logger.error(f"Error conectando con DeepSeek API: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error al conectar con servidor DeepSeek: {str(e)}")

class DeepSeekChatSessionWrapper:
    def __init__(self, key: str, model_name: str, history=None):
        self.key = key
        self.model_name = model_name
        self.history = []
        if history:
            for h in history:
                role = "assistant" if h.get("role") in ["model", "assistant"] else "user"
                parts = h.get("parts", [])
                content = parts[0] if isinstance(parts, list) and parts else h.get("content", "")
                if isinstance(content, dict):
                    content = content.get("text", str(content))
                self.history.append({"role": role, "content": str(content)})

    def send_message(self, content, stream=False, **kwargs):
        user_content = str(content)
        self.history.append({"role": "user", "content": user_content})
        if stream:
            return call_openai_compatible_api_stream(self.key, self.model_name, self.history)
        res_text = call_openai_compatible_api(self.key, self.model_name, self.history)
        self.history.append({"role": "assistant", "content": res_text})
        return UnifiedResponse(res_text)


class GeminiChatSessionWrapper:
    def __init__(self, generative_model, history=None, model_wrapper=None, key_used=None, **kwargs):
        self.chat_session = generative_model.start_chat(history=history or [], **kwargs)
        self.history = history or []
        self.model_wrapper = model_wrapper
        self.key_used = key_used
        self.kwargs = kwargs

    def send_message(self, content, **kwargs):
        try:
            return self.chat_session.send_message(content, **kwargs)
        except Exception as e:
            err_msg = str(e)
            err_lower = err_msg.lower()
            current_m = getattr(self.model_wrapper, 'model_name', 'gemini-2.5-flash')
            key_to_use = self.key_used or (self.model_wrapper.primary_key if self.model_wrapper and self.model_wrapper.primary_key else os.environ.get("GEMINI_API_KEY", "")).strip()

            # Intentar fallback transparente a gemini-flash-latest u otros modelos disponibles antes de lanzar 429
            if is_quota_error(err_msg) or "404" in err_lower or "not found" in err_lower or "unsupported" in err_lower:
                logger.warning(f"Error en chat ('{current_m}'). Intentando fallback secuencial con modelos alternativos. Detalle: {err_msg}")
                if key_to_use:
                    genai.configure(api_key=key_to_use)
                    for fb_model in _get_fallback_candidates(current_m):
                        try:
                            logger.info(f"Reintentando chat con modelo alternativo '{fb_model}'")
                            m_fb = genai.GenerativeModel(fb_model)
                            chat_fb = m_fb.start_chat(history=self.history, **self.kwargs)
                            return chat_fb.send_message(content, **kwargs)
                        except Exception as fb_e:
                            fb_err_msg = str(fb_e)
                            logger.error(f"Fallback de chat con '{fb_model}' falló: {fb_err_msg}")
                            err_msg = fb_err_msg

            if is_quota_error(err_msg):
                raise HTTPException(
                    status_code=429,
                    detail=f"⚠️ Límite de Cuota Alcanzado (429/Quota Exceeded): {err_msg}. Ingresa una clave de resguardo o cambia el modelo en el modal."
                )

            if "401" in err_msg or "invalid" in err_msg.lower() or "api_key" in err_msg.lower():
                raise HTTPException(
                    status_code=401,
                    detail=f"⚠️ API Key no válida (401): {err_msg}"
                )
            raise HTTPException(status_code=500, detail=f"Error en Chat Copilot: {err_msg}")

class GeminiModelWrapper:
    def __init__(self, primary_key: str = "", fallback_key: str = "", model_name: str = "gemini-2.5-flash"):
        self.primary_key = (primary_key or "").strip()
        self.fallback_key = (fallback_key or "").strip()
        m_name = (model_name or "gemini-2.5-flash").strip()
        if m_name in ["gemini-2.5-pro", "gemini-1.5-pro"]:
            m_name = "gemini-3.1-pro-preview"
        elif m_name == "gemini-1.5-flash":
            m_name = "gemini-2.5-flash"
        self.model_name = m_name

    def generate_content(self, contents, **kwargs):
        keys_to_try = [k for k in [self.primary_key, self.fallback_key] if k]
        if not keys_to_try:
            keys_to_try = [k for k in [os.environ.get("GEMINI_API_KEY", "").strip(), os.environ.get("GEMINI_FALLBACK_API_KEY", "").strip()] if k]

        if not keys_to_try:
            raise HTTPException(
                status_code=401, 
                detail="Falta la API Key. Configúrala en la interfaz web (Gemini o DeepSeek sk-...)."
            )

        last_error = None
        has_any_quota_err = False
        quota_err_str = ""

        for idx, key in enumerate(keys_to_try):
            if is_deepseek_key_or_model(key, self.model_name):
                try:
                    logger.info(f"Usando proveedor DeepSeek para clave/modelo '{self.model_name}'")
                    messages = []
                    json_mode = False
                    if isinstance(contents, str):
                        messages = [{"role": "user", "content": contents}]
                    elif isinstance(contents, list):
                        messages = [{"role": "user", "content": str(item)} for item in contents]
                    else:
                        messages = [{"role": "user", "content": str(contents)}]

                    if kwargs.get("generation_config", {}).get("response_mime_type") == "application/json":
                        json_mode = True

                    res_text = call_openai_compatible_api(key, self.model_name, messages, json_mode=json_mode)
                    return UnifiedResponse(res_text)
                except Exception as ds_err:
                    last_error = ds_err
                    err_str = str(ds_err)
                    logger.error(f"Error con proveedor DeepSeek en clave #{idx+1}: {err_str}")
                    if is_quota_error(err_str):
                        has_any_quota_err = True
                        quota_err_str = err_str
                    continue

            try:
                genai.configure(api_key=key)
                m = genai.GenerativeModel(self.model_name if not self.model_name.startswith("deepseek") else "gemini-2.5-flash")
                return m.generate_content(contents, **kwargs)
            except Exception as e:
                last_error = e
                err_str = str(e)
                err_lower = err_str.lower()
                logger.warning(f"Intento {idx + 1} con modelo '{self.model_name}' falló: {e}")

                if is_quota_error(err_str):
                    if "pro" in self.model_name.lower():
                        try:
                            logger.info("Modelo Pro sin cuota en plan gratuito, intentando fallback a gemini-2.5-flash")
                            m_fb = genai.GenerativeModel("gemini-2.5-flash")
                            return m_fb.generate_content(contents, **kwargs)
                        except Exception as sub_e:
                            last_error = sub_e
                            err_str = str(sub_e)

                    has_any_quota_err = True
                    quota_err_str = err_str
                    continue

                # Si es error de modelo no encontrado/no soportado, fallback a otros modelos disponibles
                if ("not found" in err_lower or "404" in err_lower or "unsupported" in err_lower or "no longer available" in err_lower):
                    for fb_model in _get_fallback_candidates(self.model_name):
                        try:
                            logger.info(f"Modelo '{self.model_name}' no disponible (404), intentando con '{fb_model}'")
                            m_fallback = genai.GenerativeModel(fb_model)
                            return m_fallback.generate_content(contents, **kwargs)
                        except Exception as sub_e:
                            sub_err_str = str(sub_e)
                            last_error = sub_e
                            if is_quota_error(sub_err_str):
                                has_any_quota_err = True
                                quota_err_str = sub_err_str

        # Detectar error universal de cuota / rate limit / 429
        err_msg = str(last_error)
        if has_any_quota_err or is_quota_error(err_msg):
            final_quota_msg = quota_err_str or err_msg
            raise HTTPException(
                status_code=429,
                detail=f"⚠️ Límite de Cuota Alcanzado (429/Quota Exceeded): {final_quota_msg}. Ingresa una clave de resguardo o cambia el modelo en la interfaz."
            )

        if "401" in err_msg or "invalid" in err_msg.lower() or "api_key" in err_msg.lower():
            raise HTTPException(
                status_code=401,
                detail=f"⚠️ API Key no válida (401): {err_msg}"
            )

        raise HTTPException(
            status_code=500,
            detail=f"Error en el servicio de IA: {err_msg}"
        )

    def start_chat(self, history=None, **kwargs):
        keys_to_try = [k for k in [self.primary_key, self.fallback_key] if k]
        if not keys_to_try:
            keys_to_try = [k for k in [os.environ.get("GEMINI_API_KEY", "").strip(), os.environ.get("GEMINI_FALLBACK_API_KEY", "").strip()] if k]

        if not keys_to_try:
            raise HTTPException(
                status_code=401, 
                detail="Falta la API Key. Configúrala en la interfaz web."
            )

        last_error = None
        has_any_quota_err = False
        quota_err_str = ""

        for idx, key in enumerate(keys_to_try):
            if is_deepseek_key_or_model(key, self.model_name):
                try:
                    logger.info(f"Iniciando chat con proveedor DeepSeek ({self.model_name})")
                    return DeepSeekChatSessionWrapper(key, self.model_name, history=history)
                except Exception as ds_err:
                    last_error = ds_err
                    err_str = str(ds_err)
                    logger.error(f"Error iniciando chat con DeepSeek en clave #{idx+1}: {err_str}")
                    if is_quota_error(err_str):
                        has_any_quota_err = True
                        quota_err_str = err_str
                    continue

            try:
                genai.configure(api_key=key)
                m = genai.GenerativeModel(self.model_name)
                return GeminiChatSessionWrapper(m, history=history, model_wrapper=self, key_used=key, **kwargs)
            except Exception as e:
                last_error = e
                err_str = str(e)
                err_lower = err_str.lower()
                logger.warning(f"start_chat intento {idx + 1} con modelo '{self.model_name}' falló: {e}")

                if is_quota_error(err_str):
                    if "pro" in self.model_name.lower():
                        try:
                            logger.info("Modelo Pro sin cuota en plan gratuito para start_chat, intentando fallback a gemini-2.5-flash")
                            m_fb = genai.GenerativeModel("gemini-2.5-flash")
                            return GeminiChatSessionWrapper(m_fb, history=history, model_wrapper=self, key_used=key, **kwargs)
                        except Exception as sub_e:
                            last_error = sub_e
                            err_str = str(sub_e)

                    has_any_quota_err = True
                    quota_err_str = err_str
                    continue

                if ("not found" in err_lower or "404" in err_lower or "unsupported" in err_lower or "no longer available" in err_lower):
                    for fb_model in _get_fallback_candidates(self.model_name):
                        try:
                            logger.info(f"Modelo '{self.model_name}' no soportado en la clave, intentando start_chat con '{fb_model}'")
                            m_fallback = genai.GenerativeModel(fb_model)
                            return GeminiChatSessionWrapper(m_fallback, history=history, model_wrapper=self, key_used=key, **kwargs)
                        except Exception as sub_e:
                            sub_err_str = str(sub_e)
                            last_error = sub_e
                            if is_quota_error(sub_err_str):
                                has_any_quota_err = True
                                quota_err_str = sub_err_str

        err_msg = str(last_error)
        if has_any_quota_err or is_quota_error(err_msg):
            final_quota_msg = quota_err_str or err_msg
            raise HTTPException(
                status_code=429,
                detail=f"⚠️ Límite de Cuota Alcanzado (429/Quota Exceeded): {final_quota_msg}. Ingresa una clave de resguardo o cambia el modelo en la interfaz."
            )

        if "401" in err_msg or "invalid" in err_msg.lower() or "api_key" in err_msg.lower():
            raise HTTPException(
                status_code=401,
                detail=f"⚠️ API Key no válida (401): {err_msg}"
            )

        raise HTTPException(
            status_code=500,
            detail=f"Error en el servicio de IA: {err_msg}"
        )

# Helper para obtener el modelo Gemini wrapper
def get_gemini_model(
    api_key: Optional[str] = None,
    fallback_key: Optional[str] = None,
    model_name: Optional[str] = None
) -> GeminiModelWrapper:
    primary = (api_key or "").strip() or os.environ.get("GEMINI_API_KEY", "").strip()
    sec = (fallback_key or "").strip() or os.environ.get("GEMINI_FALLBACK_API_KEY", "").strip()
    m_name = (model_name or "").strip() or os.environ.get("GEMINI_MODEL", "gemini-2.5-flash").strip()

    return GeminiModelWrapper(primary_key=primary, fallback_key=sec, model_name=m_name)

# Servir archivos estáticos del frontend
static_dir = os.path.join(os.path.dirname(__file__), "static")
if not os.path.exists(static_dir):
    os.makedirs(static_dir)

# Endpoints de la API

# Estado global del progreso de generación de especificaciones
GENERATION_STATUS: Dict[str, Any] = {
    "is_generating": False,
    "total_files": 17,
    "current_index": 0,
    "current_filename": "",
    "completed_files": [],
    "percent": 0
}

@app.get("/api/config")
async def get_config():
    has_key = bool(os.environ.get("GEMINI_API_KEY"))
    has_fallback = bool(os.environ.get("GEMINI_FALLBACK_API_KEY"))
    current_model = os.environ.get("GEMINI_MODEL", "gemini-2.5-flash")
    if current_model in ["gemini-2.5-pro", "gemini-1.5-pro"]:
        current_model = "gemini-3.1-pro-preview"
    elif current_model == "gemini-1.5-flash":
        current_model = "gemini-2.5-flash"
    return {
        "hasApiKey": has_key,
        "hasFallbackKey": has_fallback,
        "currentModel": current_model,
        "availableModels": [
            {"id": "gemini-3.1-pro-preview", "name": "🧠 Gemini 3.1 Pro (Máxima Potencia)", "badge": "Pro"},
            {"id": "gemini-2.5-flash", "name": "⚡ Gemini 2.5 Flash (Ultra Rápido - Recomendado)", "badge": "Flash"},
            {"id": "gemini-2.0-flash", "name": "⚡ Gemini 2.0 Flash (Alta Disponibilidad)", "badge": "Flash"},
            {"id": "gemini-flash-latest", "name": "⚡ Gemini Flash (Última Versión)", "badge": "Flash"},
            {"id": "deepseek-chat", "name": "🐳 DeepSeek V3 (deepseek-chat)", "badge": "DeepSeek"},
            {"id": "deepseek-reasoner", "name": "🐳 DeepSeek R1 (deepseek-reasoner)", "badge": "DeepSeek"}
        ]
    }

@app.get("/api/generation-status")
async def get_generation_status():
    global GENERATION_STATUS
    specs_dir = get_specs_dir()
    disk_completed = []
    
    files_to_generate = [
        "project.md", "product.md", "requirements.md", "user-stories.md",
        "architecture.md", "database.md", "api.md", "openapi.json", "frontend.md",
        "backend.md", "security.md", "integrations.md", "roadmap.md",
        "tasks.md", "decisions.md", "glossary.md", "agents.md"
    ]
    
    if os.path.exists(specs_dir):
        for f in files_to_generate:
            fp = os.path.join(specs_dir, f)
            if os.path.exists(fp) and os.path.getsize(fp) > 0:
                disk_completed.append(f)
                
    total = len(files_to_generate)
    completed_count = len(disk_completed)
    percent = int((completed_count / total) * 100) if total > 0 else 0
    
    is_generating = GENERATION_STATUS.get("is_generating", False)
    if completed_count == total:
        is_generating = False
        
    return {
        "is_generating": is_generating,
        "total_files": total,
        "current_index": completed_count,
        "current_filename": GENERATION_STATUS.get("current_filename", ""),
        "completed_files": disk_completed,
        "percent": percent
    }

@app.post("/api/cancel-generation")
def cancel_generation():
    global GENERATION_STATUS
    GENERATION_STATUS["cancel_requested"] = True
    GENERATION_STATUS["is_generating"] = False
    logger.info("Solicitud de cancelación de generación de especificaciones recibida.")
    return {"status": "success", "message": "Generación cancelada."}

@app.get("/api/project-path")
async def get_project_path():
    current_path = get_target_project_path()
    return {
        "status": "success",
        "project_path": current_path,
        "project_name": os.path.basename(current_path) or current_path
    }

@app.post("/api/set-project-path")
async def set_project_path_endpoint(req: SetProjectPathRequest):
    try:
        new_path = set_target_project_path(req.project_path)
        return {
            "status": "success",
            "message": f"Ruta del proyecto configurada en: {new_path}",
            "project_path": new_path,
            "project_name": os.path.basename(new_path) or new_path
        }
    except Exception as e:
        logger.error(f"Error al establecer ruta del proyecto: {str(e)}")
        raise HTTPException(status_code=400, detail=f"Ruta inválida: {str(e)}")

@app.get("/api/recent-projects")
async def get_recent_projects():
    try:
        projects = project_manager.list_projects()
        current_active = get_target_project_path()
        return {"status": "success", "projects": projects, "active_path": current_active}
    except Exception as e:
        logger.error(f"Error en get_recent_projects: {str(e)}")
        return {"status": "error", "projects": [], "active_path": get_target_project_path()}

@app.post("/api/delete-project")
async def delete_project_endpoint(req: DeleteProjectRequest):
    try:
        res = project_manager.delete_project(req.project_path, req.delete_files)
        active_path = get_target_project_path()
        if active_path == os.path.abspath(req.project_path):
            all_projs = project_manager.list_projects()
            new_active = all_projs[0]["path"] if all_projs else ROOT_DIR
            set_target_project_path(new_active)

        return {
            "status": "success",
            "message": res.get("message", "Proyecto eliminado"),
            "projects": project_manager.list_projects()
        }
    except Exception as e:
        logger.error(f"Error en delete_project_endpoint: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/select-folder-dialog")
async def select_folder_dialog():
    import subprocess
    import asyncio

    def _open_dialog():
        # 1. Intentar con zenity
        try:
            result = subprocess.run(
                ["zenity", "--file-selection", "--directory", "--title=Selecciona la carpeta destino para el Proyecto Spec-First"],
                capture_output=True, text=True, timeout=300
            )
            if result.returncode == 0 and result.stdout.strip():
                return {"status": "success", "selected_path": result.stdout.strip()}
            elif result.returncode != 0:
                return {"status": "cancelled", "message": "Selección de carpeta cancelada por el usuario."}
        except subprocess.TimeoutExpired:
            logger.warning("Diálogo zenity excedió tiempo de espera")
            return {"status": "cancelled", "message": "Tiempo de espera agotado al seleccionar carpeta."}
        except Exception as e:
            logger.warning(f"No se pudo usar zenity: {str(e)}")

        # 2. Fallback: intentar con kdialog
        try:
            result = subprocess.run(
                ["kdialog", "--getexistingdirectory", os.path.expanduser("~"), "--title", "Selecciona la carpeta destino"],
                capture_output=True, text=True, timeout=300
            )
            if result.returncode == 0 and result.stdout.strip():
                return {"status": "success", "selected_path": result.stdout.strip()}
            elif result.returncode != 0:
                return {"status": "cancelled", "message": "Selección de carpeta cancelada por el usuario."}
        except Exception as e:
            logger.warning(f"No se pudo usar kdialog: {str(e)}")

        return {
            "status": "manual_required",
            "message": "Escribe directamente la ruta de la carpeta en el campo de texto.",
            "current_path": get_target_project_path()
        }

    res = await asyncio.to_thread(_open_dialog)
    if res.get("status") == "success":
        set_target_project_path(res["selected_path"])
        res["project_name"] = os.path.basename(res["selected_path"]) or res["selected_path"]
    return res

@app.post("/api/analyze-idea")
def analyze_idea(req: IdeaAnalysisRequest, x_gemini_key: Optional[str] = Header(None), x_gemini_fallback_key: Optional[str] = Header(None), x_gemini_model: Optional[str] = Header(None)):
    model = get_gemini_model(x_gemini_key, x_gemini_fallback_key, x_gemini_model)
    
    local_docs = get_local_project_docs_summary()
    
    prompt = f"""
    Eres un Staff Software Architect y Product Designer.
    Analiza la siguiente idea de software y extrae información clave estructurada en formato JSON válido.
    
    Idea del usuario: "{req.idea}"
    {local_docs}
    
    Debes devolver ÚNICAMENTE un objeto JSON con las siguientes claves (no uses markdown, no incluyas texto antes o después del JSON):
    {{
        "domain": "Dominio principal del producto (ej: E-commerce, EdTech, FinTech, Audio/Voice, Developer Tool, Mobile IME)",
        "productType": "Tipo de producto (ej: Web SPA, SaaS, Mobile App, Chrome Extension, CLI Tool)",
        "actors": ["Actor 1", "Actor 2"],
        "detectedFeatures": ["Funcionalidad 1", "Funcionalidad 2"],
        "risks": ["Riesgo 1", "Riesgo 2"],
        "uncertainties": ["Incertidumbre 1", "Incertidumbre 2"],
        "questions": [
            {{
                "id": "q_domain_specific_1",
                "section": "Arquitectura / Dominio",
                "label": "Pregunta técnica o de negocio profundamente relevante y específica para esta idea de software (EVITA preguntas genéricas sobre auth o DB a menos que la idea sea un sistema multiusuario o web app).",
                "type": "select",
                "options": ["Opción 1 adaptada al contexto", "Opción 2 adaptada al contexto", "Opción 3"]
            }},
            {{
                "id": "q_domain_specific_2",
                "section": "Rendimiento / Privacidad / UX",
                "label": "Pregunta específica sobre integraciones clave, latencia, privacidad o experiencia del usuario para este software.",
                "type": "select",
                "options": ["Opción A", "Opción B", "Opción C"]
            }},
            {{
                "id": "q_features_core",
                "section": "Producto",
                "label": "Describe las funcionalidades más críticas que debe tener el MVP:",
                "type": "text"
            }}
        ]
    }}
    """
    
    try:
        response = model.generate_content(
            prompt,
            generation_config={"response_mime_type": "application/json"}
        )
        data = json.loads(response.text)
        return data
    except Exception as e:
        logger.error(f"Error al analizar la idea: {str(e)}")
        # Fallback local simulado en caso de error o límite de cuota
        return {
            "domain": "Por definir",
            "productType": "Web App",
            "actors": ["Usuario final", "Administrador"],
            "detectedFeatures": ["Inicio de sesión", "Gestión básica"],
            "risks": ["Especificación incompleta"],
            "uncertainties": ["Falta definir arquitectura"],
            "questions": [
                {
                    "id": "q_fallback_1",
                    "section": "General",
                    "label": "Hubo un problema al contactar a la IA. Ingresa el objetivo principal de la app:",
                    "type": "text"
                }
            ]
        }

@app.post("/api/next-questions")
def next_questions(req: NextQuestionsRequest, x_gemini_key: Optional[str] = Header(None), x_gemini_fallback_key: Optional[str] = Header(None), x_gemini_model: Optional[str] = Header(None)):
    model = get_gemini_model(x_gemini_key, x_gemini_fallback_key, x_gemini_model)
    
    prompt = f"""
    Eres un Tech Lead e Ingeniero de Requisitos.
    Analiza la idea del proyecto y las respuestas dadas hasta el momento, y genera entre 2 y 3 preguntas de profundización estrictamente relevantes para los aspectos técnicos pendientes de este proyecto (asegurando un total acumulado máximo de 5 a 6 preguntas en todo el flujo).
    
    Idea del proyecto: "{req.idea}"
    Respuestas actuales: {json.dumps(req.answers, ensure_ascii=False)}
    
    Reglas:
    - NO repitas temas ya aclarados en las respuestas actuales.
    - Las preguntas deben ser condicionales al contexto real de este software.
    
    Devuelve ÚNICAMENTE un objeto JSON con la siguiente estructura (sin markdown, solo el JSON):
    {{
        "questions": [
            {{
                "id": "id_pregunta_unica",
                "section": "Nombre de la sección (ej. API, Rendimiento, Seguridad, Calidad)",
                "label": "Texto de la pregunta",
                "type": "text | select | boolean",
                "options": ["Opción 1", "Opción 2"] // Solo si el tipo es select
            }}
        ]
    }}
    """
    
    try:
        response = model.generate_content(
            prompt,
            generation_config={"response_mime_type": "application/json"}
        )
        return json.loads(response.text)
    except Exception as e:
        logger.error(f"Error en next-questions: {str(e)}")
        return {"questions": []}

@app.post("/api/generate-diagram")
def generate_diagram(req: DiagramRequest, x_gemini_key: Optional[str] = Header(None), x_gemini_fallback_key: Optional[str] = Header(None), x_gemini_model: Optional[str] = Header(None)):
    model = get_gemini_model(x_gemini_key, x_gemini_fallback_key, x_gemini_model)
    
    prompt = f"""
    Eres un Arquitecto de Software experto.
    Genera un diagrama en formato Mermaid.js para el tipo de diagrama '{req.diagram_type}'.
    
    Respuestas del proyecto: {json.dumps(req.answers, ensure_ascii=False)}
    
    Tipos de diagramas esperados:
    - 'er': Diagrama de Entidad Relación (erDiagram) con entidades principales, atributos y relaciones.
    - 'flow': Diagrama de Flujo del caso de uso principal (graph TD/LR).
    - 'architecture': Diagrama conceptual de arquitectura e infraestructura (servicios, cliente, base de datos).
    
    Instrucciones críticas:
    1. Devuelve únicamente el código de Mermaid listo para ser renderizado.
    2. No encierres el código en bloques de código markdown (como ```mermaid). Solo devuelve el texto del código de Mermaid directamente.
    3. Asegúrate de usar sintaxis correcta de Mermaid.
    """
    
    try:
        response = model.generate_content(prompt)
        # Limpiar posibles bloques markdown si la IA no siguió la regla estricta
        code = response.text.strip()
        if code.startswith("```"):
            lines = code.split("\n")
            if lines[0].startswith("```mermaid") or lines[0].startswith("```"):
                lines = lines[1:]
            if lines[-1].strip() == "```":
                lines = lines[:-1]
            code = "\n".join(lines).strip()
        return {"code": code}
    except Exception as e:
        logger.error(f"Error generando diagrama Mermaid: {str(e)}")
        return {"code": "graph TD\n  A[Error al generar el diagrama] --> B[Verifica tu API Key]"}

@app.post("/api/check-consistency")
def check_consistency(req: SaveProjectRequest, x_gemini_key: Optional[str] = Header(None), x_gemini_fallback_key: Optional[str] = Header(None), x_gemini_model: Optional[str] = Header(None)):
    model = get_gemini_model(x_gemini_key, x_gemini_fallback_key, x_gemini_model)
    
    prompt = f"""
    Eres un QA Lead y Arquitecto de Software.
    Evalúa la consistencia de las respuestas y decisiones de la especificación técnica de este proyecto.
    
    Datos del proyecto: {json.dumps(req.project_data, ensure_ascii=False)}
    
    Busca contradicciones, inconsistencias de seguridad, arquitectura o requisitos funcionales faltantes.
    Por ejemplo, si la base de datos es NoSQL pero se habla de joins complejos, o si hay pagos pero no se especifica HTTPS/seguridad.
    
    Devuelve ÚNICAMENTE una lista de advertencias en formato JSON (sin markdown):
    {{
        "warnings": [
            {{
                "severity": "critical | warning | info",
                "section": "Sección afectada (ej: Seguridad, Base de datos)",
                "message": "Descripción detallada de la inconsistencia",
                "suggestion": "Cómo solucionarlo o qué preguntar para resolverlo"
            }}
        ]
    }}
    """
    try:
        response = model.generate_content(
            prompt,
            generation_config={"response_mime_type": "application/json"}
        )
        return json.loads(response.text)
    except Exception as e:
        logger.error(f"Error evaluando consistencia: {str(e)}")
        return {"warnings": [{"severity": "info", "section": "Sistema", "message": "No se pudo realizar el análisis automático de consistencia.", "suggestion": "Inténtalo de nuevo más tarde."}]}

@app.post("/api/save-project")
async def save_project(req: SaveProjectRequest):
    project_data = req.project_data
    try:
        # 1. Guardar el estado general del proyecto en project.json de la carpeta destino
        project_file = get_project_file()
        specs_dir = get_specs_dir()
        os.makedirs(os.path.dirname(project_file), exist_ok=True)
        with open(project_file, "w", encoding="utf-8") as f:
            json.dump(project_data, f, ensure_ascii=False, indent=2)
            
        # 2. Sincronizar hacia los archivos individuales en el disco (specs/ y features/)
        spec_modules = project_data.get("specModules", {})
        if os.path.exists(specs_dir):
            for name_key, content in spec_modules.items():
                if not content:
                    continue
                # Si es una feature dinámica (ej. features/auth/login)
                if name_key.startswith("features/"):
                    filepath = os.path.join(specs_dir, f"{name_key}.md")
                else:
                    # Guardamos openapi como .json y el resto como .md
                    ext = ".json" if name_key == "openapi" else ".md"
                    filepath = os.path.join(specs_dir, f"{name_key}{ext}")
                
                # Asegurar que existan los directorios
                os.makedirs(os.path.dirname(filepath), exist_ok=True)
                try:
                    with open(filepath, "w", encoding="utf-8") as file_obj:
                        file_obj.write(content.strip())
                except Exception as file_err:
                    logger.error(f"Error escribiendo archivo individual {name_key} en save_project: {str(file_err)}")
                    
        register_recent_project(get_target_project_path())
        return {"status": "success", "message": "Proyecto y archivos físicos guardados localmente"}
    except Exception as e:
        logger.error(f"Error al guardar proyecto: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

def parse_feature_metadata_from_file(filepath: str, folder: str, feat_id: str) -> dict:
    name = feat_id.replace("-", " ").title()
    description = f"Especificación para {name}."
    try:
        if os.path.exists(filepath):
            with open(filepath, "r", encoding="utf-8") as f:
                content = f.read()
                lines = content.split("\n")
                
                # Buscar el primer título # o ##
                found_name = False
                for line in lines:
                    line_strip = line.strip()
                    if line_strip.startswith("#"):
                        raw_name = line_strip.lstrip("#").strip()
                        if ":" in raw_name:
                            parts = raw_name.split(":", 1)
                            raw_name = parts[1].strip()
                        if raw_name:
                            name = raw_name
                            found_name = True
                            break
                            
                # Buscar el primer párrafo no vacío para la descripción
                found_title = False
                for line in lines:
                    line_strip = line.strip()
                    if line_strip.startswith("#"):
                        found_title = True
                        continue
                    if found_title and line_strip:
                        if not line_strip.startswith("#") and not line_strip.startswith(">"):
                            description = line_strip
                            if len(description) > 120:
                                description = description[:117] + "..."
                            break
    except Exception as e:
        logger.error(f"Error parsing feature file metadata: {str(e)}")
    return {
        "id": feat_id,
        "name": name,
        "description": description,
        "folder": folder
    }

@app.get("/api/load-project")
async def load_project():
    try:
        project_file = get_project_file()
        specs_dir = get_specs_dir()
        
        project_data = None
        if os.path.exists(project_file):
            try:
                with open(project_file, "r", encoding="utf-8") as f:
                    project_data = json.load(f)
            except Exception as e:
                logger.error(f"Error leyendo project.json: {str(e)}")

        if not project_data:
            if os.path.exists(specs_dir):
                folder_name = os.path.basename(get_target_project_path())
                project_data = {
                    "id": "proj_" + str(int(os.path.getmtime(specs_dir))),
                    "name": folder_name.replace("-", " ").replace("_", " ").title(),
                    "seedIdea": f"Proyecto {folder_name}",
                    "createdAt": int(os.path.getmtime(specs_dir) * 1000),
                    "updatedAt": int(os.path.getmtime(specs_dir) * 1000),
                    "answers": {},
                    "specModules": {},
                    "featuresList": []
                }
            else:
                return {"status": "empty", "project": None}

        disk_features = []
        disk_modules = {}
            
        if os.path.exists(specs_dir):
            for filename in os.listdir(specs_dir):
                filepath = os.path.join(specs_dir, filename)
                if os.path.isfile(filepath):
                    name_key = filename.replace(".md", "").replace(".json", "")
                    try:
                        with open(filepath, "r", encoding="utf-8") as file_obj:
                            disk_modules[name_key] = file_obj.read().strip()
                    except Exception as e:
                        logger.error(f"Error leyendo archivo en load_project: {str(e)}")
            
        # Reemplazar specModules estrictamente por lo que existe actualmente en el disco
        project_data["specModules"] = disk_modules
            
        # Sincronizar también para las features dinámicas
        features_dir = os.path.join(specs_dir, "features")
        if os.path.exists(features_dir):
            for folder in os.listdir(features_dir):
                folder_path = os.path.join(features_dir, folder)
                if os.path.isdir(folder_path):
                    for feat_file in os.listdir(folder_path):
                        if feat_file.endswith(".md"):
                            feat_id = feat_file.replace(".md", "")
                            feat_path = os.path.join(folder_path, feat_file)
                            if os.path.isfile(feat_path):
                                name_key = f"features/{folder}/{feat_id}"
                                try:
                                    with open(feat_path, "r", encoding="utf-8") as file_obj:
                                        project_data["specModules"][name_key] = file_obj.read().strip()
                                    
                                    # Parsear metadatos e insertar en la lista
                                    feat_metadata = parse_feature_metadata_from_file(feat_path, folder, feat_id)
                                    disk_features.append(feat_metadata)
                                except Exception as e:
                                    logger.error(f"Error leyendo feature en load_project: {str(e)}")
                                    
        # Actualizar la lista en project_data si encontramos features en el disco
        if disk_features:
            project_data["featuresList"] = disk_features
        else:
            project_data["featuresList"] = []

        # Guardar la versión sincronizada de project_data en project.json
        try:
            with open(project_file, "w", encoding="utf-8") as pf:
                json.dump(project_data, pf, ensure_ascii=False, indent=2)
        except Exception as p_err:
            logger.error(f"Error guardando project_data sincronizado: {str(p_err)}")
                                     
        return {"status": "success", "project": project_data}
    except Exception as e:
        logger.error(f"Error al cargar el proyecto: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

def clean_markdown(text: str) -> str:
    text = text.strip()
    if text.startswith("```"):
        lines = text.split("\n")
        if lines[0].startswith("```markdown") or lines[0].startswith("```"):
            lines = lines[1:]
        if lines[-1].strip() == "```":
            lines = lines[:-1]
        text = "\n".join(lines).strip()
    return text

def get_local_project_docs_summary() -> str:
    """Escanea el directorio del proyecto en busca de documentos locales (.txt, .md, .doc, docs/) para enriquecer el contexto de la IA."""
    project_dir = get_target_project_path()
    if not os.path.exists(project_dir):
        return ""
    
    docs_content = []
    ignored_dirs = {".git", ".venv", "node_modules", "specs", "__pycache__", "dist", "build"}
    ignored_files = {"chat_history.json", "project.json", ".active_project.json", ".recent_projects.json"}
    valid_exts = (".md", ".txt", ".json", ".rst", ".yaml", ".yml")
    
    try:
        for root, dirs, files in os.walk(project_dir):
            dirs[:] = [d for d in dirs if d not in ignored_dirs]
            for file in files:
                if file in ignored_files or file.startswith("."):
                    continue
                if file.lower().endswith(valid_exts):
                    rel_path = os.path.relpath(os.path.join(root, file), project_dir)
                    full_path = os.path.join(root, file)
                    if os.path.getsize(full_path) < 200000:
                        try:
                            with open(full_path, "r", encoding="utf-8", errors="ignore") as f:
                                text = f.read(4000)
                                if text.strip():
                                    docs_content.append(f"--- Documento local ({rel_path}) ---\n{text}")
                        except Exception:
                            pass
    except Exception as e:
        logger.error(f"Error escaneando documentos del proyecto: {str(e)}")
        
    if docs_content:
        return "\n\nDOCUMENTOS LOCALES ENCONTRADOS EN EL PROYECTO:\n" + "\n".join(docs_content[:5])
    return ""

@app.post("/api/export-specs")
def export_specs(req: SaveProjectRequest, x_gemini_key: Optional[str] = Header(None), x_gemini_fallback_key: Optional[str] = Header(None), x_gemini_model: Optional[str] = Header(None)):
    global GENERATION_STATUS
    model = get_gemini_model(x_gemini_key, x_gemini_fallback_key, x_gemini_model)
    specs_dir = get_specs_dir()
    project_file = get_project_file()
    
    # Creamos la carpeta de specs si no existe
    if not os.path.exists(specs_dir):
        os.makedirs(specs_dir, exist_ok=True)
        
    project = req.project_data
    if "specModules" not in project:
        project["specModules"] = {}
        
    force_regenerate = getattr(req, "force_regenerate", False)

    # Cargar historial de chat y documentos locales si existen para enriquecer el contexto de la IA
    chat_history_summary = ""
    history_file = os.path.join(get_target_project_path(), "chat_history.json")
    if os.path.exists(history_file):
        try:
            with open(history_file, "r", encoding="utf-8") as hf:
                history_data = json.load(hf)
                chat_summary_items = []
                for msg in history_data[-15:]:
                    role = msg.get("role", "user")
                    content = msg.get("content", "")[:300]
                    chat_summary_items.append(f"[{role}]: {content}")
                chat_history_summary = "\n".join(chat_summary_items)
        except Exception as err:
            logger.error(f"Error leyendo chat_history.json en export_specs: {str(err)}")
            
    local_docs_summary = get_local_project_docs_summary()
    if local_docs_summary:
        chat_history_summary += f"\n\n{local_docs_summary}"
            
    answers = project.get("answers", {})
    metadata = project.get("metadata", {})
    idea = project.get("seedIdea", "")
    
    # Definimos la lista de archivos a generar
    files_to_generate = [
        "project.md", "product.md", "requirements.md", "user-stories.md",
        "architecture.md", "database.md", "api.md", "openapi.json", "frontend.md",
        "backend.md", "security.md", "integrations.md", "roadmap.md",
        "tasks.md", "decisions.md", "glossary.md", "agents.md"
    ]
    
    GENERATION_STATUS = {
        "is_generating": True,
        "total_files": len(files_to_generate),
        "current_index": 0,
        "current_filename": "product.md",
        "completed_files": [],
        "percent": 0
    }

    generated_files = []
    ai_markdowns = {}
    
    def save_single_spec(fname: str, raw_content: str):
        cleaned = clean_markdown(raw_content)
        ai_markdowns[fname] = cleaned
        filepath = os.path.join(specs_dir, fname)
        try:
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(cleaned.strip())
            if fname not in generated_files:
                generated_files.append(fname)
            project["specModules"][fname.replace(".md", "").replace(".json", "")] = cleaned.strip()
            
            if fname not in GENERATION_STATUS["completed_files"]:
                GENERATION_STATUS["completed_files"].append(fname)
            
            GENERATION_STATUS["current_index"] = len(GENERATION_STATUS["completed_files"])
            GENERATION_STATUS["current_filename"] = fname
            GENERATION_STATUS["percent"] = int((len(GENERATION_STATUS["completed_files"]) / GENERATION_STATUS["total_files"]) * 100)
            logger.info(f"Guardado inmediato en disco: {filepath}")
        except Exception as err:
            logger.error(f"Error escribiendo {fname} en disco: {str(err)}")

    def check_cancel():
        if GENERATION_STATUS.get("cancel_requested", False):
            logger.info("Generación de especificaciones abortada por cancelación del usuario.")
            GENERATION_STATUS["is_generating"] = False
            return True
        return False

    # 1. Generar product.md
    if check_cancel():
        return {"status": "cancelled", "detail": "Generación cancelada por el usuario."}
    try:
        GENERATION_STATUS["current_filename"] = "product.md"
        filepath = os.path.join(specs_dir, "product.md")
        if not force_regenerate and os.path.exists(filepath) and os.path.getsize(filepath) > 100:
            logger.info("product.md ya existe en disco, reutilizando contenido existente.")
            with open(filepath, "r", encoding="utf-8") as f:
                save_single_spec("product.md", f.read())
        else:
            prod_prompt = f"""
            Eres un Staff Software Architect y Product Designer.
            Genera el contenido completo en formato Markdown para el archivo 'product.md'.
            Debe incluir:
            1. Visión General del Producto y Propuesta de Valor.
            2. Objetivos de Negocio y Métricas de Éxito.
            3. Usuarios, Actores y sus Roles detallados.
            4. Reglas de Negocio Críticas e Inquebrantables.
            5. Casos de Uso principales e Historias clave.
            6. DIAGRAMA MERMAID OBLIGATORIO: Incluye al menos un diagrama de flujo o mapa visual de navegación del usuario en sintaxis Mermaid.js (```mermaid graph TD ... ```).
            
            Basándote en la idea del proyecto: "{idea}"
            Respuestas recopiladas: {json.dumps(answers, ensure_ascii=False)}
            Metadatos: {json.dumps(metadata, ensure_ascii=False)}
            Conversación previa en el chat:
            {chat_history_summary}
            
            Devuelve únicamente el contenido Markdown listo para ser guardado. No utilices bloques ```markdown para envolver tu respuesta.
            """
            logger.info("Generando product.md por IA...")
            resp = model.generate_content(prod_prompt)
            save_single_spec("product.md", resp.text)
    except Exception as e:
        logger.error(f"Error generando product.md por IA: {str(e)}")

    # 2. architecture.md
    if check_cancel():
        return {"status": "cancelled", "detail": "Generación cancelada por el usuario."}
    try:
        GENERATION_STATUS["current_filename"] = "architecture.md"
        filepath = os.path.join(specs_dir, "architecture.md")
        if os.path.exists(filepath) and os.path.getsize(filepath) > 100:
            logger.info("architecture.md ya existe en disco, reutilizando contenido existente.")
            with open(filepath, "r", encoding="utf-8") as f:
                save_single_spec("architecture.md", f.read())
        else:
            arch_prompt = f"""
            Eres un Arquitecto de Software experto.
            Genera el contenido completo en formato Markdown para el archivo 'architecture.md'.
            Debe incluir:
            1. Pila Tecnológica Propuesta (Frontend, Backend, Base de Datos, Servidor) y su justificación.
            2. Decisiones de Diseño Clave e Infraestructura (Conceptos de despliegue).
            3. Estructura de Módulos del Sistema y Flujo de Datos.
            4. DIAGRAMA MERMAID OBLIGATORIO: Incluye un diagrama conceptual completo de la arquitectura del sistema y flujo de componentes en sintaxis Mermaid.js (bloque ```mermaid graph TD ... ```). Queda estrictamente prohibido usar gráficos en texto ASCII plano.
            
            Basándote en la idea del proyecto: "{idea}"
            y las respuestas recopiladas: {json.dumps(answers, ensure_ascii=False)}
            y metadatos: {json.dumps(metadata, ensure_ascii=False)}
            
            Devuelve únicamente el contenido Markdown listo para ser guardado. No utilices bloques de código Markdown (como ```markdown) para envolver tu respuesta.
            """
            logger.info("Generando architecture.md por IA...")
            resp = model.generate_content(arch_prompt)
            save_single_spec("architecture.md", resp.text)
    except Exception as e:
        logger.error(f"Error generando architecture.md por IA: {str(e)}")

    # 3. database.md
    if check_cancel():
        return {"status": "cancelled", "detail": "Generación cancelada por el usuario."}
    try:
        GENERATION_STATUS["current_filename"] = "database.md"
        filepath = os.path.join(specs_dir, "database.md")
        if os.path.exists(filepath) and os.path.getsize(filepath) > 100:
            logger.info("database.md ya existe en disco, reutilizando contenido existente.")
            with open(filepath, "r", encoding="utf-8") as f:
                save_single_spec("database.md", f.read())
        else:
            db_prompt = f"""
            Eres un Ingeniero de Base de Datos experto.
            Genera el contenido completo en formato Markdown para el archivo 'database.md'.
            Debe incluir:
            1. Diseño Conceptual del Modelo de Datos.
            2. DIAGRAMA MERMAID OBLIGATORIO: Incluye un diagrama de Entidad-Relación completo escrito exclusivamente en sintaxis Mermaid.js (bloque ```mermaid erDiagram ... ``` con entidades, atributos principales y cardinalidad de relaciones). Queda estrictamente prohibido usar gráficos en texto ASCII plano.
            3. Listado de Entidades principales con sus atributos (tipos de datos) y relaciones.
            4. Esquema físico completo escrito en sintaxis Prisma DSL (un bloque de código schema.prisma completo y listo para copiar).
            5. Índices, restricciones o consideraciones de rendimiento.
            
            Basándote en la idea del proyecto: "{idea}"
            y las respuestas recopiladas: {json.dumps(answers, ensure_ascii=False)}
            y metadatos: {json.dumps(metadata, ensure_ascii=False)}
            
            Devuelve únicamente el contenido Markdown listo para ser guardado. No utilices bloques de código Markdown (como ```markdown) para envolver tu respuesta.
            """
            logger.info("Generando database.md por IA...")
            resp = model.generate_content(db_prompt)
            save_single_spec("database.md", resp.text)
    except Exception as e:
        logger.error(f"Error generando database.md por IA: {str(e)}")

    # 4. api.md
    if check_cancel():
        return {"status": "cancelled", "detail": "Generación cancelada por el usuario."}
    try:
        GENERATION_STATUS["current_filename"] = "api.md"
        filepath = os.path.join(specs_dir, "api.md")
        if os.path.exists(filepath) and os.path.getsize(filepath) > 100:
            logger.info("api.md ya existe en disco, reutilizando contenido existente.")
            with open(filepath, "r", encoding="utf-8") as f:
                save_single_spec("api.md", f.read())
        else:
            api_prompt = f"""
            Eres un Diseñador de APIs RESTful experto.
            Genera el contenido completo en formato Markdown para el archivo 'api.md'.
            Debe incluir:
            1. Protocolo de Comunicación, Autenticación y Manejo de Sesiones.
            2. DIAGRAMA MERMAID OBLIGATORIO: Incluye un diagrama de secuencia del flujo de peticiones/respuestas o autenticación en sintaxis Mermaid.js (bloque ```mermaid sequenceDiagram ... ```). Queda estrictamente prohibido usar gráficos en texto ASCII plano.
            3. Listado de Endpoints clave (Rutas, Métodos HTTP, Payloads de petición y respuesta esperados).
            4. Estructura de errores comunes.
            
            Basándote en la idea del proyecto: "{idea}"
            y las respuestas recopiladas: {json.dumps(answers, ensure_ascii=False)}
            y metadatos: {json.dumps(metadata, ensure_ascii=False)}
            
            Devuelve únicamente el contenido Markdown listo para ser guardado. No utilices bloques de código Markdown (como ```markdown) para envolver tu respuesta.
            """
            logger.info("Generando api.md por IA...")
            resp = model.generate_content(api_prompt)
            save_single_spec("api.md", resp.text)
    except Exception as e:
        logger.error(f"Error generando api.md por IA: {str(e)}")

    # 4b. openapi.json
    if check_cancel():
        return {"status": "cancelled", "detail": "Generación cancelada por el usuario."}
    try:
        GENERATION_STATUS["current_filename"] = "openapi.json"
        filepath = os.path.join(specs_dir, "openapi.json")
        if os.path.exists(filepath) and os.path.getsize(filepath) > 100:
            logger.info("openapi.json ya existe en disco, reutilizando contenido existente.")
            with open(filepath, "r", encoding="utf-8") as f:
                save_single_spec("openapi.json", f.read())
        else:
            api_json_prompt = f"""
            Eres un Diseñador de APIs RESTful experto.
            Genera una especificación OpenAPI 3.0 completa en formato JSON para el proyecto.
            Debe describir todos los endpoints clave (autenticación, recursos principales del dominio).
            Asegúrate de devolver ÚNICAMENTE el código JSON válido. No utilices bloques de código Markdown (como ```json) para envolver tu respuesta.
            
            Basándote en la idea del proyecto: "{idea}"
            y las respuestas recopiladas: {json.dumps(answers, ensure_ascii=False)}
            y metadatos: {json.dumps(metadata, ensure_ascii=False)}
            """
            logger.info("Generando openapi.json por IA...")
            resp = model.generate_content(api_json_prompt)
            json_content = clean_markdown(resp.text)
            try:
                json.loads(json_content)
                save_single_spec("openapi.json", json_content)
            except Exception as json_err:
                logger.error(f"El JSON generado para openapi.json no es válido: {str(json_err)}")
                default_json = json.dumps({
                    "openapi": "3.0.0",
                    "info": {
                        "title": project.get("name", "Proyecto Spec-First") + " API",
                        "version": "1.0.0",
                        "description": f"Especificación de API generada automáticamente para {idea}"
                    },
                    "paths": {}
                }, indent=2)
                save_single_spec("openapi.json", default_json)
    except Exception as e:
        logger.error(f"Error generando openapi.json por IA: {str(e)}")

    # 4c. glossary.md
    if check_cancel():
        return {"status": "cancelled", "detail": "Generación cancelada por el usuario."}
    try:
        GENERATION_STATUS["current_filename"] = "glossary.md"
        filepath = os.path.join(specs_dir, "glossary.md")
        if os.path.exists(filepath) and os.path.getsize(filepath) > 100:
            logger.info("glossary.md ya existe en disco, reutilizando contenido existente.")
            with open(filepath, "r", encoding="utf-8") as f:
                save_single_spec("glossary.md", f.read())
        else:
            glossary_prompt = f"""
            Eres un Ingeniero de Software experto.
            Genera el contenido completo en formato Markdown para el archivo 'glossary.md'.
            Debe incluir un glosario de términos del dominio del proyecto, con su traducción del Español al Inglés técnico sugerido para las variables del código, base de datos y endpoints (por ejemplo: Almacén: Warehouse, Existencias: Stock, etc.), asegurando coherencia conceptual y terminológica en todo el equipo.
            
            Basándote en la idea del proyecto: "{idea}"
            y las respuestas recopiladas: {json.dumps(answers, ensure_ascii=False)}
            y metadatos: {json.dumps(metadata, ensure_ascii=False)}
            
            Devuelve únicamente el contenido Markdown listo para ser guardado. No utilices bloques de código Markdown (como ```markdown) para envolver tu respuesta.
            """
            logger.info("Generando glossary.md por IA...")
            resp = model.generate_content(glossary_prompt)
            save_single_spec("glossary.md", resp.text)
    except Exception as e:
        logger.error(f"Error generando glossary.md por IA: {str(e)}")

    # 4d. agents.md
    if check_cancel():
        return {"status": "cancelled", "detail": "Generación cancelada por el usuario."}
    try:
        GENERATION_STATUS["current_filename"] = "agents.md"
        filepath = os.path.join(specs_dir, "agents.md")
        if os.path.exists(filepath) and os.path.getsize(filepath) > 100:
            logger.info("agents.md ya existe en disco, reutilizando contenido existente.")
            with open(filepath, "r", encoding="utf-8") as f:
                save_single_spec("agents.md", f.read())
        else:
            agents_prompt = f"""
            Eres un Staff Software Architect.
            Genera el contenido completo en formato Markdown para el archivo 'agents.md' (Instrucciones para Agentes de Código de IA).
            Debe incluir:
            1. Contexto básico de la aplicación para el agente.
            2. Estilos de codificación explícitos (ej. camelCase en TypeScript, PascalCase en clases, etc.).
            3. Reglas Técnicas de Comportamiento Crítico (ej. usar transacciones de base de datos para modificaciones financieras/inventario, usar middleware centralizado de errores, prohibir librerías no aprobadas, etc.).
            4. Indicación de que su fuente única de verdad (SSOT) son las especificaciones de esta carpeta.
            
            Basándote en la idea del proyecto: "{idea}"
            y las respuestas recopiladas: {json.dumps(answers, ensure_ascii=False)}
            y metadatos: {json.dumps(metadata, ensure_ascii=False)}
            
            Devuelve únicamente el contenido Markdown listo para ser guardado. No utilices bloques de código Markdown (como ```markdown) para envolver tu respuesta.
            """
            logger.info("Generando agents.md por IA...")
            resp = model.generate_content(agents_prompt)
            save_single_spec("agents.md", resp.text)
    except Exception as e:
        logger.error(f"Error generando agents.md por IA: {str(e)}")
        
    actors_list = [a for a in metadata.get('actors', []) if a]
    if not actors_list:
        actors_list = ['Usuario']
    primary_actor = actors_list[0]

    # Plantillas de fallback para los archivos
    for filename in files_to_generate:
        if check_cancel():
            return {"status": "cancelled", "detail": "Generación cancelada por el usuario."}
        GENERATION_STATUS["current_filename"] = filename
        content = ""
        
        # Si fue generado por la IA, lo usamos
        if filename in ai_markdowns:
            content = ai_markdowns[filename]
        else:
            # Generar contenido completo por IA si no se generó previamente
            if filename != "project.md":
                try:
                    logger.info(f"Generando {filename} por IA en export_specs...")
                    auto_prompt = f"""
                    Actúa como un Staff Software Architect de nivel mundial.
                    Redacta el contenido técnico completo en Markdown para el archivo '{filename}' de este proyecto.
                    
                    Idea semilla: "{idea}"
                    Respuestas recopiladas: {json.dumps(answers, ensure_ascii=False)}
                    Metadatos: {json.dumps(metadata, ensure_ascii=False)}
                    
                    INSTRUCCIONES DE DISEÑO:
                    1. Genera documentación técnica detallada, profesional y estructurada específica para '{filename}'.
                    2. Si es 'backend.md', detalla la arquitectura de servicios backend, componentes, APIs consumidas o expuestas, manejo de datos y diagramas de flujo.
                    3. Si es 'frontend.md', detalla componentes UI, vistas, patrones de diseño y flujo de interacción.
                    4. Si es 'security.md', detalla matrices RBAC, autenticación, protección de datos y OWASP.
                    5. Si es 'requirements.md', detalla lista completa de RF y RNF categorizados.
                    6. Si es 'user-stories.md', detalla las historias de usuario con criterios de aceptación (Dado/Cuando/Entonces).
                    7. Si es 'integrations.md', detalla servicios externos, APIs y webhooks.
                    8. Si es 'roadmap.md', detalla las fases MVP, V1 y V2.
                    9. Si es 'tasks.md', detalla la lista estructurada de tareas TODO de desarrollo.
                    10. Si es 'decisions.md', detalla los Registros de Decisiones de Arquitectura (ADR).
                    11. DIAGRAMAS MERMAID OBLIGATORIOS: Si incluyes diagramas, DEBES generarlos SIEMPRE en bloques de código Mermaid.js (```mermaid ... ```).
                    
                    Devuelve únicamente el contenido Markdown listo para ser guardado. No uses bloques de código ```markdown para envolver todo el archivo.
                    """
                    resp = model.generate_content(auto_prompt)
                    ai_content = clean_markdown(resp.text)
                    if len(ai_content) > 50:
                        content = ai_content
                except Exception as gen_err:
                    logger.error(f"Error generando {filename} por IA en export_specs: {str(gen_err)}")

            # Fallback o generación basada en reglas si falla la IA
            if not content:
                if filename == "project.md":
                    content = f"""# Ficha Técnica del Proyecto: {project.get('name', 'Proyecto Spec-First')}
 
 ## Información General
 *   **Idea Semilla:** {idea}
 *   **Dominio:** {metadata.get('domain', 'No especificado')}
 *   **Tipo de Producto:** {metadata.get('productType', 'No especificado')}
 *   **Actores Detectados:** {", ".join(actors_list)}
 
 ## Resumen de Respuestas clave
 {chr(10).join([f"*   **{k}:** {v}" for k, v in answers.items()])}
 
 ---
 *Documento generado automáticamente por [Spec IDE](file://{os.path.abspath(__file__)}).*
 """
            elif filename == "requirements.md":
                content = f"""# Requisitos Funcionales y No Funcionales
 
 ## Requisitos Funcionales (RF)
 A partir de la idea: *{idea}*
 *   **RF-01 (Autenticación):** El sistema debe permitir a los actores ({", ".join(actors_list)}) iniciar sesión de forma segura.
 *   **RF-02 (Core):** El sistema debe resolver la problemática central: "{idea}".
 *   **RF-03 (Administración):** Se debe proveer un panel de control para gestionar recursos.
 
 ## Requisitos No Funcionales (RNF)
 *   **RNF-01 (Seguridad):** Cifrado de datos en tránsito (TLS/HTTPS).
 *   **RNF-02 (Rendimiento):** Tiempos de respuesta del backend inferiores a 300ms para endpoints CRUD.
 *   **RNF-03 (Usabilidad):** Interfaz fluida y accesible que cumpla con los estándares WCAG 2.1 AA.
 """
            elif filename == "user-stories.md":
                content = f"""# Historias de Usuario (Specs)
 
 ## Historia 1: Acceso al Sistema
 **Como** {primary_actor}  
 **Quiero** ingresar con mis credenciales al sistema  
 **Para** poder acceder a mis recursos privados.
 
 *   **Criterio de Aceptación 1:** Dado un usuario no registrado, cuando intenta ingresar, el sistema debe mostrar un error de credenciales.
 *   **Criterio de Aceptación 2:** Dado un usuario registrado, cuando ingresa credenciales válidas, es redirigido al panel de control.
 
 ## Historia 2: Ejecución del Core
 **Como** {primary_actor}  
 **Quiero** interactuar con la funcionalidad principal del software  
 **Para** resolver mi necesidad de negocio.
 """
            elif filename == "frontend.md":
                content = f"""# Especificación Frontend
 
 ## Vistas del Sistema
 1.  **Vista de Autenticación (Login):** Formulario limpio y accesible.
 2.  **Dashboard Principal:** Vista de datos generales y accesos rápidos.
 3.  **Detalle del Core:** Interfaz para interactuar con la lógica principal.
 
 ## Estándares de Estilo
 *   **Tema:** Soporte de tema oscuro/claro.
 *   **Alineación:** Diseño fluido y mobile-first.
 """
            elif filename == "backend.md":
                content = f"""# Especificación Backend
 
 ## Componentes y Servicios
 *   **Servicio de API REST:** Procesa las solicitudes del frontend.
 *   **Módulo de Base de Datos:** Capa de acceso a datos (ORM o consultas optimizadas).
 *   **Capa de Autenticación:** Validación de tokens JWT / Sesiones.
 """
            elif filename == "security.md":
                content = f"""# Políticas de Seguridad y Roles
 
 ## Matriz de Control de Acceso (RBAC)
 *   **Roles:** {", ".join(actors_list)}
 *   **Políticas:**
     *   Cada rol tiene permisos limitados a sus propios recursos.
     *   Los administradores pueden gestionar todos los recursos.
 """
            elif filename == "integrations.md":
                content = f"""# Integraciones con Servicios de Terceros
 
 ## Servicios Identificados
 *   **IA / LLM:** Google Gemini API (para flujos asistidos).
 *   **Otros servicios:** A definir en las fases de desarrollo avanzadas.
 """
            elif filename == "roadmap.md":
                content = f"""# Planificación de Fases y Roadmap
 
 ## Fase 1: Producto Mínimo Viable (MVP)
 *   Implementación del núcleo de la idea: "{idea}"
 *   Autenticación básica de usuarios.
 
 ## Fase 2: Robustez y Escalabilidad (V1)
 *   Integraciones avanzadas de seguridad y analíticas.
 *   Optimización de base de datos.
 """
            elif filename == "tasks.md":
                content = f"""# Lista de Tareas de Desarrollo (TODOs)
 
 - [ ] **Configurar Base de Datos** e infraestructura inicial.
 - [ ] **Implementar Autenticación** y manejo de sesiones.
 - [ ] **Desarrollar el Flujo Principal** para: *{idea}*.
 - [ ] **Realizar Pruebas de Integración** y QA.
 """
            elif filename == "decisions.md":
                content = f"""# Registro de Decisiones de Arquitectura (ADR)
 
 ## ADR-01: Uso de API de Gemini para Refinamiento
 *   **Estatus:** Aceptado
 *   **Contexto:** Necesitamos un descubrimiento inteligente de requisitos.
 *   **Decisión:** Integrar Gemini para generar preguntas condicionales y pre-escribir las specs.
 *   **Consecuencias:** Mayor velocidad de diseño y consistencia técnica inicial.
 """
            elif filename == "glossary.md":
                content = f"""# Glosario de Términos
 
 *   **MVP:** Minimum Viable Product (Producto Mínimo Viable).
 *   **Spec IDE:** Entorno de especificaciones técnicas interactivas.
 *   **SSOT:** Single Source of Truth (Fuente única de verdad).
 """
            elif filename == "agents.md":
                content = f"""# Instrucciones para Agentes de Código (System Prompts)
 
 Este archivo sirve como prompt del sistema para herramientas como Cursor, Cline, Aider o Roo Code.
 
 ```text
 Actúa como un desarrollador experto que va a implementar el proyecto.
 Tu fuente única de verdad es la carpeta /specs del proyecto.
 No escribas código que contradiga las definiciones en:
 - architecture.md
 - database.md
 - api.md
 ```
 """
            elif filename == "openapi.json":
                content = json.dumps({
                    "openapi": "3.0.0",
                    "info": {
                        "title": project.get("name", "Proyecto Spec-First") + " API",
                        "version": "1.0.0",
                        "description": f"Especificación de API para {idea}"
                    },
                    "paths": {}
                }, indent=2)
            else:
                content = f"# Especificación: {filename.replace('.md', '').replace('.json', '').capitalize()}\n\nContenido pendiente de refinamiento por el usuario."
        
        save_single_spec(filename, content)
            
    # Guardar el proyecto con los specModules cargados en project.json
    try:
        with open(project_file, "w", encoding="utf-8") as f:
            json.dump(project, f, ensure_ascii=False, indent=2)
    except Exception as e:
        logger.error(f"Error escribiendo en {project_file} en export_specs: {str(e)}")
        
    GENERATION_STATUS["is_generating"] = False
    GENERATION_STATUS["percent"] = 100

    return {
        "status": "success",
        "message": f"Se han generado {len(generated_files)} archivos de especificación en el directorio /specs/",
        "files": generated_files
    }

@app.post("/api/plan-features")
def plan_features(req: PlanFeaturesRequest, x_gemini_key: Optional[str] = Header(None), x_gemini_fallback_key: Optional[str] = Header(None), x_gemini_model: Optional[str] = Header(None)):
    model = get_gemini_model(x_gemini_key, x_gemini_fallback_key, x_gemini_model)
    project = req.project_data
    answers = project.get("answers", {})
    idea = project.get("seedIdea", "")
    spec_modules = project.get("specModules", {})
    custom_feature = req.custom_feature
    
    product_spec = spec_modules.get("product", "")
    reqs_spec = spec_modules.get("requirements", "")
    
    if custom_feature and custom_feature.strip():
        logger.info(f"Planificando feature personalizada: '{custom_feature.strip()}' por IA...")
        prompt = f"""
        Eres un Product Owner y Staff Software Architect.
        El usuario desea planificar y agregar la siguiente funcionalidad específica a su proyecto: "{custom_feature.strip()}"
        
        Basándote en la idea general del proyecto: "{idea}"
        y la documentación técnica / de producto existente:
        {product_spec}
        {reqs_spec}
        
        Planifica y desglosa en detalle esta funcionalidad específica en sub-características o tareas de especificación técnica necesarias para implementarla.
        Identifica entre 2 y 5 sub-características/módulos clave directamente relacionados con la funcionalidad solicitada.
        Para cada sub-característica, define:
        1. Un ID corto, descriptivo y en minúsculas (ej: "payment-checkout", "stripe-webhook").
        2. Un nombre claro en español (ej: "Checkout de Pago", "Webhook de Notificación de Pago").
        3. Una descripción breve (1-2 líneas).
        4. Un nombre de directorio temático para agruparlo (ej: "billing", "payments").
        
        Devuelve la información estructurada en el siguiente formato JSON estricto:
        [
            {{
                "id": "id-corto",
                "name": "Nombre de la Feature",
                "description": "Descripción de la feature",
                "folder": "nombre-carpeta"
            }}
        ]
        """
    else:
        logger.info("Planificando lista general de features propuestas por IA...")
        prompt = f"""
        Eres un Product Owner y Staff Software Architect.
        Basándote en la idea del proyecto: "{idea}"
        y la documentación de producto existente:
        {product_spec}
        {reqs_spec}
        
        Planifica la lista de características (features) y módulos necesarios para implementar la visión del producto.
        Debes identificar entre 8 y 10 características clave.
        Para cada característica, define:
        1. Un ID corto, descriptivo y en minúsculas (ej: "login", "create-appointment").
        2. Un nombre claro en español (ej: "Inicio de Sesión", "Reserva de Cita").
        3. Una descripción breve (1-2 líneas).
        4. Un nombre de directorio temático para agruparlo (ej: "auth", "dashboard", "appointments", "billing").
        
        Devuelve la información estructurada en el siguiente formato JSON estricto:
        [
            {{
                "id": "id-corto",
                "name": "Nombre de la Feature",
                "description": "Descripción de la feature",
                "folder": "nombre-carpeta"
            }}
        ]
        """
    
    try:
        response = model.generate_content(
            prompt,
            generation_config={"response_mime_type": "application/json"}
        )
        features = json.loads(response.text.strip())
        return {"status": "success", "features": features}
    except Exception as e:
        logger.error(f"Error planificando features por IA: {str(e)}")
        if custom_feature and custom_feature.strip():
            fallback_features = [
                {"id": "custom-feature-spec", "name": f"Especificación de {custom_feature.strip()}", "description": f"Detalle técnico, endpoints e interfaz para {custom_feature.strip()}.", "folder": "custom"}
            ]
        else:
            fallback_features = [
                {"id": "auth", "name": "Autenticación y Registro", "description": "Gestión de registro de usuarios y control de acceso.", "folder": "auth"},
                {"id": "dashboard", "name": "Dashboard Principal", "description": "Vista consolidada de información clave y accesos rápidos.", "folder": "dashboard"},
                {"id": "profile", "name": "Gestión de Perfil", "description": "Edición de datos de usuario y configuraciones personales.", "folder": "profile"},
                {"id": "core-flow", "name": "Flujo Principal", "description": f"Funcionalidad principal del sistema para {idea}", "folder": "core"},
                {"id": "notifications", "name": "Módulo de Notificaciones", "description": "Envío de correos y alertas en tiempo real al usuario.", "folder": "notifications"},
                {"id": "settings", "name": "Configuraciones", "description": "Ajustes avanzados de seguridad e idioma.", "folder": "settings"},
                {"id": "reports", "name": "Reportes y Estadísticas", "description": "Auditoría, logs de actividad y métricas de negocio.", "folder": "reports"},
                {"id": "api-keys", "name": "Gestión de API Keys", "description": "Generación y revocación de tokens de acceso externo.", "folder": "developer"}
            ]
        return {"status": "fallback", "features": fallback_features}

class GenerateFeatureRequest(BaseModel):
    project_data: dict
    feature: dict

@app.post("/api/generate-feature")
def generate_feature(req: GenerateFeatureRequest, x_gemini_key: Optional[str] = Header(None), x_gemini_fallback_key: Optional[str] = Header(None), x_gemini_model: Optional[str] = Header(None)):
    model = get_gemini_model(x_gemini_key, x_gemini_fallback_key, x_gemini_model)
    project = req.project_data
    feature = req.feature
    
    answers = project.get("answers", {})
    idea = project.get("seedIdea", "")
    spec_modules = project.get("specModules", {})
    
    specs_dir = get_specs_dir()
    features_dir = os.path.join(specs_dir, "features")
    folder = feature.get("folder", "general").strip().lower()
    feature_id = feature.get("id", "feature").strip().lower()
    
    folder_path = os.path.join(features_dir, folder)
    if not os.path.exists(folder_path):
        os.makedirs(folder_path, exist_ok=True)
        
    filepath = os.path.join(folder_path, f"{feature_id}.md")
    
    product_spec = spec_modules.get("product", "")
    db_spec = spec_modules.get("database", "")
    
    prompt = f"""
    Eres un Product Owner y Analista Técnico de Software.
    Tu tarea es redactar la especificación técnica en Markdown para la siguiente feature:
    
    Nombre: {feature.get('name')}
    Descripción: {feature.get('description')}
    Categoría/Carpeta: {folder}
    
    Contexto General del Proyecto:
    Idea: "{idea}"
    Visión del producto: {product_spec}
    Esquema de Base de Datos: {db_spec}
    
    Debes redactar un archivo Markdown detallado que incluya obligatoriamente:
    1. Historia de Usuario (User Story): Formato "Como [Rol], Quiero [Acción], Para [Beneficio]".
    2. Criterios de Aceptación Detallados: Reglas de comportamiento esperadas (con formato Dado/Cuando/Entonces si aplica).
    3. Casos de Error y Casos Borde (Edge cases): Errores de red, entradas inválidas, violaciones de reglas de negocio, etc.
    4. DIAGRAMA MERMAID OBLIGATORIO: Si incluyes diagramas de flujo, secuencias de interacción o estados, DEBES generarlos SIEMPRE en bloques de código Mermaid.js (bloque ```mermaid ... ```). Queda estrictamente prohibido usar gráficos en texto ASCII plano o esquemas gráficos de texto.
    
    Restricción Absoluta:
    * NO escribas código de implementación (como funciones, endpoints en Node/Python, etc.). Mantente exclusivamente en la etapa de diseño funcional, diseño técnico y documentación.
    * Devuelve únicamente el contenido Markdown listo para ser guardado. No utilices bloques de código Markdown (como ```markdown) para envolver tu respuesta.
    """
    
    content = ""
    try:
        resp = model.generate_content(prompt)
        content = clean_markdown(resp.text)
    except Exception as e:
        logger.error(f"Error generando feature {feature_id} por IA: {str(e)}")
        content = f"""# Feature: {feature.get('name')}
        
## Descripción
{feature.get('description')}

## Historia de Usuario
**Como** Usuario del sistema  
**Quiero** utilizar la función de {feature.get('name')}  
**Para** cumplir con mi objetivo en la plataforma.

## Criterios de Aceptación
1. **Acceso básico:** Dado un usuario logueado, cuando accede a la sección, el sistema muestra la interfaz de {feature.get('name')}.
2. **Validación:** El sistema debe comprobar la validez de los datos de entrada antes de procesarlos.

## Casos de Error (Edge Cases)
*   **Error 1:** Si se envían campos vacíos, el sistema debe retornar un código 400 Bad Request.
*   **Error 2:** Si ocurre un error de conexión, se debe alertar al usuario y reintentar la acción.
"""
        
    try:
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content.strip())
            
        if "specModules" not in project:
            project["specModules"] = {}
            
        key_name = f"features/{folder}/{feature_id}"
        project["specModules"][key_name] = content.strip()
        
        if "featuresList" not in project:
            project["featuresList"] = []
            
        if not any(f.get("id") == feature_id for f in project["featuresList"]):
            project["featuresList"].append(feature)
            
        project_file = get_project_file()
        os.makedirs(os.path.dirname(project_file), exist_ok=True)
        with open(project_file, "w", encoding="utf-8") as f:
            json.dump(project, f, ensure_ascii=False, indent=2)
            
        return {
            "status": "success", 
            "filepath": f"features/{folder}/{feature_id}.md", 
            "content": content.strip(),
            "project_data": project
        }
    except Exception as e:
        logger.error(f"Error guardando feature en disco: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/copilot")
async def copilot_chat(req: CopilotRequest, x_gemini_key: str = Header(None)):
    model = get_gemini_model(x_gemini_key)
    project = req.projectData
    answers = project.get("answers", {})
    idea = project.get("seedIdea", "")
    
    prompt = f"""
    Eres el Copiloto de Spec IDE, un Staff Software Architect.
    Ayuda al usuario a estructurar su especificación técnica.
    
    Proyecto: "{project.get('name', 'Sin título')}"
    Idea Semilla: "{idea}"
    Archivo activo: "{req.activeFile}"
    Respuestas dadas en el Wizard: {json.dumps(answers, ensure_ascii=False)}
    
    Pregunta o solicitud del usuario: "{req.prompt}"
    
    Instrucciones:
    1. Responde de forma técnica, profesional, clara y directa.
    2. Si pide endpoints de API, modelos de datos o diagramas, provee la respuesta lista para copiar.
    3. No utilices introducciones largas, ve directo al grano.
    """
    
    try:
        response = model.generate_content(prompt)
        return {"reply": response.text.strip()}
    except Exception as e:
        logger.error(f"Error en chat copiloto: {str(e)}")
        return {"reply": f"Error al procesar consulta con Gemini: {str(e)}"}

@app.post("/api/autocomplete-file")
async def autocomplete_file(req: AutocompleteFileRequest, x_gemini_key: str = Header(None)):
    model = get_gemini_model(x_gemini_key)
    project = req.project_data
    filename = req.filename
    
    answers = project.get("answers", {})
    idea = project.get("seedIdea", "")
    spec_modules = project.get("specModules", {})
    
    # Contexto existente
    product_spec = spec_modules.get("product", "")
    db_spec = spec_modules.get("database", "")
    
    # Prompt de autocompletado
    prompt = f"""
    Actúa como un Staff Software Architect de nivel mundial.
    Tu objetivo es redactar el contenido técnico completo del archivo '{filename}' para el proyecto de especificación técnica.
    
    Idea semilla del producto:
    "{idea}"
    
    Definiciones de producto y negocio:
    {product_spec}
    
    Esquema y modelo de datos actual:
    {db_spec}
    
    Respuestas dadas por el usuario en su entrevista de descubrimiento:
    {json.dumps(answers, ensure_ascii=False)}
    
    INSTRUCCIONES DE DISEÑO:
    1. Genera documentación técnica detallada, profesional y estructurada específica para el archivo '{filename}'.
    2. Si el archivo es '{filename}', asegúrate de detallar todos los aspectos relacionados con su temática (por ejemplo, si es 'security.md' habla sobre roles, auth, cifrado, OWASP; si es 'roadmap.md' sobre fases de release; si es 'integrations.md' sobre pasarelas de pago, webhooks, etc.).
    3. Si el archivo es 'openapi.json', devuelve únicamente un JSON válido que cumpla con el estándar OpenAPI 3.0.0. No incluyas explicaciones en texto para archivos JSON.
    4. Para archivos Markdown, no utilices bloques de código Markdown generales (como ```markdown o ```) para envolver tu respuesta completa; simplemente escribe el contenido Markdown crudo directamente.
    5. DIAGRAMAS MERMAID OBLIGATORIOS: Si incluyes diagramas de flujo, esquemas de arquitectura, modelos de base de datos o secuencias de API, DEBES generarlos SIEMPRE en bloques de código Mermaid.js (utilizando la sintaxis ```mermaid ... ```). Queda estrictamente prohibido utilizar texto ASCII plano o esquemas gráficos de texto rígido.
    
    Escribe el documento completo para '{filename}':
    """
    
    logger.info(f"Autocompletando el archivo {filename} por IA...")
    
    try:
        response = model.generate_content(prompt)
        content = clean_markdown(response.text.strip())
        
        # Escribir directamente en la carpeta specs
        specs_dir = get_specs_dir()
        project_file = get_project_file()
        filepath = os.path.join(specs_dir, filename)
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)
            
        # Actualizar en memoria y project.json
        if "specModules" not in project:
            project["specModules"] = {}
        
        name_key = filename.replace(".md", "").replace(".json", "")
        project["specModules"][name_key] = content
        
        os.makedirs(os.path.dirname(project_file), exist_ok=True)
        with open(project_file, "w", encoding="utf-8") as f:
            json.dump(project, f, ensure_ascii=False, indent=2)
            
        return {
            "status": "success",
            "message": f"Archivo {filename} autocompletado y guardado con éxito.",
            "content": content,
            "project": project
        }
    except Exception as e:
        logger.error(f"Error autocompletando {filename}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/copilot-chat")
def copilot_chat(req: CopilotChatRequest, x_gemini_key: Optional[str] = Header(None), x_gemini_fallback_key: Optional[str] = Header(None), x_gemini_model: Optional[str] = Header(None)):
    try:
        model = get_gemini_model(x_gemini_key, x_gemini_fallback_key, x_gemini_model)
        pdata = req.project_data or {}
        proj_name = pdata.get("name", "Proyecto Activo")
        seed_idea = pdata.get("seedIdea", "")
        answers = pdata.get("answers", {})
        spec_modules = pdata.get("specModules", {})

        # Construir contexto completo de especificaciones
        specs_summary = []
        for fname, content in spec_modules.items():
            if content and content.strip():
                specs_summary.append(f"=== INICIO ARCHIVO SPEC: {fname} ===\n{content.strip()}\n=== FIN ARCHIVO SPEC: {fname} ===")

        if not specs_summary:
            specs_summary_text = "Aún no hay archivos de especificación (.md) completos. Solo se cuenta con la idea semilla."
        else:
            specs_summary_text = "\n\n".join(specs_summary)

        local_docs_summary = get_local_project_docs_summary()

        system_instruction = f"""Eres el "Spec Copilot", un Arquitecto de Software y Product Owner experimentado que conversa sobre el proyecto "{proj_name}".

OBJETIVO:
Tu misión es actuar como el interlocutor principal entre el usuario y las especificaciones técnicas del proyecto. Responde preguntas, aclara dudas, resume decisiones de diseño, explica la arquitectura o sugiere mejoras en lenguaje claro, amigable y estructurado.

INFORMACIÓN DEL PROYECTO:
- Nombre: {proj_name}
- Idea General: {seed_idea}
- Respuestas del Wizard: {json.dumps(answers, ensure_ascii=False)}
{local_docs_summary}

DOCUMENTOS DE ESPECIFICACIÓN DISPONIBLES:
{specs_summary_text}

REGLAS DE RESPUESTA:
1. Responde de forma clara, directa y estructurada en Markdown (usa títulos breves, viñetas, bloques de código SQL/JSON/JS cuando aporte valor).
2. Cita siempre el documento de origen cuando menciones detalles específicos (ejemplo: [product.md], [architecture.md], [database.md], etc.).
3. Si en el proyecto existen documentos locales escaneados (mostrados arriba), ÚSALOS e intégralos activamente en tu respuesta. NUNCA digas que no tienes acceso a los archivos si ya se muestran escaneados.
4. Si el usuario te pide un resumen alto nivel, sé sintético y resalta el propósito del proyecto, la arquitectura propuesta y la pila tecnológica.
5. Mantén un tono profesional, servicial y experto.
6. SI EL USUARIO TE PIDE CREAR, GENERAR O IMPLEMENTAR UNA NUEVA FUNCIONALIDAD/FEATURE (O CREAR SUS ARCHIVOS .MD):
   - Explica brevemente la solución arquitectónica.
   - AL FINAL DE TU RESPUESTA, incluye obligatoriamente una etiqueta con este formato JSON exacto en una sola línea (reemplazando con los valores apropiados):
     <!-- GENERATE_FEATURE: {{"name": "Nombre de la Feature", "folder": "nombre-carpeta", "description": "Breve descripcion de la feature"}} -->
"""

        gemini_history = []
        for msg in (req.history or []):
            role = "user" if msg.get("role") == "user" else "model"
            content = msg.get("content", "")
            if content:
                gemini_history.append({"role": role, "parts": [content]})

        chat = model.start_chat(history=gemini_history)
        
        full_prompt = f"{system_instruction}\n\nPREGUNTA E INSTRUCCIÓN DEL USUARIO:\n{req.message}"
        
        response = chat.send_message(full_prompt)
        reply_text = clean_markdown(response.text)

        # Fallback de seguridad: si el usuario solicitó generar/crear una feature y la IA no generó la etiqueta
        if "GENERATE_FEATURE:" not in reply_text:
            user_msg_lower = req.message.lower()
            trigger_words = ["generar", "crear", "hacer", "implementar", "redactar", "feature", "funcionalidad", "especificacion", "especificación", "md", "fichas", "archivos", "modulo", "módulo", "boton", "botón", "planificar"]
            if any(w in user_msg_lower for w in trigger_words):
                clean_req = req.message.strip().replace('"', '').replace("'", "")
                feat_name = clean_req[:40] if len(clean_req) <= 40 else clean_req[:37] + "..."
                folder_name = "modulos"
                payload_json = json.dumps({
                    "name": feat_name,
                    "folder": folder_name,
                    "description": f"Especificación técnica generada desde el chat."
                }, ensure_ascii=False)
                reply_text += f'\n\n<!-- GENERATE_FEATURE: {payload_json} -->'

        # Guardar historial actualizado en el disco del proyecto
        history_file = os.path.join(get_target_project_path(), "chat_history.json")
        updated_history = (req.history or []) + [
            {"role": "user", "content": req.message},
            {"role": "model", "content": reply_text}
        ]
        try:
            with open(history_file, "w", encoding="utf-8") as f:
                json.dump(updated_history, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"Error guardando chat_history.json: {str(e)}")

        return {"status": "success", "reply": reply_text, "history": updated_history}
    except HTTPException as http_e:
        raise http_e
    except Exception as e:
        err_msg = str(e)
        logger.error(f"Error en copilot-chat: {err_msg}")
        if is_quota_error(err_msg):
            raise HTTPException(status_code=429, detail=err_msg)
        raise HTTPException(status_code=500, detail=err_msg)

@app.post("/api/copilot-chat-stream")
def copilot_chat_stream(req: CopilotChatRequest, x_gemini_key: Optional[str] = Header(None), x_gemini_fallback_key: Optional[str] = Header(None), x_gemini_model: Optional[str] = Header(None)):
    def event_generator():
        try:
            model = get_gemini_model(x_gemini_key, x_gemini_fallback_key, x_gemini_model)
            pdata = req.project_data or {}
            proj_name = pdata.get("name", "Proyecto Activo")
            seed_idea = pdata.get("seedIdea", "")
            answers = pdata.get("answers", {})
            spec_modules = pdata.get("specModules", {})

            specs_summary = []
            for fname, content in spec_modules.items():
                if content and content.strip():
                    specs_summary.append(f"=== INICIO ARCHIVO SPEC: {fname} ===\n{content.strip()}\n=== FIN ARCHIVO SPEC: {fname} ===")

            specs_summary_text = "\n\n".join(specs_summary) if specs_summary else "Aún no hay archivos de especificación (.md) completos. Solo se cuenta con la idea semilla."

            local_docs_summary = get_local_project_docs_summary()

            system_instruction = f"""Eres el "Spec Copilot", un Arquitecto de Software y Product Owner experimentado que conversa sobre el proyecto "{proj_name}".

OBJETIVO:
Tu misión es actuar como el interlocutor principal entre el usuario y las especificaciones técnicas del proyecto. Responde preguntas, aclara dudas, resume decisiones de diseño, explica la arquitectura o sugiere mejoras en lenguaje claro, amigable y estructurado.

INFORMACIÓN DEL PROYECTO:
- Nombre: {proj_name}
- Idea General: {seed_idea}
- Respuestas del Wizard: {json.dumps(answers, ensure_ascii=False)}
{local_docs_summary}

DOCUMENTOS DE ESPECIFICACIÓN DISPONIBLES:
{specs_summary_text}

REGLAS DE RESPUESTA:
1. Responde de forma clara, directa y estructurada en Markdown (usa títulos breves, viñetas, bloques de código SQL/JSON/JS cuando aporte valor).
2. Cita siempre el documento de origen cuando menciones detalles específicos (ejemplo: [product.md], [architecture.md], [database.md], etc.).
3. DIAGRAMAS Y GRÁFICOS: Si incluyes o el usuario te pide esquemas de arquitectura, modelos de base de datos, flujos de usuario o secuencias de API, DEBES generarlos SIEMPRE en bloques de código Mermaid.js (bloque ```mermaid ... ```). NUNCA utilices texto ASCII plano o gráficos de texto para diagramas.
4. Si en el proyecto existen documentos locales escaneados (mostrados arriba), ÚSALOS e intégralos activamente en tu respuesta. NUNCA digas que no tienes acceso a los archivos si ya se muestran escaneados.
5. Si el usuario te pide un resumen alto nivel, sé sintético y resalta el propósito del proyecto, la arquitectura propuesta y la pila tecnológica.
6. Mantén un tono profesional, servicial y experto.
7. SI EL USUARIO TE PIDE CREAR, GENERAR O IMPLEMENTAR UNA NUEVA FUNCIONALIDAD/FEATURE (O CREAR SUS ARCHIVOS .MD):
   - Explica brevemente la solución arquitectónica.
   - AL FINAL DE TU RESPUESTA, incluye obligatoriamente una etiqueta con este formato JSON exacto en una sola línea (reemplazando con los valores apropiados):
     <!-- GENERATE_FEATURE: {{"name": "Nombre de la Feature", "folder": "nombre-carpeta", "description": "Breve descripcion de la feature"}} -->
"""

            # Cargar historial existente en disco para no sobreescribir mensajes previos si el cliente rellenó history con []
            history_file = os.path.join(get_target_project_path(), "chat_history.json")
            disk_history = []
            if os.path.exists(history_file):
                try:
                    with open(history_file, "r", encoding="utf-8") as f:
                        disk_history = json.load(f)
                except Exception as e:
                    logger.error(f"Error leyendo chat_history.json en disco: {str(e)}")

            client_history = req.history or []
            base_history = client_history if (len(client_history) >= len(disk_history)) else disk_history

            gemini_history = []
            for msg in base_history:
                role = "user" if msg.get("role") == "user" else "model"
                content = msg.get("content", "")
                if content:
                    gemini_history.append({"role": role, "parts": [content]})

            chat = model.start_chat(history=gemini_history)
            full_prompt = f"{system_instruction}\n\nPREGUNTA E INSTRUCCIÓN DEL USUARIO:\n{req.message}"

            response = chat.send_message(full_prompt, stream=True)
            accumulated_text = ""

            if isinstance(response, UnifiedResponse) or not hasattr(response, "__iter__"):
                chunks = [response]
            else:
                try:
                    chunks = iter(response)
                except TypeError:
                    chunks = [response]

            for chunk in chunks:
                chunk_text = getattr(chunk, "text", "") or ""
                if chunk_text:
                    accumulated_text += chunk_text
                    data_json = json.dumps({"type": "chunk", "content": chunk_text}, ensure_ascii=False)
                    yield f"data: {data_json}\n\n"

            reply_text = clean_markdown(accumulated_text)

            # Fallback de seguridad: si el usuario solicitó generar/crear una feature y la IA no generó la etiqueta
            if "GENERATE_FEATURE:" not in reply_text:
                user_msg_lower = req.message.lower()
                trigger_words = ["generar", "crear", "hacer", "implementar", "redactar", "feature", "funcionalidad", "especificacion", "especificación", "md", "fichas", "archivos", "modulo", "módulo", "boton", "botón", "planificar"]
                if any(w in user_msg_lower for w in trigger_words):
                    clean_req = req.message.strip().replace('"', '').replace("'", "")
                    feat_name = clean_req[:40] if len(clean_req) <= 40 else clean_req[:37] + "..."
                    folder_name = "modulos"
                    payload_json = json.dumps({
                        "name": feat_name,
                        "folder": folder_name,
                        "description": "Especificación técnica generada desde el chat."
                    }, ensure_ascii=False)
                    tag_str = f'\n\n<!-- GENERATE_FEATURE: {payload_json} -->'
                    reply_text += tag_str
                    data_json = json.dumps({"type": "chunk", "content": tag_str}, ensure_ascii=False)
                    yield f"data: {data_json}\n\n"

            # Guardar historial actualizado en el disco del proyecto
            updated_history = base_history + [
                {"role": "user", "content": req.message},
                {"role": "model", "content": reply_text}
            ]
            try:
                with open(history_file, "w", encoding="utf-8") as f:
                    json.dump(updated_history, f, ensure_ascii=False, indent=2)
            except Exception as e:
                logger.error(f"Error guardando chat_history.json: {str(e)}")

            done_json = json.dumps({"type": "done", "history": updated_history}, ensure_ascii=False)
            yield f"data: {done_json}\n\n"

        except Exception as e:
            err_msg = str(e)
            logger.error(f"Error en copilot-chat-stream: {err_msg}")
            err_json = json.dumps({"type": "error", "message": err_msg}, ensure_ascii=False)
            yield f"data: {err_json}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")

@app.get("/api/copilot-history")
async def get_copilot_history():
    history_file = os.path.join(get_target_project_path(), "chat_history.json")
    if os.path.exists(history_file):
        try:
            with open(history_file, "r", encoding="utf-8") as f:
                history = json.load(f)
                return {"status": "success", "history": history}
        except Exception as e:
            logger.error(f"Error leyendo chat_history.json: {str(e)}")
    return {"status": "success", "history": []}

@app.post("/api/copilot-clear-history")
async def clear_copilot_history_endpoint():
    history_file = os.path.join(get_target_project_path(), "chat_history.json")
    if os.path.exists(history_file):
        try:
            os.remove(history_file)
        except Exception as e:
            logger.error(f"Error eliminando chat_history.json: {str(e)}")
    return {"status": "success", "message": "Historial de chat borrado"}

@app.post("/api/explore-extract-answers")
async def explore_extract_answers(req: ExploreExtractRequest, x_gemini_key: Optional[str] = Header(None), x_gemini_fallback_key: Optional[str] = Header(None), x_gemini_model: Optional[str] = Header(None)):
    try:
        model = get_gemini_model(x_gemini_key, x_gemini_fallback_key, x_gemini_model)
        
        chat_text_list = []
        for msg in req.history:
            role = "Usuario" if msg.get("role") == "user" else "IA (Spec Copilot)"
            content = msg.get("content", "")
            if content:
                chat_text_list.append(f"{role}: {content}")

        chat_history_str = "\n".join(chat_text_list)
        
        prompt = f"""
Eres un Arquitecto de Software y Analista de Requisitos Senior.
Analiza la siguiente conversación de exploración inicial ("Explore") entre el usuario y la IA sobre la idea del proyecto: "{req.idea}".

HISTORIAL DE LA CONVERSACIÓN:
{chat_history_str}

TU OBJETIVO:
Extraer y deducir las respuestas técnicas más precisas y relevantes discutidas en la charla.
Devuelve ÚNICAMENTE un objeto JSON donde las claves sean IDs de parámetros (como q_auth, q_database, q_features_core, q_platform, q_language, q_privacy, q_latency, etc.) y los valores sean las decisiones concluidas o deducidas de la charla de forma concisa.

Instrucciones:
- Extrae únicamente parámetros relevantes para el tipo de software discutido (por ejemplo: si es una app local de teclado o CLI, no infieras pasarelas de pago o autenticación JWT si no se mencionaron).
- Devuelve ÚNICAMENTE el objeto JSON válido sin bloques de código markdown ni texto antes o después.
"""
        response = model.generate_content(prompt)
        cleaned = clean_markdown(response.text.strip())
        extracted_data = json.loads(cleaned)
        return {"status": "success", "answers": extracted_data}
    except Exception as e:
        logger.error(f"Error extrayendo respuestas de explore: {str(e)}")
        return {
            "status": "partial",
            "answers": {
                "q_auth": "Sin autenticación / Local",
                "q_database": "Local SQLite / JSON",
                "q_notifications_strategy": "Sin notificaciones",
                "q_payment_integration": "No contempla pagos"
            }
        }

@app.post("/api/open-specs-folder")
async def open_specs_folder():
    import os
    import platform
    import shutil
    import subprocess
    
    dir_path = get_specs_dir()
    if not os.path.exists(dir_path):
        os.makedirs(dir_path, exist_ok=True)
        
    logger.info(f"Abriendo la carpeta de specs {dir_path} en el editor...")
    
    try:
        # Intentar con Cursor primero
        if shutil.which("cursor"):
            subprocess.Popen(["cursor", dir_path])
            return {"status": "success", "message": "Abierto con Cursor"}
            
        # Intentar con VS Code
        if shutil.which("code"):
            subprocess.Popen(["code", dir_path])
            return {"status": "success", "message": "Abierto con VS Code"}
            
        # Fallback al sistema operativo por defecto
        system_name = platform.system()
        if system_name == "Darwin": # macOS
            subprocess.Popen(["open", dir_path])
        elif system_name == "Windows":
            os.startfile(dir_path)
        else: # Linux y otros
            subprocess.Popen(["xdg-open", dir_path])
            
        return {"status": "success", "message": "Abierto con el programa por defecto del sistema"}
    except Exception as e:
        logger.error(f"Error al abrir la carpeta de specs: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/")
async def serve_root():
    index_path = os.path.join(static_dir, "index.html")
    if os.path.exists(index_path):
        headers = {"Cache-Control": "no-cache, no-store, must-revalidate", "Pragma": "no-cache", "Expires": "0"}
        return FileResponse(index_path, headers=headers)
    return JSONResponse(status_code=404, content={"message": "Frontend index.html not found"})

# Servir index.html para todas las demás rutas no API (SPA routing fallback)
@app.get("/{rest_of_path:path}")
async def serve_spa(rest_of_path: str):
    file_path = os.path.join(static_dir, rest_of_path)
    headers = {"Cache-Control": "no-cache, no-store, must-revalidate", "Pragma": "no-cache", "Expires": "0"}
    if os.path.exists(file_path) and os.path.isfile(file_path):
        return FileResponse(file_path, headers=headers)
    
    index_path = os.path.join(static_dir, "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path, headers=headers)
    
class NoCacheStaticFiles(StaticFiles):
    async def get_response(self, path: str, scope):
        response = await super().get_response(path, scope)
        response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
        response.headers["Pragma"] = "no-cache"
        response.headers["Expires"] = "0"
        return response

# Montar los estáticos al final para permitir que las rutas de la API tengan prioridad
app.mount("/", NoCacheStaticFiles(directory=static_dir, html=True), name="static")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="127.0.0.1", port=8000, reload=True, reload_excludes=[".git/*", ".venv/*", "specs/*", "agendapro/*", "__pycache__/*"])
