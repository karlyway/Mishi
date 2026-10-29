from django.test import TestCase, Client
from django.urls import reverse

class MishiViewsTestCase(TestCase):
    def setUp(self):
        self.client = Client()

    def test_dashboard_view(self):
        response = self.client.get(reverse('dashboard'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'dashboard.html')
        self.assertTemplateUsed(response, 'base.html')
        self.assertContains(response, 'mishi')
        self.assertContains(response, 'Límite diario recomendado')

    def test_registro_view(self):
        response = self.client.get(reverse('registro'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'registro.html')
        self.assertContains(response, 'Registrar Movimiento')
        self.assertContains(response, 'Alimentación')

    def test_historial_view(self):
        response = self.client.get(reverse('historial'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'historial.html')
        self.assertContains(response, 'Historial Financiero')
        self.assertContains(response, 'GASTOS HORMIGA')

    def test_metas_view(self):
        response = self.client.get(reverse('metas'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'metas.html')
        self.assertContains(response, 'Metas de Ahorro y Préstamos')
