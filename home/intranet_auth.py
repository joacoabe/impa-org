"""
Utilidades para autenticación con la intranet en imparg.org.
- Login con usuario/contraseña de la intranet (POST /api/v1/auth/login).
- Obtener usuario desde sesión (tras login o token).
- Comprobar si puede editar la página "sitio" de una iglesia.
"""
import logging
import requests
from django.conf import settings

logger = logging.getLogger(__name__)


def login_intranet(username, password):
    """
    Llama a POST /api/v1/auth/login de la intranet con usuario y contraseña.
    Devuelve (access_token, user_dict_del_login, None) si OK, o (None, None, mensaje_error) si falla.
    """
    base = getattr(settings, "INTRANET_API_BASE_URL", None) or ""
    if not base:
        return None, None, "No está configurada la URL de la intranet (INTRANET_API_BASE_URL)."
    url = f"{base}/api/v1/auth/login"
    try:
        r = requests.post(
            url,
            json={"username": username, "password": password},
            headers={"Content-Type": "application/json"},
            timeout=15,
        )
        data = r.json() if r.headers.get("content-type", "").startswith("application/json") else {}
        if r.status_code != 200:
            return None, None, data.get("error", "Credenciales inválidas. Por favor intentá nuevamente.")
        token = (data.get("access_token") or "").strip()
        if not token:
            return None, None, "La intranet no devolvió token."
        user_from_login = data.get("user") or {}
        return token, user_from_login, None
    except requests.RequestException as e:
        logger.warning("intranet login request error: %s", e)
        return None, None, "No se pudo conectar con la intranet. Revisá INTRANET_API_BASE_URL."
    except Exception as e:
        logger.warning("intranet login error: %s", e)
        return None, None, "Error al iniciar sesión. Intentá de nuevo."


def build_user_data_from_login(user_dict):
    """
    Construye el mismo formato que /public/me a partir del user devuelto por el login.
    Usado como fallback cuando /public/me no está disponible (proxy, URL, etc.).
    """
    if not user_dict:
        return None
    role = (user_dict.get("role") or "").strip() or "miembro"
    first = (user_dict.get("first_name") or "").strip()
    last = (user_dict.get("last_name") or "").strip()
    return {
        "usuario": (user_dict.get("username") or "").strip(),
        "tipo_de_usuario": role,
        "first_name": first,
        "last_name": last,
        "full_name": f"{first} {last}".strip() or user_dict.get("username", ""),
        "roles": [role],
        "is_staff": role in ("administrador", "secretaria"),
        "church_id": user_dict.get("church_id"),
    }


def fetch_me_from_intranet(access_token):
    """
    Llama a GET /api/v1/public/me con el token y devuelve el dict del usuario
    o None si falla.
    """
    base = getattr(settings, "INTRANET_API_BASE_URL", None) or ""
    if not base:
        return None
    url = f"{base}/api/v1/public/me"
    try:
        r = requests.get(
            url,
            headers={"Authorization": f"Bearer {(access_token or '').strip()}"},
            timeout=10,
        )
        if r.status_code != 200:
            logger.warning("intranet fetch_me status %s url=%s", r.status_code, url)
            return None
        return r.json()
    except Exception as e:
        logger.warning("intranet fetch_me error: %s url=%s", e, url)
        return None


def get_intranet_user(request):
    """
    Devuelve el dict del usuario intranet desde la sesión, o None.
    Esperado: request.session["intranet_user"] con keys como
    usuario, roles, church_id, is_staff, first_name, last_name, full_name.
    """
    return request.session.get("intranet_user")


def ensure_intranet_user_for_edit(request):
    """
    Si hay token guardado pero el usuario de sesión no tiene church_id (p. ej. fallback
    cuando /public/me dio 401), intenta refrescar desde /public/me una vez.
    Actualiza request.session["intranet_user"] si se obtienen datos nuevos.
    Devuelve el intranet_user actual (puede ser el de sesión o el refrescado).
    """
    user = request.session.get("intranet_user")
    token = request.session.get("intranet_access_token")
    if not token:
        return user
    # Refrescar si falta church_id y es pastor (necesitamos church_id para can_edit)
    roles = (user or {}).get("roles") or []
    need_refresh = not user or (
        (("pastorado" in roles) or ("pastor" in roles))
        and user.get("church_id") is None
    )
    if not need_refresh:
        return user
    fresh = fetch_me_from_intranet(token)
    if fresh:
        request.session["intranet_user"] = fresh
        return fresh
    return user


def can_edit_church_site(iglesia_page, intranet_user):
    """
    True si el usuario intranet puede editar la página "sitio" de esta iglesia.
    - Secretaría y administrador: pueden editar todas.
    - Pastor: solo la iglesia cuyo intranet_id coincide con su church_id.
    - Múltiples roles: se evalúa si tiene alguno de los anteriores.
    """
    if not intranet_user:
        return False
    roles = intranet_user.get("roles") or []
    # Aceptar "secretaria" (con y sin tilde por si la API devuelve distinto)
    if "administrador" in roles or "secretaria" in roles or "secretaría" in roles:
        return True
    if "pastorado" in roles or "pastor" in roles:
        church_id = intranet_user.get("church_id")
        if church_id is not None and iglesia_page.intranet_id is not None:
            if iglesia_page.intranet_id == church_id:
                return True
    return False
