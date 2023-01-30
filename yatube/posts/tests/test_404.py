from http import HTTPStatus
from django.test import Client, TestCase


class TestURL404(TestCase):

    def setUp(self):
        self.guest_client = Client()

    def test_urls_use_404_template(self):
        """Страница 404 отдает кастомный шаблон."""
        templates_url_names = {
            '/nonexisting_page/': 'core/404.html',
            '/group/error/': 'core/404.html',
        }
        for address, template in templates_url_names.items():
            with self.subTest(adress=address):
                response = self.guest_client.get(address)
                self.assertTemplateUsed(response, template)
                self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)
