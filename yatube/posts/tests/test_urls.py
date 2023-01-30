from ..models import Group, Post
from django.contrib.auth import get_user_model
from django.test import TestCase, Client
from http import HTTPStatus
from django.urls import reverse
from django.core.cache import cache

User = get_user_model()


class PostURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='UserTest')
        cls.group = Group.objects.create(
            title='Группа для теста Urls',
            slug='urls_slug',
            description='Описание группы Urls'
        )
        cls.post = Post.objects.create(
            text='Тестовый пост 1',
            author=cls.user
        )
        cls.urls = [
            reverse('posts:index'),
            reverse(
                'posts:group_list',
                kwargs={'slug': PostURLTests.group.slug}
            ),
            reverse(
                'posts:profile',
                kwargs={'username': PostURLTests.user}
            ),
            reverse(
                'posts:post_detail',
                kwargs={'post_id': PostURLTests.post.id}
            ),
        ]
        cls.templates_names_address = {
            reverse('posts:index'): 'posts/index.html',
            reverse(
                'posts:group_list',
                kwargs={'slug': PostURLTests.group.slug}
            ): 'posts/group_list.html',
            reverse(
                'posts:profile',
                kwargs={'username': PostURLTests.user}
            ): 'posts/profile.html',
            reverse(
                'posts:post_detail',
                kwargs={'post_id': PostURLTests.post.id}
            ): 'posts/post_detail.html',
            reverse('posts:post_create'): 'posts/create_post.html',
            reverse(
                'posts:post_edit',
                kwargs={'post_id': PostURLTests.post.id}
            ): 'posts/create_post.html',
        }

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        cache.clear()

    def test_all_urls_for_all_users(self):
        """
        Главная страница, страница группы, страница профиля,
        страница с подробностями о посте, доступны любому пользователю.
        """
        for address in self.urls:
            with self.subTest(address):
                responce = self.guest_client.get(address)
                self.assertEqual(responce.status_code, HTTPStatus.OK)

    def test_create_post_url_for_authorized_user(self):
        """Страница с созданием поста доступна авторизованному пользователю."""
        responce = self.authorized_client.get(reverse(
            'posts:post_create'
        ))
        self.assertEqual(responce.status_code, HTTPStatus.OK)

    def test_edit_post_url_for_author(self):
        """Страница с редактированием поста доступна только автору поста."""
        responce = self.authorized_client.get(reverse(
            'posts:post_edit',
            kwargs={'post_id': PostURLTests.post.id}
        ))
        self.assertEqual(responce.status_code, HTTPStatus.OK)

    def test_create_post_url_redirect_anonymus_user(self):
        """
        Страница с созданием поста перенаправит на
        залогинивание анонимного пользователя.
        """
        responce = self.guest_client.get('/create/', follow=True)
        self.assertRedirects(responce, '/auth/login/?next=/create/')

    def test_urls_used_is_corrected_templates(self):
        """Url адрес - использует соответствующий ему шаблон."""
        for address, template in self.templates_names_address.items():
            with self.subTest(address=address):
                response = self.authorized_client.get(address)
                self.assertTemplateUsed(response, template)

    def test_url_not_available(self):
        """Ошибка о несуществующей страницы."""
        responce = self.guest_client.get('/not_available_url/')
        self.assertEqual(responce.status_code, HTTPStatus.NOT_FOUND)
