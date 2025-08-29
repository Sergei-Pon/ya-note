from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from notes.models import Note


User = get_user_model()


class TestRoutes(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.reader = User.objects.create(username='Читатель')
        cls.author = User.objects.create(username='Автор')
        cls.note = Note.objects.create(title='Заголовок',
                                       text='Текст',
                                       author=cls.author)

    def test_pages_availability_for_anonymous_user(self):
        url_names = ('notes:home', 'users:login',
                     'users:logout', 'users:signup',)
        for url_name in url_names:
            with self.subTest(url_name=url_name):
                url = reverse(url_name)
                if url_name != 'users:logout':
                    response = self.client.get(url)
                else:
                    self.client.post(url)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_pages_availability_for_auth_user(self):
        self.client.force_login(self.reader)
        url_names = ('notes:list', 'notes:add', 'notes:success',)
        for url_name in url_names:
            with self.subTest(url_name=url_name):
                self.assertEqual(self.client.get(
                    reverse(url_name)).status_code, HTTPStatus.OK)

    def test_pages_availability_for_different_users(self):
        users_statuses = ((self.author, HTTPStatus.OK),
                          (self.reader, HTTPStatus.NOT_FOUND),)
        url_names = ('notes:detail', 'notes:edit', 'notes:delete',)
        for user, status in users_statuses:
            self.client.force_login(user)
            for url_name in url_names:
                with self.subTest(url_name=url_name):
                    assert self.client.get(
                        reverse(url_name, args=(self.note.slug,))
                    ).status_code == status

    def test_redirects(self):
        names_args = (('notes:detail', (self.note.slug,)),
                      ('notes:edit', (self.note.slug,)),
                      ('notes:delete', (self.note.slug,)),
                      ('notes:add', None),
                      ('notes:success', None),
                      ('notes:list', None),)
        login_url = reverse('users:login')
        for name, arg in names_args:
            with self.subTest(name=name, arg=arg):
                url = reverse(name, args=arg)
                self.assertRedirects(self.client.get(url),
                                     f'{login_url}?next={url}')
