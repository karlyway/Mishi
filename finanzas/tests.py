from decimal import Decimal
from datetime import date
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from .models import Usuario, Categoria, Transaccion, MetaAhorro, Prestamo


class MishiViewsTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        User = get_user_model()
        self.user = User.objects.create_user(
            username='estudiante@curn.edu.co',
            email='estudiante@curn.edu.co',
            password='password123'
        )
        self.perfil = Usuario.objects.create(
            cuenta=self.user,
            nombre='Karla Estudiante',
            universidad='Corporación Universitaria Rafael Núñez',
            frecuencia='quincenal',
            mesada=Decimal('300000.00')
        )
        self.categoria = Categoria.objects.create(nombre='Alimentación')

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

    # Comprueba la pantalla de inicio del panel autenticado
    def test_dashboard_view(self):
        self.client.force_login(self.user)
        response = self.client.get(reverse('dashboard'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'dashboard.html')
        self.assertContains(response, 'Panel principal')

    # Comprueba el formulario para registrar un movimiento y su creacion
    def test_movimiento_view(self):
        self.client.force_login(self.user)
        response = self.client.get(reverse('movimiento'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'registro.html')
        self.assertContains(response, 'Registrar movimiento')

        post_res = self.client.post(reverse('movimiento'), {
            'tipo': 'gasto',
            'monto': '12000',
            'categoria': self.categoria.idCategoria,
            'descripcion': 'Almuerzo universitario',
            'fecha': date.today().isoformat(),
        })
        self.assertRedirects(post_res, reverse('dashboard'))
        self.assertEqual(Transaccion.objects.filter(idUsuario=self.perfil).count(), 1)

    # Comprueba la tabla de historial
    def test_historial_view(self):
        self.client.force_login(self.user)
        response = self.client.get(reverse('historial'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'historial.html')
        self.assertContains(response, 'Historial de transacciones')

    # Comprueba la seccion de metas y prestamos
    def test_metas_view(self):
        self.client.force_login(self.user)
        response = self.client.get(reverse('metas'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'metas.html')
        self.assertContains(response, 'Metas de ahorro')
