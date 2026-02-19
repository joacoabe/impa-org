"""
Formulario de login del admin que usa nombre de usuario (no correo).
Los usuarios se identifican y se mueven en el admin por username.
"""
from django import forms
from django.utils.translation import gettext_lazy as _

from wagtail.admin.forms.auth import LoginForm as WagtailLoginForm


class UsernameLoginForm(WagtailLoginForm):
    """
    Login por nombre de usuario (no por correo).
    Los usuarios se identifican y se mueven en el admin por username.
    """
    username = forms.CharField(
        max_length=254,
        label=_("Nombre de usuario"),
        widget=forms.TextInput(attrs={"autofocus": ""}),
    )

    def __init__(self, request=None, *args, **kwargs):
        super().__init__(request=request, *args, **kwargs)
        self.fields["username"].label = _("Nombre de usuario")
        self.fields["username"].widget.attrs["placeholder"] = _("Ingresá tu nombre de usuario")
