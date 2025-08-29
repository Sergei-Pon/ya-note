from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from notes.forms import NoteForm
from notes.models import Note


User = get_user_model()


class TestContent(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.reader = User.objects.create(username='Читатель')
        cls.author = User.objects.create(username='Автор')
        cls.note = Note.objects.create(title='Заголовок',
                                       text='Текст',
                                       author=cls.author)

    def test_notes_list_for_different_users(self):
        users_and_note_in_list = ((self.author, True),
                                  (self.reader, False),)
        for user, note_in_list in users_and_note_in_list:
            with self.subTest(user=user, note_in_list=note_in_list):
                self.client.force_login(user)
                assert (self.note in self.client.get(
                    reverse('notes:list')).context['object_list']
                ) is note_in_list

    def test_pages_contains_form(self):
        self.client.force_login(self.author)
        names_args = (('notes:add', None),
                      ('notes:edit', (self.note.slug,)),)
        for name, arg in names_args:
            with self.subTest(name=name, arg=arg):
                response = self.client.get(reverse(name, args=arg))
                assert 'form' in response.context
                assert isinstance(response.context['form'], NoteForm)
