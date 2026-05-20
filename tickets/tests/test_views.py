from django.test import TestCase
from django.contrib.auth.models import User
from django.urls import reverse
from accounts.models import UserProfile
from tickets.models import Ticket, TicketType, Project


class TicketViewsTest(TestCase):

    def setUp(self):
        self.operator = User.objects.create_user(
            username='operator1',
            password='TestPass123',
            first_name='Иван',
            last_name='Петров'
        )
        UserProfile.objects.create(user=self.operator, role='operator')

        self.manager = User.objects.create_user(
            username='manager1',
            password='TestPass123',
            first_name='Пётр',
            last_name='Сидоров'
        )
        UserProfile.objects.create(user=self.manager, role='manager')

        self.ticket_type = TicketType.objects.create(name='Запрос на расчёт')
        self.project = Project.objects.create(code='НВК-001', name='Тестовый проект')

    def test_ticket_list_requires_login(self):
        """Негативный тест: без авторизации редирект на логин"""
        response = self.client.get(reverse('ticket_list'))
        self.assertEqual(response.status_code, 302)

    def test_ticket_list_operator_sees_own(self):
        """Позитивный тест: оператор видит только свои заявки"""
        self.client.login(username='operator1', password='TestPass123')
        Ticket.objects.create(
            subject='Моя заявка',
            description='Описание моей заявки минимум десять символов',
            initiator='Сидоров А.В.',
            author=self.operator
        )
        Ticket.objects.create(
            subject='Чужая заявка',
            description='Описание чужой заявки минимум десять символов',
            initiator='Иванов И.И.',
            author=self.manager
        )
        response = self.client.get(reverse('ticket_list'))
        self.assertContains(response, 'Моя заявка')
        self.assertNotContains(response, 'Чужая заявка')

    def test_ticket_list_manager_sees_all(self):
        """Позитивный тест: руководитель видит все заявки"""
        self.client.login(username='manager1', password='TestPass123')
        Ticket.objects.create(
            subject='Первая заявка',
            description='Описание первой заявки тут',
            initiator='Сидоров А.В.',
            author=self.operator
        )
        Ticket.objects.create(
            subject='Вторая заявка',
            description='Описание второй заявки тут',
            initiator='Иванов И.И.',
            author=self.manager
        )
        response = self.client.get(reverse('ticket_list'))
        self.assertContains(response, 'Первая заявка')
        self.assertContains(response, 'Вторая заявка')

    def test_ticket_create_valid(self):
        """Позитивный тест: создание заявки с валидными данными"""
        self.client.login(username='operator1', password='TestPass123')
        response = self.client.post(reverse('ticket_create'), {
            'subject': 'Тестовая заявка',
            'description': 'Описание тестовой заявки для проверки создания',
            'initiator': 'Петров П.П.',
            'initiator_phone': '+79998887766',
            'initiator_email': 'petrov@nevex.ru',
            'ticket_type': self.ticket_type.id,
            'project': self.project.id,
            'priority': 'high',
        })
        self.assertEqual(Ticket.objects.count(), 1)
        ticket = Ticket.objects.first()
        self.assertEqual(ticket.subject, 'Тестовая заявка')
        self.assertEqual(ticket.status, 'new')
        self.assertRedirects(response, reverse('ticket_detail', kwargs={'pk': ticket.pk}))

    def test_ticket_create_empty_subject(self):
        """Негативный тест: создание заявки с пустой темой"""
        self.client.login(username='operator1', password='TestPass123')
        response = self.client.post(reverse('ticket_create'), {
            'subject': '',
            'description': 'Описание',
            'initiator': 'Петров П.П.',
        })
        self.assertEqual(Ticket.objects.count(), 0)
        self.assertEqual(response.status_code, 200)

    def test_ticket_create_invalid_phone(self):
        """Негативный тест: создание заявки с неверным форматом телефона"""
        self.client.login(username='operator1', password='TestPass123')
        response = self.client.post(reverse('ticket_create'), {
            'subject': 'Тест',
            'description': 'Описание проблемы',
            'initiator': 'Петров П.П.',
            'initiator_phone': '12345',
        })
        self.assertEqual(Ticket.objects.count(), 0)
        self.assertContains(response, 'Формат телефона')

    def test_ticket_detail_access_own(self):
        """Позитивный тест: оператор видит детали своей заявки"""
        self.client.login(username='operator1', password='TestPass123')
        ticket = Ticket.objects.create(
            subject='Моя заявка',
            description='Описание моей заявки',
            initiator='Сидоров А.В.',
            author=self.operator
        )
        response = self.client.get(reverse('ticket_detail', kwargs={'pk': ticket.pk}))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Моя заявка')

    def test_ticket_detail_access_foreign_denied(self):
        """Негативный тест: оператор не видит чужую заявку"""
        self.client.login(username='operator1', password='TestPass123')
        ticket = Ticket.objects.create(
            subject='Чужая заявка',
            description='Описание чужой заявки',
            initiator='Иванов И.И.',
            author=self.manager
        )
        response = self.client.get(reverse('ticket_detail', kwargs={'pk': ticket.pk}))
        self.assertEqual(response.status_code, 403)

    def test_ticket_edit_own_new(self):
        """Позитивный тест: редактирование своей новой заявки"""
        self.client.login(username='operator1', password='TestPass123')
        ticket = Ticket.objects.create(
            subject='Старая тема',
            description='Описание старой темы',
            initiator='Петров П.П.',
            author=self.operator
        )
        response = self.client.post(reverse('ticket_edit', kwargs={'pk': ticket.pk}), {
            'subject': 'Новая тема',
            'description': 'Новое описание заявки',
            'initiator': 'Петров П.П.',
        })
        ticket.refresh_from_db()
        self.assertEqual(ticket.subject, 'Новая тема')
        self.assertRedirects(response, reverse('ticket_detail', kwargs={'pk': ticket.pk}))

    def test_ticket_edit_not_new_denied(self):
        """Негативный тест: нельзя редактировать заявку не в статусе Новая"""
        self.client.login(username='operator1', password='TestPass123')
        ticket = Ticket.objects.create(
            subject='Заявка в работе',
            description='Описание заявки в работе',
            initiator='Петров П.П.',
            author=self.operator,
            status='in_progress'
        )
        response = self.client.get(reverse('ticket_edit', kwargs={'pk': ticket.pk}))
        self.assertRedirects(response, reverse('ticket_detail', kwargs={'pk': ticket.pk}))

    def test_ticket_delete_by_manager(self):
        """Позитивный тест: руководитель удаляет заявку"""
        self.client.login(username='manager1', password='TestPass123')
        ticket = Ticket.objects.create(
            subject='На удаление',
            description='Эту заявку надо удалить',
            initiator='Иванов И.И.',
            author=self.operator
        )
        response = self.client.post(reverse('ticket_delete', kwargs={'pk': ticket.pk}))
        self.assertEqual(Ticket.objects.count(), 0)
        self.assertRedirects(response, reverse('ticket_list'))

    def test_ticket_delete_by_operator_denied(self):
        """Негативный тест: оператор не может удалить заявку"""
        self.client.login(username='operator1', password='TestPass123')
        ticket = Ticket.objects.create(
            subject='Моя заявка',
            description='Описание моей заявки',
            initiator='Петров П.П.',
            author=self.operator
        )
        response = self.client.get(reverse('ticket_delete', kwargs={'pk': ticket.pk}))
        self.assertEqual(response.status_code, 403)

    def test_add_comment(self):
        """Позитивный тест: добавление комментария к заявке"""
        self.client.login(username='operator1', password='TestPass123')
        ticket = Ticket.objects.create(
            subject='Заявка с комментарием',
            description='Описание заявки',
            initiator='Петров П.П.',
            author=self.operator
        )
        response = self.client.post(reverse('ticket_detail', kwargs={'pk': ticket.pk}), {
            'comment_submit': '1',
            'text': 'Проверил узел, всё в порядке',
        })
        self.assertEqual(ticket.comments.count(), 1)
        self.assertRedirects(response, reverse('ticket_detail', kwargs={'pk': ticket.pk}))

    def test_add_empty_comment_denied(self):
        """Негативный тест: нельзя добавить пустой комментарий"""
        self.client.login(username='operator1', password='TestPass123')
        ticket = Ticket.objects.create(
            subject='Заявка',
            description='Описание заявки',
            initiator='Петров П.П.',
            author=self.operator
        )
        response = self.client.post(reverse('ticket_detail', kwargs={'pk': ticket.pk}), {
            'comment_submit': '1',
            'text': '  ',
        })
        self.assertEqual(ticket.comments.count(), 0)

    def test_change_status_valid(self):
        """Позитивный тест: изменение статуса Новая → В работе"""
        self.client.login(username='operator1', password='TestPass123')
        ticket = Ticket.objects.create(
            subject='Заявка',
            description='Описание заявки',
            initiator='Петров П.П.',
            author=self.operator
        )
        response = self.client.post(
            reverse('ticket_change_status', kwargs={'pk': ticket.pk}),
            {'status': 'in_progress'}
        )
        ticket.refresh_from_db()
        self.assertEqual(ticket.status, 'in_progress')

    def test_change_status_invalid_transition(self):
        """Негативный тест: нельзя перевести Новую в Решена"""
        self.client.login(username='operator1', password='TestPass123')
        ticket = Ticket.objects.create(
            subject='Заявка',
            description='Описание заявки',
            initiator='Петров П.П.',
            author=self.operator
        )
        response = self.client.post(
            reverse('ticket_change_status', kwargs={'pk': ticket.pk}),
            {'status': 'resolved'}
        )
        ticket.refresh_from_db()
        self.assertNotEqual(ticket.status, 'resolved')


