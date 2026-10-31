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
        self.assertContains(response, 'Mishi')
        self.assertContains(response, 'Limite diario recomendado')

    def test_registro_view(self):
        response = self.client.get(reverse('registro'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'registro.html')
        self.assertContains(response, 'Registrar movimiento')
        self.assertContains(response, 'Alimentacion')

    def test_historial_view(self):
        response = self.client.get(reverse('historial'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'historial.html')
        self.assertContains(response, 'Historial de transacciones')

    def test_metas_view(self):
        response = self.client.get(reverse('metas'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'metas.html')
        self.assertContains(response, 'Metas de ahorro')
