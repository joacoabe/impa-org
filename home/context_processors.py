"""Context processors para templates del sitio."""
from wagtail.models import Site


# Slugs que aparecen como tabs bajo el header (orden fijo)
TAB_SLUGS = ["iglesias", "noticias", "recursos", "radios", "contacto", "mapa"]


def site_menu(request):
    """Añade 'site_menu' (todos los hijos), 'site_nav' (institucionales) y 'site_tabs' (tabs)."""
    site = Site.objects.filter(is_default_site=True).first()
    if not site or not site.root_page_id:
        return {"site_menu": [], "site_nav": [], "site_tabs": []}
    try:
        children = list(site.root_page.get_children().live())
        by_slug = {c.slug: c for c in children}
        # Tabs: solo estas páginas, en el orden definido
        site_tabs = [by_slug[s] for s in TAB_SLUGS if s in by_slug]
        # Nav del header: el resto (Historia, Visión, Doctrina, Autoridades, etc.)
        tab_slugs_set = set(TAB_SLUGS)
        site_nav = [c for c in children if c.slug not in tab_slugs_set]
        return {"site_menu": children, "site_nav": site_nav, "site_tabs": site_tabs}
    except Exception:
        return {"site_menu": [], "site_nav": [], "site_tabs": []}
