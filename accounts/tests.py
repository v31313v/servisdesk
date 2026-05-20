from django.test import TestCase
from django.contrib.auth.models import User
from django.urls import reverse
from .models import UserProfile


class UserModelTest(TestCase):
    """Тесты модели UserProfile"""

    def setUp(self):
        self.user = User.objects.create_user(
            username='operator1',
            password='TestPass123',
            first_name='Иван',
            last_name='Петров'
        )
        self.profile = UserProfile.objects.create(
            user=self.user,
            middle_name='Сергеевич',
            phone='+79991234567',
            role='operator',
            department='Конструкторский отдел'
        )

    def test_profile_creation(self):
        """Позитивный тест: создание профиля пользователя"""
        self.assertEqual(self.profile.role, 'operator')
        self.assertEqual(self.profile.phone, '+79991234567')
        self.assertEqual(self.profile.department, 'Конструкторский отдел')
        self.assertEqual(str(self.profile), 'Петров Иван (Оператор)')

    def test_full_name_with_middle(self):
        """Проверка свойства full_name с отчеством"""
        self.assertEqual(self.profile.full_name, 'Петров Иван Сергеевич')

    def test_full_name_without_middle(self):
        """Проверка свойства full_name без отчества"""
        self.profile.middle_name = ''
        self.profile.save()
        self.assertEqual(self.profile.full_name, 'Петров Иван')

    def test_full_name_without_first_name(self):
        """Проверка full_name если нет имени"""
        self.profile.user.first_name = ''
        self.profile.user.save()
        self.profile.middle_name = ''
        self.profile.save()
        self.assertEqual(self.profile.full_name, 'Петров')

    def test_default_role(self):
        """Проверка роли по умолчанию"""
        user2 = User.objects.create_user(username='user2', password='pass')
        profile2 = UserProfile.objects.create(user=user2)
        self.assertEqual(profile2.role, 'operator')

    def test_default_department_blank(self):
        """Проверка пустого отдела по умолчанию"""
        user2 = User.objects.create_user(username='user3', password='pass')
        profile2 = UserProfile.objects.create(user=user2)
        self.assertEqual(profile2.department, '')


class AuthViewsTest(TestCase):
    """Тесты представлений аутентификации"""

    def setUp(self):
        self.user = User.objects.create_user(
            username='operator1',
            password='TestPass123',
            first_name='Иван',
            last_name='Петров'
        )
        UserProfile.objects.create(user=self.user, role='operator', department='Конструкторский отдел')

        self.manager = User.objects.create_user(
            username='manager1',
            password='TestPass123',
            first_name='Пётр',
            last_name='Сидоров'
        )
        UserProfile.objects.create(user=self.manager, role='manager', department='Руководство')

    def test_login_page_accessible(self):
        """Позитивный тест: страница логина доступна"""
        response = self.client.get(reverse('login'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Войти')
        self.assertContains(response, 'НЕВЕКС')

    def test_login_success(self):
        """Позитивный тест: успешная авторизация"""
        response = self.client.post(reverse('login'), {
            'username': 'operator1',
            'password': 'TestPass123',
        })
        self.assertRedirects(response, reverse('ticket_list'))

    def test_login_wrong_password(self):
        """Негативный тест: неверный пароль"""
        response = self.client.post(reverse('login'), {
            'username': 'operator1',
            'password': 'WrongPass',
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Неверный логин или пароль')

    def test_login_nonexistent_user(self):
        """Негативный тест: несуществующий пользователь"""
        response = self.client.post(reverse('login'), {
            'username': 'ghost',
            'password': 'nopass',
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Неверный логин или пароль')

    def test_login_blank_fields(self):
        """Негативный тест: пустые поля"""
        response = self.client.post(reverse('login'), {
            'username': '',
            'password': '',
        })
        self.assertEqual(response.status_code, 200)

    def test_logout(self):
        """Позитивный тест: выход из системы"""
        self.client.login(username='operator1', password='TestPass123')
        response = self.client.get(reverse('logout'))
        self.assertRedirects(response, reverse('login'))

    def test_redirect_if_authenticated(self):
        """Позитивный тест: редирект авторизованного на список заявок"""
        self.client.login(username='operator1', password='TestPass123')
        response = self.client.get(reverse('login'))
        self.assertRedirects(response, reverse('ticket_list'))


class RegistrationTest(TestCase):
    """Тесты регистрации пользователей"""

    def setUp(self):
        self.manager = User.objects.create_user(
            username='manager1',
            password='TestPass123'
        )
        UserProfile.objects.create(user=self.manager, role='manager')

    def test_register_page_accessible_for_manager(self):
        """Позитивный тест: страница регистрации доступна руководителю"""
        self.client.login(username='manager1', password='TestPass123')
        response = self.client.get(reverse('register'))
        self.assertEqual(response.status_code, 200)

    def test_register_access_denied_for_operator(self):
        """Негативный тест: оператор не может зайти на страницу регистрации"""
        operator = User.objects.create_user(username='op', password='pass')
        UserProfile.objects.create(user=operator, role='operator')
        self.client.login(username='op', password='pass')
        response = self.client.get(reverse('register'))
        self.assertEqual(response.status_code, 302)

    def test_register_access_denied_anonymous(self):
        """Негативный тест: аноним не может зайти на страницу регистрации"""
        response = self.client.get(reverse('register'))
        self.assertEqual(response.status_code, 302)

    def test_register_user(self):
        """Позитивный тест: создание нового пользователя"""
        self.client.login(username='manager1', password='TestPass123')
        response = self.client.post(reverse('register'), {
            'username': 'new_operator',
            'password1': 'StrongPass123',
            'password2': 'StrongPass123',
            'first_name': 'Алексей',
            'last_name': 'Иванов',
            'middle_name': 'Петрович',
            'phone': '+79998887766',
            'role': 'operator',
            'department': 'Технологический отдел',
        })
        self.assertEqual(response.status_code, 302)
        user = User.objects.get(username='new_operator')
        self.assertEqual(user.first_name, 'Алексей')
        self.assertEqual(user.last_name, 'Иванов')
        self.assertEqual(user.profile.role, 'operator')
        self.assertEqual(user.profile.department, 'Технологический отдел')