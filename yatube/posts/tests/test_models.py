from django.contrib.auth import get_user_model
from django.test import TestCase
from ..models import Group, Post

User = get_user_model()


class PostModelTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='Группа для теста модели',
            slug='model_slug',
            description='описание группы Модели',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый пост 1',
        )

    def test_models_group_have_correct_object_names(self):
        """Проверяем, что у модели Group корректно работает __str__."""
        group = PostModelTest.group
        expected_group = group.title
        self.assertEqual(expected_group, str(group))

    def test_models_post_have_correct_object_names(self):
        """Проверяем, что у модели Post корректно работает __str__."""
        post = PostModelTest.post
        expected_post = post.text[:15]
        self.assertEqual(expected_post, str(post))
