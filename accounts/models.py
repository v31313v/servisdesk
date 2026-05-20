from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver


class UserProfile(models.Model):
    ROLE_CHOICES = [
        ('operator', 'Оператор'),
        ('manager', 'Руководитель'),
    ]

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='profile',
        verbose_name='Пользователь'
    )
    middle_name = models.CharField(max_length=50, blank=True, verbose_name='Отчество')
    phone = models.CharField(max_length=18, blank=True, verbose_name='Телефон')
    role = models.CharField(
        max_length=10,
        choices=ROLE_CHOICES,
        default='operator',
        verbose_name='Роль'
    )
    department = models.CharField(max_length=100, blank=True, verbose_name='Отдел')

    class Meta:
        verbose_name = 'Профиль пользователя'
        verbose_name_plural = 'Профили пользователей'

    def __str__(self):
        return f'{self.user.last_name} {self.user.first_name} ({self.get_role_display()})'

    @property
    def full_name(self):
        parts = [self.user.last_name, self.user.first_name, self.middle_name]
        return ' '.join(p for p in parts if p)


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.get_or_create(user=instance)