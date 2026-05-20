from django.test import TestCase
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from tickets.models import Ticket, TicketType, Project, Comment


class TicketModelTest(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            username='engineer1',
            password='TestPass123'
        )
        self.ticket_type = TicketType.objects.create(
            name='Запрос на корректировку чертежа',
            department='Конструкторский отдел'
        )
        self.project = Project.objects.create(
            code='НВК-2024-001',
            name='Реконструкция цеха №3 АО "Металлург"',
            client='АО "Металлург"'
        )
        self.ticket = Ticket.objects.create(
            subject='Проверка узла сопряжения фермы Ф-1 и колонны К-2',
            description='Необходимо проверить узел на прочность с учётом новых нагрузок из отчёта ИГИ',
            initiator='Сидоров Алексей Викторович',
            initiator_department='Конструкторский отдел',
            initiator_phone='+79991234567',
            initiator_email='sidorov@nevex.ru',
            ticket_type=self.ticket_type,
            project=self.project,
            document_number='НВК-2024-КМ-045',
            priority='high',
            author=self.user
        )

    def test_ticket_creation_full(self):
        self.assertEqual(Ticket.objects.count(), 1)
        self.assertEqual(self.ticket.status, 'new')
        self.assertEqual(self.ticket.priority, 'high')
        self.assertEqual(str(self.ticket),
            f'Заявка #{self.ticket.pk}: Проверка узла сопряжения фермы Ф-1 и колонны К-2')

    def test_ticket_absolute_url(self):
        url = self.ticket.get_absolute_url()
        self.assertEqual(url, f'/tickets/{self.ticket.pk}/')

    def test_phone_validation_valid(self):
        self.ticket.initiator_phone = '+79998887766'
        self.ticket.full_clean()

    def test_phone_validation_invalid(self):
        self.ticket.initiator_phone = '12345'
        with self.assertRaises(ValidationError):
            self.ticket.full_clean()


class TicketStatusTransitionTest(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(username='eng', password='pass')
        self.ticket = Ticket.objects.create(
            subject='Тест статусов',
            description='Описание для проверки переходов статусов — минимум десять символов',
            initiator='Петров Пётр Петрович',
            author=self.user
        )

    def test_new_to_in_progress(self):
        self.ticket.change_status('in_progress', self.user)
        self.assertEqual(self.ticket.status, 'in_progress')

    def test_in_progress_to_resolved(self):
        self.ticket.status = 'in_progress'
        self.ticket.save()
        self.ticket.change_status('resolved', self.user)
        self.assertEqual(self.ticket.status, 'resolved')

    def test_resolved_to_closed(self):
        self.ticket.status = 'resolved'
        self.ticket.save()
        self.ticket.change_status('closed', self.user)
        self.assertEqual(self.ticket.status, 'closed')

    def test_new_to_resolved_invalid(self):
        with self.assertRaises(ValidationError):
            self.ticket.change_status('resolved', self.user)

    def test_closed_to_in_progress_invalid(self):
        self.ticket.status = 'closed'
        self.ticket.save()
        with self.assertRaises(ValidationError):
            self.ticket.change_status('in_progress', self.user)


class CommentModelTest(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(username='eng', password='pass')
        self.ticket = Ticket.objects.create(
            subject='Тест комментариев',
            description='Описание для теста комментариев',
            initiator='Иванов И.И.',
            author=self.user
        )

    def test_comment_creation(self):
        comment = Comment.objects.create(
            ticket=self.ticket,
            author=self.user,
            text='Узел проверен, требуется усиление'
        )
        self.assertEqual(Comment.objects.count(), 1)
        self.assertIn('Узел проверен', comment.text)