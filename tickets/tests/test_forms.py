from django.test import TestCase
from django.contrib.auth.models import User
from tickets.forms import TicketForm, CommentForm, TicketStatusForm
from tickets.models import TicketType, Project


class TicketFormTest(TestCase):

    def setUp(self):
        self.ticket_type = TicketType.objects.create(name='Запрос на расчёт')
        self.project = Project.objects.create(code='НВК-001', name='Тест')

    def test_form_valid_full_data(self):
        """Позитивный тест: форма валидна со всеми полями"""
        data = {
            'subject': 'Тестовая тема',
            'description': 'Описание проблемы, достаточно длинное',
            'initiator': 'Иванов И.И.',
            'initiator_phone': '+79991234567',
            'initiator_email': 'ivanov@nevex.ru',
            'ticket_type': self.ticket_type.id,
            'project': self.project.id,
            'document_number': 'НВК-2024-КМ-001',
            'priority': 'high',
        }
        form = TicketForm(data=data)
        self.assertTrue(form.is_valid())

    def test_form_valid_minimal_data(self):
        """Позитивный тест: форма валидна с минимальными обязательными полями"""
        data = {
            'subject': 'Краткая тема',
            'description': 'Описание минимум 10 символов',
            'initiator': 'Петров П.П.',
        }
        form = TicketForm(data=data)
        self.assertTrue(form.is_valid())

    def test_form_invalid_empty_subject(self):
        """Негативный тест: пустая тема"""
        data = {
            'subject': '',
            'description': 'Описание',
            'initiator': 'Иванов И.И.',
        }
        form = TicketForm(data=data)
        self.assertFalse(form.is_valid())
        self.assertIn('subject', form.errors)

    def test_form_invalid_short_subject(self):
        """Негативный тест: тема короче 5 символов"""
        data = {
            'subject': 'Абв',
            'description': 'Описание проблемы',
            'initiator': 'Иванов И.И.',
        }
        form = TicketForm(data=data)
        self.assertFalse(form.is_valid())
        self.assertIn('subject', form.errors)

    def test_form_invalid_empty_description(self):
        """Негативный тест: пустое описание"""
        data = {
            'subject': 'Тестовая тема',
            'description': '',
            'initiator': 'Иванов И.И.',
        }
        form = TicketForm(data=data)
        self.assertFalse(form.is_valid())
        self.assertIn('description', form.errors)

    def test_form_invalid_short_description(self):
        """Негативный тест: описание короче 10 символов"""
        data = {
            'subject': 'Тестовая тема',
            'description': 'Коротко',
            'initiator': 'Иванов И.И.',
        }
        form = TicketForm(data=data)
        self.assertFalse(form.is_valid())
        self.assertIn('description', form.errors)

    def test_form_invalid_phone_format(self):
        """Негативный тест: неверный формат телефона"""
        data = {
            'subject': 'Тестовая тема',
            'description': 'Описание проблемы длинное',
            'initiator': 'Иванов И.И.',
            'initiator_phone': '12345',
        }
        form = TicketForm(data=data)
        self.assertFalse(form.is_valid())
        self.assertIn('initiator_phone', form.errors)

    def test_form_invalid_email_format(self):
        """Негативный тест: неверный формат email"""
        data = {
            'subject': 'Тестовая тема',
            'description': 'Описание проблемы длинное',
            'initiator': 'Иванов И.И.',
            'initiator_email': 'notanemail',
        }
        form = TicketForm(data=data)
        self.assertFalse(form.is_valid())
        self.assertIn('initiator_email', form.errors)

    def test_form_blank_phone_ok(self):
        """Позитивный тест: пустой телефон допустим"""
        data = {
            'subject': 'Тестовая тема',
            'description': 'Описание проблемы длинное',
            'initiator': 'Иванов И.И.',
            'initiator_phone': '',
        }
        form = TicketForm(data=data)
        self.assertTrue(form.is_valid())

    def test_form_blank_email_ok(self):
        """Позитивный тест: пустой email допустим"""
        data = {
            'subject': 'Тестовая тема',
            'description': 'Описание проблемы длинное',
            'initiator': 'Иванов И.И.',
            'initiator_email': '',
        }
        form = TicketForm(data=data)
        self.assertTrue(form.is_valid())


class CommentFormTest(TestCase):

    def test_comment_form_valid(self):
        """Позитивный тест: комментарий с текстом валиден"""
        form = CommentForm(data={'text': 'Полезный комментарий'})
        self.assertTrue(form.is_valid())

    def test_comment_form_invalid_empty(self):
        """Негативный тест: пустой комментарий"""
        form = CommentForm(data={'text': ''})
        self.assertFalse(form.is_valid())
        self.assertIn('text', form.errors)

    def test_comment_form_invalid_spaces(self):
        """Негативный тест: комментарий из пробелов"""
        form = CommentForm(data={'text': '   '})
        self.assertFalse(form.is_valid())
        self.assertIn('text', form.errors)

    def test_comment_form_invalid_short(self):
        """Негативный тест: комментарий короче 2 символов"""
        form = CommentForm(data={'text': 'а'})
        self.assertFalse(form.is_valid())
        self.assertIn('text', form.errors)


class TicketStatusFormTest(TestCase):

    def test_status_form_valid_choice(self):
        """Позитивный тест: выбор статуса"""
        form = TicketStatusForm(data={'status': 'in_progress'})
        self.assertTrue(form.is_valid())

    def test_status_form_empty(self):
        """Негативный тест: пустой выбор статуса"""
        form = TicketStatusForm(data={'status': ''})
        self.assertFalse(form.is_valid())