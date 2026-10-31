from django.test import TestCase, Client
from django.urls import reverse

# Pruebas para verificar que todas las paginas carguen correctamente (Codigo HTTP 200)
class MishiViewsTestCase(TestCase):
    def setUp(self):
        self.client = Client()

    # Comprueba la pagina de presentacion
    def test_landing_view(self):
        response = self.client.get(reverse('landing'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'landing.html')
        self.assertContains(response, 'Control de gastos para estudiantes universitarios')

    # Comprueba el formulario de login
    def test_login_view(self):
        response = self.client.get(reverse('login'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'login.html')
        self.assertContains(response, 'Iniciar sesion')

    # Comprueba el formulario de registro de usuario
    def test_registro_usuario_view(self):
        response = self.client.get(reverse('registro_usuario'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'registro_usuario.html')
        self.assertContains(response, 'Crear cuenta de estudiante')

    # Comprueba la pantalla de inicio del panel
    def test_dashboard_view(self):
        response = self.client.get(reverse('dashboard'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'dashboard.html')
        self.assertContains(response, 'Panel principal')

    # Comprueba el formulario para registrar un movimiento
    def test_movimiento_view(self):
        response = self.client.get(reverse('movimiento'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'registro.html')
        self.assertContains(response, 'Registrar movimiento')

    # Comprueba la tabla de historial
    def test_historial_view(self):
        response = self.client.get(reverse('historial'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'historial.html')
        self.assertContains(response, 'Historial de transacciones')

    # Comprueba la seccion de metas y prestamos
    def test_metas_view(self):
        response = self.client.get(reverse('metas'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'metas.html')
        self.assertContains(response, 'Metas de ahorro')
