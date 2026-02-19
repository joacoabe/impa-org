from django import template
from wagtail.models import Site

register = template.Library()


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
