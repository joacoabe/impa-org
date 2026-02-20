from django import template
from wagtail.models import Site

register = template.Library()


@register.simple_tag(takes_context=True)
def can_edit_iglesia_site(context):
    """
    True si el usuario de la intranet puede editar el sitio de la iglesia actual.
    Usar solo en templates de IglesiaPage (context tiene 'page').
    """
    request = context.get("request")
    page = context.get("page")
    if not request or not page:
        return False
    if not hasattr(page, "intranet_id"):
        return False
    from home.intranet_auth import get_intranet_user, can_edit_church_site

    user = get_intranet_user(request)
    return can_edit_church_site(page, user)


@register.filter
def path_startswith(path, prefix):
    """True si path es igual a prefix o es una subruta (path empieza con prefix/)."""
    if not prefix:
        return path == "/" or path == ""
    return path == prefix or (path.startswith(prefix) and (len(path) == len(prefix) or path[len(prefix) : len(prefix) + 1] == "/"))


@register.simple_tag
def get_site_menu():
    """Devuelve los hijos publicados de la página raíz para el menú."""
    site = Site.objects.filter(is_default_site=True).first()
    if not site or not site.root_page_id:
        return []
    try:
        return list(site.root_page.get_children().live())
    except Exception:
        return []
