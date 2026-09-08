import os
import json
import sqlite3
import logging
from typing import List, Dict, Any, Optional

logger = logging.getLogger("spec_ide.project_manager")

# Directorios de configuración y base de datos SQLite
ROOT_APP_DIR = os.path.abspath(os.path.dirname(__file__))
GLOBAL_CONFIG_DIR = os.path.expanduser("~/.spec_ide")
PRIMARY_DB_PATH = os.path.join(GLOBAL_CONFIG_DIR, "projects_registry.db")
FALLBACK_DB_PATH = os.path.join(ROOT_APP_DIR, "projects_registry.db")

ACTIVE_PROJECT_CONFIG_FILE = os.path.join(ROOT_APP_DIR, ".active_project.json")
RECENT_PROJECTS_CONFIG_FILE = os.path.join(ROOT_APP_DIR, ".recent_projects.json")

def _get_db_path() -> str:
    try:
        os.makedirs(GLOBAL_CONFIG_DIR, exist_ok=True)
        return PRIMARY_DB_PATH
    except Exception as e:
        logger.warning(f"No se pudo acceder a {GLOBAL_CONFIG_DIR}: {e}. Usando base de datos local.")
        return FALLBACK_DB_PATH

def get_db_connection():
    db_path = _get_db_path()
    conn = sqlite3.connect(db_path, timeout=10.0)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    try:
        with get_db_connection() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS projects (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    path TEXT UNIQUE NOT NULL,
                    seed_idea TEXT,
                    created_at REAL,
                    updated_at REAL,
                    is_active INTEGER DEFAULT 0
                )
            """)
            conn.execute("CREATE INDEX IF NOT EXISTS idx_projects_path ON projects(path)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_projects_updated_at ON projects(updated_at)")
            conn.commit()
    except Exception as e:
        logger.error(f"Error inicializando base de datos SQLite de proyectos: {str(e)}")

# Inicializar tabla SQLite al importar el módulo
init_db()

def _extract_project_metadata(folder_path: str) -> Dict[str, Any]:
    abs_path = os.path.abspath(folder_path.strip())
    folder_name = os.path.basename(abs_path)
    clean_name = folder_name.replace("-", " ").replace("_", " ").title()
    seed_idea = ""
    updated_at = os.path.getmtime(abs_path) * 1000 if os.path.exists(abs_path) else 0

    proj_json_path = os.path.join(abs_path, "project.json")
    if os.path.exists(proj_json_path):
        try:
            with open(proj_json_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                clean_name = data.get("name") or clean_name
                seed_idea = data.get("seedIdea") or data.get("idea") or seed_idea
                if data.get("updatedAt"):
                    updated_at = float(data["updatedAt"])
                else:
                    updated_at = os.path.getmtime(proj_json_path) * 1000
        except Exception as e:
            logger.error(f"Error leyendo {proj_json_path}: {e}")

    # Si no hay seedIdea en json, intentar buscar fragmentos en specs/ o archivos .md
    if not seed_idea:
        specs_dir = os.path.join(abs_path, "specs")
        candidates = [
            os.path.join(abs_path, "PRODUCT.md"),
            os.path.join(abs_path, "especificacion_proyecto.md"),
            os.path.join(abs_path, "especificacion_proyecto (1).md"),
            os.path.join(abs_path, "README.md"),
            os.path.join(specs_dir, "product.md"),
            os.path.join(specs_dir, "project.md")
        ]
        for candidate in candidates:
            if os.path.exists(candidate) and os.path.isfile(candidate):
                try:
                    with open(candidate, "r", encoding="utf-8") as f:
                        content = f.read(1000)
                        lines = [line.strip() for line in content.split("\n") if line.strip() and not line.strip().startswith("#")]
                        if lines:
                            seed_idea = lines[0]
                            if len(seed_idea) > 120:
                                seed_idea = seed_idea[:117] + "..."
                            break
                except Exception:
                    pass

    if not seed_idea:
        seed_idea = f"Proyecto {clean_name}"

    proj_id = f"proj_{abs(hash(abs_path))}"

    return {
        "id": proj_id,
        "name": clean_name,
        "path": abs_path,
        "seedIdea": seed_idea,
        "updatedAt": updated_at
    }

def register_project(path: str, name: Optional[str] = None, seed_idea: Optional[str] = None, updated_at: Optional[float] = None, is_active: bool = False) -> Dict[str, Any]:
    abs_path = os.path.abspath(path.strip())
    if not os.path.exists(abs_path):
        os.makedirs(abs_path, exist_ok=True)

    meta = _extract_project_metadata(abs_path)
    p_name = name or meta["name"]
    p_seed = seed_idea or meta["seedIdea"]
    p_updated = updated_at or meta["updatedAt"] or (os.path.getmtime(abs_path) * 1000)
    p_id = meta["id"]

    try:
        with get_db_connection() as conn:
            if is_active:
                conn.execute("UPDATE projects SET is_active = 0")
            conn.execute("""
                INSERT INTO projects (id, name, path, seed_idea, created_at, updated_at, is_active)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(path) DO UPDATE SET
                    name = excluded.name,
                    seed_idea = COALESCE(NULLIF(excluded.seed_idea, ''), projects.seed_idea),
                    updated_at = excluded.updated_at,
                    is_active = CASE WHEN excluded.is_active = 1 THEN 1 ELSE projects.is_active END
            """, (p_id, p_name, abs_path, p_seed, p_updated, p_updated, 1 if is_active else 0))
            conn.commit()
    except Exception as e:
        logger.error(f"Error registrando proyecto en SQLite ({abs_path}): {str(e)}")

    # Mantener sincronizado el archivo JSON legacy para herramientas externas
    _sync_legacy_json_files(abs_path)

    return {
        "id": p_id,
        "name": p_name,
        "path": abs_path,
        "seedIdea": p_seed,
        "updatedAt": p_updated,
        "isActive": is_active
    }

def set_active_project(path: str) -> str:
    abs_path = os.path.abspath(path.strip())
    if not os.path.exists(abs_path):
        os.makedirs(abs_path, exist_ok=True)

    register_project(abs_path, is_active=True)

    try:
        with get_db_connection() as conn:
            conn.execute("UPDATE projects SET is_active = 0 WHERE path != ?", (abs_path,))
            conn.execute("UPDATE projects SET is_active = 1 WHERE path = ?", (abs_path,))
            conn.commit()
    except Exception as e:
        logger.error(f"Error actualizando proyecto activo en SQLite: {str(e)}")

    try:
        with open(ACTIVE_PROJECT_CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump({"active_path": abs_path}, f, ensure_ascii=False, indent=2)
    except Exception as e:
        logger.error(f"Error escribiendo {ACTIVE_PROJECT_CONFIG_FILE}: {str(e)}")

    return abs_path

def load_active_project_path() -> str:
    if os.path.exists(ACTIVE_PROJECT_CONFIG_FILE):
        try:
            with open(ACTIVE_PROJECT_CONFIG_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                active_path = data.get("active_path")
                if active_path and os.path.exists(active_path):
                    return os.path.abspath(active_path)
        except Exception as e:
            logger.error(f"Error leyendo active_project.json: {str(e)}")
    return ROOT_APP_DIR

def delete_project(path: str, delete_disk_files: bool = False) -> Dict[str, Any]:
    abs_path = os.path.abspath(path.strip())
    try:
        with get_db_connection() as conn:
            conn.execute("DELETE FROM projects WHERE path = ?", (abs_path,))
            conn.commit()
    except Exception as e:
        logger.error(f"Error eliminando proyecto de SQLite ({abs_path}): {str(e)}")

    if delete_disk_files and os.path.exists(abs_path):
        import shutil
        try:
            shutil.rmtree(abs_path)
            logger.info(f"Carpeta de proyecto eliminada de disco: {abs_path}")
        except Exception as e:
            logger.error(f"Error eliminando directorio de disco ({abs_path}): {str(e)}")
            return {
                "status": "partial",
                "message": f"Se quitó del registro, pero no se pudo borrar del disco: {str(e)}"
            }

    return {
        "status": "success",
        "message": f"Proyecto '{os.path.basename(abs_path)}' eliminado correctamente."
    }

def list_projects() -> List[Dict[str, Any]]:
    init_db()
    current_active = load_active_project_path()
    res = []

    try:
        with get_db_connection() as conn:
            rows = conn.execute("SELECT * FROM projects ORDER BY updated_at DESC").fetchall()
            for r in rows:
                p_abs = r["path"]
                if os.path.exists(p_abs):
                    res.append({
                        "id": r["id"],
                        "name": r["name"],
                        "path": p_abs,
                        "updatedAt": float(r["updated_at"] or 0),
                        "isActive": (p_abs == current_active),
                        "seedIdea": r["seed_idea"] or ""
                    })
    except Exception as e:
        logger.error(f"Error consultando proyectos desde SQLite: {str(e)}")

    # Si la lista está vacía, registrar el proyecto activo actual
    if not res:
        meta = register_project(current_active, is_active=True)
        res = [{
            "id": meta["id"],
            "name": meta["name"],
            "path": meta["path"],
            "updatedAt": meta["updatedAt"],
            "isActive": True,
            "seedIdea": meta["seedIdea"]
        }]

    return res

def _sync_legacy_json_files(active_path: str):
    try:
        paths = [active_path]
        if os.path.exists(RECENT_PROJECTS_CONFIG_FILE):
            try:
                with open(RECENT_PROJECTS_CONFIG_FILE, "r", encoding="utf-8") as f:
                    old_p = json.load(f)
                    for p in old_p:
                        if p not in paths and os.path.exists(p):
                            paths.append(p)
            except Exception:
                pass

        with open(RECENT_PROJECTS_CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(paths[:50], f, ensure_ascii=False, indent=2)

        os.makedirs(GLOBAL_CONFIG_DIR, exist_ok=True)
        with open(os.path.join(GLOBAL_CONFIG_DIR, "recent_projects.json"), "w", encoding="utf-8") as f:
            json.dump(paths[:100], f, ensure_ascii=False, indent=2)
    except Exception as e:
        logger.error(f"Error sincronizando JSONs legacy: {str(e)}")
