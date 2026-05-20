from django.shortcuts import render, redirect
from django.contrib.auth import login, logout
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from .models import UserProfile


def login_view(request):
    if request.user.is_authenticated:
        if request.user.is_superuser:
            return redirect('/admin/')
        return redirect('ticket_list')

    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            messages.success(request, f'Добро пожаловать, {user.first_name}!')

            if user.is_superuser:
                return redirect('/admin/')
            return redirect('ticket_list')
        else:
            messages.error(request, 'Неверный логин или пароль')
    else:
        form = AuthenticationForm()
    return render(request, 'registration/login.html', {'form': form})


def logout_view(request):
    logout(request)
    messages.info(request, 'Вы вышли из системы')
    return redirect('login')


def is_manager(user):
    return (
        user.is_authenticated
        and hasattr(user, 'profile')
        and user.profile.role == 'manager'
    )


@login_required
@user_passes_test(is_manager, login_url='ticket_list')
def register_user(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.first_name = request.POST.get('first_name', '')
            user.last_name = request.POST.get('last_name', '')
            user.save()
            # Профиль создался автоматически, обновим поля
            profile = user.profile
            profile.middle_name = request.POST.get('middle_name', '')
            profile.phone = request.POST.get('phone', '')
            profile.role = request.POST.get('role', 'operator')
            profile.department = request.POST.get('department', '')
            profile.save()

            messages.success(request, f'Пользователь {user.username} создан')
            return redirect('ticket_list')
    else:
        form = UserCreationForm()
    return render(request, 'registration/register.html', {'form': form})