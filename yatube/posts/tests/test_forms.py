from http import HTTPStatus
from django.contrib.auth import get_user_model
from django.test import Client, TestCase, override_settings
from django.urls import reverse
from ..models import Group, Post, Comment
from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
import shutil
import tempfile

User = get_user_model()

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostFormTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.author_post = User.objects.create_user(
            username='автор поста',
        )
        cls.group = Group.objects.create(
            title='Группа для теста Form',
            slug='form_slug',
            description='Описание группы Form',
        )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.guest_user = Client()
        self.authorized_user = Client()
        self.authorized_user.force_login(self.author_post)

    def test_authorized_user_can_create_post(self):
        """Проверка возможности создания поста авторизованным пользователем."""
        count_posts = Post.objects.count()
        small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        uploaded = SimpleUploadedFile(
            name='small.gif',
            content=small_gif,
            content_type='image/gif'
        )
        form_data = {
            'text': 'Текст поста',
            'group': self.group.id,
            'image': uploaded,
        }
        response = self.authorized_user.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True
        )
        post = Post.objects.latest('id')
        self.assertRedirects(
            response,
            reverse(
                'posts:profile',
                kwargs={'username': self.author_post.username})
        )
        self.assertEqual(Post.objects.count(), count_posts + 1)
        self.assertEqual(post.text, form_data['text'])
        self.assertEqual(post.author, self.author_post)
        self.assertEqual(post.group_id, form_data['group'])
        self.assertEqual(post.image.name, 'posts/small.gif')

    def test_authorized_user_can_edit_post(self):
        """Проверка редактирования записи авторизированным пользователем."""
        post = Post.objects.create(
            text='Тестовый пост Form',
            author=self.author_post,
            group=self.group,
        )
        form_data = {
            'text': 'Редактирование Form',
            'group': self.group.id,
        }
        response = self.authorized_user.post(
            reverse(
                'posts:post_edit',
                args=[post.id]),
            data=form_data,
            follow=True
        )
        self.assertRedirects(
            response,
            reverse('posts:post_detail', kwargs={'post_id': post.id})
        )
        self.assertEqual(response.status_code, HTTPStatus.OK)
        post = Post.objects.latest('id')
        self.assertTrue(post.text, form_data['text'])
        self.assertTrue(post.author, self.author_post)
        self.assertTrue(post.group_id, form_data['group'])


class CommentFormTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.username = 'auth'
        cls.user = User.objects.create_user(username=cls.username)
        cls.slug = 'test-slug'
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug=cls.slug,
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый текст поста',
        )
        cls.comment = Comment.objects.create(
            author=cls.user,
            post=cls.post,
            text='Тестовый комментарий поста',
        )
        cls.form = Comment()

    def setUp(self):
        self.authorized_username = 'Bob'
        self.guest_client = Client()
        self.user = User.objects.create_user(username=self.authorized_username)
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_authorized_client_can_create_comment(self):
        """Авторизованный пользователь может писать комментарии."""
        count_comments = Comment.objects.count()
        text_comment = 'Новый комент'
        form_data = {
            'text': text_comment,
        }
        response = self.authorized_client.post(
            reverse('posts:add_comment',
                    args=[self.post.id, ]),
            data=form_data,
            follow=True,
        )
        self.assertRedirects(response, reverse('posts:post_detail',
                                               args=[self.post.id]))
        self.assertEqual(Comment.objects.count(), count_comments + 1)
        self.assertTrue(Comment.objects.filter(text=text_comment).exists())
        response = self.authorized_client.get(
            reverse('posts:post_detail',
                    args=[self.post.id])).context['comments'][0]
        self.assertEqual(text_comment, response.text)

    def test_guest_client_can_not_create_comment(self):
        """Неавторизованный пользователь не может писать комментарии."""
        count_comments = Comment.objects.count()
        text_comment = 'Новый коммент 2'
        form_data = {
            'text': text_comment,
        }
        response = self.guest_client.post(
            reverse('posts:add_comment',
                    args=[self.post.id]),
            data=form_data,
            follow=True,
        )
        self.assertRedirects(response,
                             '/auth/login/?next=%2Fposts%2F1%2Fcomment%2F')
        self.assertEqual(Comment.objects.count(), count_comments)
        self.assertFalse(Comment.objects.filter(text=text_comment).exists())
