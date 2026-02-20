"""
Vistas para el sitio imparg.org (Django).
- Página "sitio" de cada iglesia: /iglesias/<slug>/sitio/
- Edición con permisos intranet (secretaría ≈ admin, pastor = solo su iglesia).
- Auth intranet: guardar token en sesión.
"""
import os
import re
import uuid
from types import SimpleNamespace
from django.shortcuts import render, redirect
from django.http import HttpResponseForbidden, JsonResponse
from django.views.decorators.http import require_http_methods, require_GET, require_POST
from django.http import Http404
from django.conf import settings
from django.views.decorators.csrf import ensure_csrf_cookie
from wagtail.models import Page

from home.models import IglesiasIndexPage, IglesiaPage, ChurchSiteContent
from home.intranet_auth import (
    fetch_me_from_intranet,
    get_intranet_user,
    can_edit_church_site,
    ensure_intranet_user_for_edit,
)


def _fake_page(title, description=""):
    """Objeto tipo página para templates que esperan page en context."""
    return SimpleNamespace(seo_title=title, title=title, search_description=description)


@require_GET
def entrar(request):
    """
    Página de acceso unificado: elegir entre Panel de administración (Wagtail)
    o Entrar con la intranet (para editar sitios de iglesias).
    """
    context = {
        "page": _fake_page("Entrar"),
        "intranet_user": get_intranet_user(request),
    }
    return render(request, "home/entrar.html", context)


def _get_iglesia_by_slug(slug):
    """Devuelve la IglesiaPage viva con slug dado (hija del índice iglesias) o None."""
    index = IglesiasIndexPage.objects.live().first()
    if not index:
        return None
    child = Page.objects.child_of(index).filter(slug=slug).live().first()
    if not child:
        return None
    return child.specific


