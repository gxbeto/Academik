from django.test import TestCase
from django.urls import reverse

from accounts.models import Rol, Usuario


class AuthenticationFlowTests(TestCase):
    def setUp(self):
        self.rol, _ = Rol.objects.get_or_create(
            nombre=Rol.Nombres.ADMINISTRADOR,
            defaults={"descripcion": "Acceso completo"},
        )
        self.usuario = Usuario.objects.create_user(
            username="admin",
            password="admin12345",
            rol=self.rol,
            activo=True,
        )

    def test_home_redirects_to_login_when_not_authenticated(self):
        response = self.client.get(reverse("inicio"))

        self.assertRedirects(response, "/login/?next=/")

    def test_login_redirects_to_home(self):
        response = self.client.post(
            reverse("login"),
            {
                "username": "admin",
                "password": "admin12345",
            },
        )

        self.assertRedirects(response, reverse("inicio"))

    def test_authenticated_user_can_open_home(self):
        self.client.force_login(self.usuario)

        response = self.client.get(reverse("inicio"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Gestiona la informacion escolar desde un solo lugar.")
