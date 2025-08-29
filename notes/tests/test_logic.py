from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse
from pytils.translit import slugify

from notes.forms import WARNING
from notes.models import Note

User = get_user_model()


class TestLogic(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.reader = User.objects.create(username='Читатель')
        cls.reader_client = Client()
        cls.reader_client.force_login(cls.reader)
        cls.author = User.objects.create(username='Автор')
        cls.author_client = Client()
        cls.author_client.force_login(cls.author)
        cls.note = Note.objects.create(title='Заголовок',
                                       text='Текст',
                                       author=cls.author)
        cls.form_data = {'title': 'Новый заголовок',
                         'text': 'Новый текст',
                         'slug': 'new-slug', }

    def test_user_can_create_note(self):
        Note.objects.all().delete()
        self.assertRedirects(
            self.reader_client.post(reverse('notes:add'), data=self.form_data),
            reverse('notes:success'))
        assert Note.objects.count() == 1
        new_note = Note.objects.get()
        assert new_note.title == self.form_data['title']
        assert new_note.text == self.form_data['text']
        assert new_note.slug == self.form_data['slug']
        assert new_note.author == self.reader

    def test_anonymous_user_cant_create_note(self):
        Note.objects.all().delete()
        url = reverse('notes:add')
        self.assertRedirects(self.client.post(url, data=self.form_data),
                             f'{reverse('users:login')}?next={url}')
        assert Note.objects.count() == 0

    def test_not_unique_slug(self):
        self.form_data['slug'] = self.note.slug
        self.assertFormError(
            self.reader_client.post(
                reverse('notes:add'), data=self.form_data
            ).context['form'], 'slug', errors=(self.note.slug + WARNING))
        assert Note.objects.count() == 1

    def test_empty_slug(self):
        Note.objects.all().delete()
        self.form_data.pop('slug')
        self.assertRedirects(
            self.reader_client.post(reverse('notes:add'), data=self.form_data),
            reverse('notes:success'))
        assert Note.objects.count() == 1
        new_note = Note.objects.get()
        assert new_note.slug == slugify(self.form_data['title'])

    def test_author_can_edit_note(self):
        self.assertRedirects(
            self.author_client.post(
                reverse('notes:edit', args=(self.note.slug,)), self.form_data),
            reverse('notes:success'))
        self.note.refresh_from_db()
        assert self.note.title == self.form_data['title']
        assert self.note.text == self.form_data['text']
        assert self.note.slug == self.form_data['slug']

    def test_other_user_cant_edit_note(self):
        assert self.reader_client.post(
            reverse('notes:edit', args=(self.note.slug,)),
            self.form_data).status_code == HTTPStatus.NOT_FOUND
        note_from_db = Note.objects.get(id=self.note.id)
        assert self.note.title == note_from_db.title
        assert self.note.text == note_from_db.text
        assert self.note.slug == note_from_db.slug

    def test_author_can_delete_note(self):
        url = reverse('notes:delete', args=(self.note.slug,))
        response = self.author_client.post(url)
        self.assertRedirects(response, reverse('notes:success'))
        assert Note.objects.count() == 0

    def test_other_user_cant_delete_note(self):
        url = reverse('notes:delete', args=(self.note.slug,))
        response = self.reader_client.post(url)
        assert response.status_code == HTTPStatus.NOT_FOUND
        assert Note.objects.count() == 1