@require_GET
def iglesia_sitio(request, slug):
    """Vista pública: /iglesias/<slug>/sitio/ — muestra la página propia de la iglesia."""
    iglesia = _get_iglesia_by_slug(slug)
    if not iglesia:
        raise Http404("Iglesia no encontrada")
    try:
        content = iglesia.site_content
    except ChurchSiteContent.DoesNotExist:
        content = None
    intranet_user = get_intranet_user(request)
    can_edit = can_edit_church_site(iglesia, intranet_user)
    context = {
        "page": iglesia,
        "iglesia": iglesia,
        "content": content,
        "can_edit": can_edit,
        "intranet_user": intranet_user,
    }
    response = render(request, "home/iglesia_sitio.html", context)
    # Evitar caché para que se vean los cambios al guardar
    response["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
    response["Pragma"] = "no-cache"
    response["Expires"] = "0"
    return response


@require_http_methods(["GET", "POST"])
def iglesia_sitio_editar(request, slug):
    """Editar contenido del sitio de la iglesia. Requiere permiso (secretaría/admin o pastor de esta iglesia)."""
    iglesia = _get_iglesia_by_slug(slug)
    if not iglesia:
        raise Http404("Iglesia no encontrada")
    intranet_user = ensure_intranet_user_for_edit(request) or get_intranet_user(request)
    if not intranet_user:
        from django.urls import reverse
        next_url = reverse("home:iglesia_sitio_editar", kwargs={"slug": slug})
        return redirect(f"{reverse('home:auth_intranet')}?next={next_url}")
    if not can_edit_church_site(iglesia, intranet_user):
        return HttpResponseForbidden("No tenés permiso para editar esta página.")

    if request.method == "POST":
        body = request.POST.get("body", "")
        # Máximo 5 imágenes por página (MAX_FOTOS_POR_PAGINA)
        img_count = len(re.findall(r"<img\s", body, re.I))
        if img_count > MAX_FOTOS_POR_PAGINA:
            from django.contrib import messages
            messages.error(
                request,
                f"La página puede tener como máximo {MAX_FOTOS_POR_PAGINA} fotos. Actualmente tenés {img_count}. Eliminá algunas y guardá de nuevo.",
            )
            context = {
                "page": iglesia,
                "iglesia": iglesia,
                "content": ChurchSiteContent(iglesia_page=iglesia, body=body),
                "intranet_user": get_intranet_user(request),
            }
            return render(request, "home/iglesia_sitio_editar.html", context)
        content, _ = ChurchSiteContent.objects.get_or_create(
            iglesia_page=iglesia,
            defaults={"body": body},
        )
        content.body = body
        content.save(update_fields=["body"])
        from django.contrib import messages
        from django.urls import reverse
        import time
        messages.success(request, "Cambios guardados. Si no ves los cambios, actualizá con F5 o Ctrl+F5.")
        url = reverse("home:iglesia_sitio", kwargs={"slug": slug})
        return redirect(f"{url}?_={int(time.time())}")

    try:
        content = iglesia.site_content
    except ChurchSiteContent.DoesNotExist:
        content = None
    context = {
        "page": iglesia,
        "iglesia": iglesia,
        "content": content,
        "intranet_user": intranet_user,
    }
    return render(request, "home/iglesia_sitio_editar.html", context)


# Límites para fotos del sitio de la iglesia
MAX_FOTOS_POR_PAGINA = 5
MAX_TAMANO_FOTO_MB = 5
ALLOWED_IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif", ".webp"}


@require_POST
@ensure_csrf_cookie
def iglesia_sitio_subir_foto(request, slug):
    """Sube una foto para el sitio de la iglesia. Máx 5MB por archivo. Respuesta JSON con { url } o { error }."""
    iglesia = _get_iglesia_by_slug(slug)
    if not iglesia:
        return JsonResponse({"error": "Iglesia no encontrada"}, status=404)
    intranet_user = ensure_intranet_user_for_edit(request) or get_intranet_user(request)
    if not intranet_user:
        return JsonResponse({
            "error": "Tenés que iniciar sesión con la intranet para subir fotos. Entrá por «Entrar» y elegí «Sitio de las iglesias»."
        }, status=403)
    if not can_edit_church_site(iglesia, intranet_user):
        return JsonResponse({
            "error": "No tenés permiso para editar el sitio de esta iglesia. Si sos el pastor, cerrá sesión y volvé a entrar desde «Entrar»."
        }, status=403)

    archivo = request.FILES.get("foto") or request.FILES.get("file")
    if not archivo:
        return JsonResponse({"error": "No se envió ninguna imagen"}, status=400)

    # Validar tamaño (5 MB)
    if archivo.size > MAX_TAMANO_FOTO_MB * 1024 * 1024:
        return JsonResponse(
            {"error": f"Cada foto puede pesar hasta {MAX_TAMANO_FOTO_MB} MB. Esta pesa demasiado."},
            status=400,
        )

    # Validar que sea imagen
    ext = os.path.splitext(archivo.name or "")[1].lower()
    if ext not in ALLOWED_IMAGE_EXTENSIONS:
        return JsonResponse(
            {"error": "Solo se permiten imágenes (JPG, PNG, GIF, WebP)."},
            status=400,
        )
    content_type = (archivo.content_type or "").lower()
    if not content_type.startswith("image/"):
        return JsonResponse({"error": "El archivo no es una imagen válida"}, status=400)

    # Guardar en media/church_site_uploads/
    subdir = "church_site_uploads"
    upload_dir = os.path.join(settings.MEDIA_ROOT, subdir)
    os.makedirs(upload_dir, exist_ok=True)
    nombre = f"{uuid.uuid4().hex}{ext}"
    path = os.path.join(upload_dir, nombre)
    with open(path, "wb") as f:
        for chunk in archivo.chunks():
            f.write(chunk)

    url = f"{settings.MEDIA_URL.rstrip('/')}/{subdir}/{nombre}"
    return JsonResponse({"url": url})


@require_http_methods(["GET", "POST"])
def auth_intranet(request):
    """
    Iniciar sesión con la intranet para editar en imparg.org.
    - POST con username + password: llama a la API de la intranet y guarda sesión.
    - GET con ?token=... o POST con access_token: guarda sesión con ese token (sin pedir contraseña).
    """
    from home.intranet_auth import (
        login_intranet,
        fetch_me_from_intranet,
        build_user_data_from_login,
    )

    next_url = request.GET.get("next") or request.POST.get("next") or "/"
    ctx = {"page": _fake_page("Iniciar sesión"), "next": next_url}

    if request.method == "POST":
        username = (request.POST.get("username") or "").strip()
        password = request.POST.get("password") or ""
        token_from_form = request.POST.get("access_token") or request.POST.get("token") or ""

        login_user = None
        # Opción 1: usuario y contraseña (login contra la intranet)
        if username and password:
            token, login_user, err = login_intranet(username, password)
            if err:
                ctx["error"] = err
                ctx["username_value"] = username
                return render(request, "home/auth_intranet.html", ctx)
        elif token_from_form:
            token = token_from_form.strip()
        else:
            ctx["error"] = "Ingresá tu usuario y contraseña de la intranet, o pegá el token de acceso."
            return render(request, "home/auth_intranet.html", ctx)

        if not token:
            ctx["error"] = "Falta el token o las credenciales."
            return render(request, "home/auth_intranet.html", ctx)

        # Si entró con usuario/contraseña, usar los datos del login (incluye church_id).
        # No llamar a /public/me desde el servidor porque suele devolver 401 (token válido pero la intranet rechaza la petición desde imparg.org).
        if login_user:
            user_data = build_user_data_from_login(login_user)
        else:
            user_data = fetch_me_from_intranet(token)
        if not user_data:
            ctx["error"] = "Token inválido o expirado. Volvé a iniciar sesión en la intranet."
            ctx["username_value"] = username
            return render(request, "home/auth_intranet.html", ctx)

        request.session["intranet_user"] = user_data
        request.session["intranet_access_token"] = token
        return redirect(next_url)

    # GET: token en query (p. ej. redirección desde intranet)
    token = request.GET.get("token")
    if token:
        user_data = fetch_me_from_intranet(token)
        if user_data:
            request.session["intranet_user"] = user_data
            request.session["intranet_access_token"] = token
            return redirect(next_url)
        ctx["error"] = "Token inválido o expirado."
    ctx["next"] = next_url
    return render(request, "home/auth_intranet.html", ctx)


def auth_intranet_logout(request):
    """Cierra la sesión intranet en imparg.org."""
    request.session.pop("intranet_user", None)
    request.session.pop("intranet_access_token", None)
    next_url = request.GET.get("next", "/")
    return redirect(next_url)