class DashboardAccessTest(TestCase):

    def setUp(self):
        self.operator = User.objects.create_user(username='op', password='pass')
        UserProfile.objects.create(user=self.operator, role='operator')

        self.manager = User.objects.create_user(username='mgr', password='pass')
        UserProfile.objects.create(user=self.manager, role='manager')

    def test_dashboard_access_denied_operator(self):
        """Негативный тест: оператор не может зайти в отчёты"""
        self.client.login(username='op', password='pass')
        response = self.client.get(reverse('dashboard'))
        self.assertEqual(response.status_code, 302)

    def test_dashboard_access_granted_manager(self):
        """Позитивный тест: руководитель видит дашборд"""
        self.client.login(username='mgr', password='pass')
        response = self.client.get(reverse('dashboard'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Всего заявок')


class FilterSearchTest(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(username='op', password='pass')
        UserProfile.objects.create(user=self.user, role='operator')
        self.client.login(username='op', password='pass')

        self.type1 = TicketType.objects.create(name='Запрос на расчёт')
        self.type2 = TicketType.objects.create(name='Ошибка в чертеже')

        Ticket.objects.create(
            subject='Расчёт балки Б-1',
            description='Нужно проверить сечение',
            initiator='Иванов И.И.',
            ticket_type=self.type1,
            author=self.user
        )
        Ticket.objects.create(
            subject='Ошибка в узле У-3',
            description='Не совпадают размеры',
            initiator='Петров П.П.',
            ticket_type=self.type2,
            author=self.user
        )

    def test_filter_by_status(self):
        """Позитивный тест: фильтрация по статусу"""
        response = self.client.get(reverse('ticket_list') + '?status=new')
        self.assertContains(response, 'Расчёт балки Б-1')
        self.assertContains(response, 'Ошибка в узле У-3')

    def test_filter_by_type(self):
        """Позитивный тест: фильтрация по типу обращения"""
        response = self.client.get(
            reverse('ticket_list') + f'?ticket_type={self.type1.id}'
        )
        self.assertContains(response, 'Расчёт балки Б-1')
        self.assertNotContains(response, 'Ошибка в узле У-3')

    def test_search_by_subject(self):
        """Позитивный тест: поиск по ключевому слову"""
        response = self.client.get(reverse('ticket_list') + '?search=балки')
        self.assertContains(response, 'Расчёт балки Б-1')
        self.assertNotContains(response, 'Ошибка в узле У-3')