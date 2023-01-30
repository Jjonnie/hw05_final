from django.contrib.auth import get_user_model
from django.test import Client, TestCase, override_settings
from django.urls import reverse
from ..models import Group, Post, Follow
from django import forms
from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
import tempfile
import shutil
from django.core.cache import cache


User = get_user_model()

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class ViewTemplatesTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='UserTest')
        cls.group = Group.objects.create(
            title='Группа для теста Views',
            slug='views_slug',
            description='Описание группы Views'
        )
        small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        uploaded = SimpleUploadedFile(
            name='image.gif',
            content=small_gif,
            content_type='image/gif',
        )
        cls.post = Post.objects.create(
            text='Тестовый текст Views',
            author=cls.user,
            group=cls.group,
            image=uploaded,
        )
        cls.templates_names_address = {
            reverse('posts:index'): 'posts/index.html',
            reverse(
                'posts:group_list',
                kwargs={'slug': ViewTemplatesTests.group.slug}
            ): 'posts/group_list.html',
            reverse(
                'posts:profile',
                kwargs={'username': ViewTemplatesTests.user}
            ): 'posts/profile.html',
            reverse(
                'posts:post_detail',
                kwargs={'post_id': ViewTemplatesTests.post.id}
            ): 'posts/post_detail.html',
            reverse('posts:post_create'): 'posts/create_post.html',
            reverse(
                'posts:post_edit',
                kwargs={'post_id': ViewTemplatesTests.post.id}
            ): 'posts/create_post.html',
        }

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        self.client = Client()
        self.nobody = User.objects.create_user(username='NoNameUser')
        self.client.force_login(self.nobody)
        cache.clear()

    def test_urls_used_is_corrected_templates(self):
        """Url адрес - использует соответствующий ему шаблон."""
        for address, template in self.templates_names_address.items():
            with self.subTest(address=address):
                response = self.authorized_client.get(address)
                self.assertTemplateUsed(response, template)

    def test_index_correct_context(self):
        """Главная страница index передает корректный context."""
        response = self.authorized_client.get(reverse('posts:index'))
        post_obj = response.context['page_obj'][0]
        text_0 = post_obj.text
        author_0 = post_obj.author
        group_0 = post_obj.group
        image_0 = post_obj.image
        self.assertEqual(text_0, ViewTemplatesTests.post.text)
        self.assertEqual(author_0, ViewTemplatesTests.user)
        self.assertEqual(group_0, ViewTemplatesTests.group)
        self.assertEqual(image_0, self.post.image)

    def test_group_list_show_correct_context_and_filter_group(self):
        """Шаблон group_list сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse(
            'posts:group_list', kwargs={'slug': self.group.slug}))
        post_obj = response.context['page_obj'][0]
        author_0 = post_obj.author
        text_0 = post_obj.text
        group_0 = post_obj.group
        image_0 = post_obj.image
        self.assertEqual(author_0, self.user)
        self.assertEqual(text_0, self.post.text)
        self.assertEqual(group_0, self.post.group)
        self.assertEqual(image_0, self.post.image)
        self.assertEqual(response.context['group'], self.group)

    def test_group_list_show_correct_context_and_filter_profile(self):
        """Шаблон profile сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse(
            'posts:profile', kwargs={'username': self.user}))
        post_obj = response.context['page_obj'][0]
        author_0 = post_obj.author
        text_0 = post_obj.text
        group_0 = post_obj.group
        image_0 = post_obj.image
        self.assertEqual(author_0, self.user)
        self.assertEqual(text_0, self.post.text)
        self.assertEqual(group_0, self.post.group)
        self.assertEqual(image_0, self.post.image)
        self.assertEqual(response.context['author'], self.post.author)

    def test_post_detail_show_correct_context(self):
        """Шаблон post_detail сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse(
            'posts:post_detail', kwargs={'post_id': self.post.id}))
        post_obj = response.context['post']
        author_0 = post_obj.author
        text_0 = post_obj.text
        group_0 = post_obj.group
        image_0 = post_obj.image
        self.assertEqual(author_0, self.user)
        self.assertEqual(text_0, self.post.text)
        self.assertEqual(group_0, self.post.group)
        self.assertEqual(image_0, self.post.image)

    def test_create_and_edit_post_show_correct_context_and_form(self):
        """Шаблон create_post сформирован с правильным контекстом."""
        urls = (
            reverse('posts:post_create'),
            reverse('posts:post_edit', kwargs={'post_id': self.post.id})
        )
        form_fields = {
            'group': forms.fields.ChoiceField,
            'text': forms.fields.CharField,
        }
        for url in urls:
            for value, expected in form_fields.items():
                with self.subTest(value=value, url=url):
                    response = self.authorized_client.get(url)
                    form_field = response.context['form'].fields[value]
                    self.assertIsInstance(form_field, expected)

    def test_post_in_select_group(self):
        """Проверка наличия поста с выбранной группой."""
        urls = (
            reverse('posts:index'),
            reverse('posts:group_list', kwargs={'slug': self.group.slug}),
            reverse('posts:profile', kwargs={'username': self.user}),
        )
        for url in urls:
            with self.subTest(url=url):
                response = self.authorized_client.get(url)
                page_obj = response.context['page_obj']
                self.assertIn(self.post, page_obj)

    def test_post_have_correct_group(self):
        """Проверка на пренадлежность группы."""
        post = Post.objects.create(
            text='тестовый текст 1',
            author=self.user,
        )
        response = self.authorized_client.get(reverse(
            'posts:group_list', kwargs={'slug': self.group.slug}))
        page_obj = response.context['page_obj']
        self.assertNotIn(post, page_obj)

    def test_cache_index_page(self):
        """Проверка кеша на станице index."""
        post = Post.objects.create(
            text='Пост для теста кеша',
            author=self.user)
        add_content = self.authorized_client.get(
            reverse('posts:index')).content
        post.delete()
        delete_content = self.authorized_client.get(
            reverse('posts:index')).content
        self.assertEqual(add_content, delete_content)
        cache.clear()
        clear_cache_content = self.authorized_client.get(
            reverse('posts:index')).content
        self.assertNotEqual(add_content, clear_cache_content)

    def test_authorized_user_can_follow_other_user(self):
        """
        Авторизованный пользователь может подписываться
        на других пользователей.
        """
        self.response = (self.client.get(
            reverse('posts:profile_follow', args={self.user})))
        self.assertIs(
            Follow.objects.filter(user=self.nobody, author=self.user).exists(),
            True
        )

    def test_authorized_user_can_unfollow_other_user(self):
        """
        Авторизованный пользователь может одписываться
        от других пользователей.
        """
        self.response = (self.client.get(
            reverse('posts:profile_follow', args={self.user})))
        self.response = (self.client.get(
            reverse('posts:profile_unfollow', args={self.user})))
        self.assertIs(
            Follow.objects.filter(user=self.nobody, author=self.user).exists(),
            False
        )

    def test_new_post_watch_for_follow_user(self):
        """
        Новая запись пользователя появляется в ленте тех,
        кто на него подписан.
        """
        Follow.objects.create(user=self.nobody, author=self.user)
        response = (self.client.get(reverse('posts:follow_index')))
        self.assertIn(self.post, response.context['page_obj'])

    def test_new_post_not_watch_unfollow_user(self):
        """
        Новая запись пользователя не появляется в ленте тех,
        кто на него не подписан.
        """
        User.objects.create_user(username='user_test')
        self.client.login(username='user_test')
        response = (self.client.get(reverse('posts:follow_index')))
        self.assertNotIn(self.post, response.context['page_obj'])


class PaginatorViewsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='Группа для проверки Paginator',
            slug='paginator_slug',
            description='Описание группы Paginator'
        )

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        cache.clear()

    def test_paginator_correct_context(self):
        """
        Шаблоны: index, group_list, profile -
        сформированы с правильным Paginator.
        """
        post_list = []
        for i in range(0, 14):
            new_post = Post(
                author=PaginatorViewsTest.user,
                text='Тестовый пост ' + str(i),
                group=PaginatorViewsTest.group
            )
            post_list.append(new_post)
        Post.objects.bulk_create(post_list)
        paginator_urls = {
            'index': reverse('posts:index'),
            'group': reverse(
                'posts:group_list',
                kwargs={'slug': PaginatorViewsTest.group.slug}
            ),
            'profile': reverse(
                'posts:profile',
                kwargs={'username': PaginatorViewsTest.user.username}
            )
        }
        for paginator, paginator_urls in paginator_urls.items():
            with self.subTest(paginator=paginator):
                page_1 = self.authorized_client.get(paginator_urls)
                page_2 = self.authorized_client.get(
                    paginator_urls + '?page=2'
                )
                self.assertEqual(len(
                    page_1.context['page_obj']),
                    10
                )
                self.assertEqual(len(
                    page_2.context['page_obj']),
                    4
                )
