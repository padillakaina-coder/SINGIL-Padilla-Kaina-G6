from django.contrib import messages
from django.contrib.auth import views as auth_views
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from .decorators import role_required
from .forms import RegisterForm, ProfileForm
from .models import User
from django.db.models import Sum
from debts.models import Transaction, refresh_statuses


def register(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    form = RegisterForm(request.POST or None)
    if request.method == 'POST':
        if form.is_valid():
            form.save()
            messages.success(request, 'Account created! You can now log in.')
            return redirect('login')
        messages.error(request, 'Please fix the errors below.')
    return render(request, 'accounts/register.html', {'form': form})


class SingilLoginView(auth_views.LoginView):
    template_name = 'accounts/login.html'
    redirect_authenticated_user = True

    def form_valid(self, form):
        messages.success(self.request, 'Welcome back!')
        return super().form_valid(form)

    def form_invalid(self, form):
        messages.error(self.request, 'Invalid email or password.')
        return super().form_invalid(form)


@login_required
def dashboard(request):
    """Sends each user to the dashboard for their role."""
    if request.user.role == 'ADMIN':
        return redirect('admin_dashboard')
    return redirect('user_dashboard')


@role_required('USER')
def user_dashboard(request):
    mine = Transaction.objects.filter(person__user=request.user)
    refresh_statuses(mine)
    owed = mine.filter(direction='BORROWED').aggregate(t=Sum('remaining_balance'))['t'] or 0
    receivable = mine.filter(direction='LENT').aggregate(t=Sum('remaining_balance'))['t'] or 0
    context = {
        'total_owed': owed,
        'total_receivable': receivable,
        'pending_count': mine.filter(status__status_name='Pending').count(),
        'overdue_count': mine.filter(status__status_name='Overdue').count(),
        'recent': mine.select_related('person', 'status')[:5],
    }
    return render(request, 'accounts/user_dashboard.html', context)


@role_required('ADMIN')
def admin_dashboard(request):
    # The admin sees only counts, never anyone's transaction details (SDD 1.3)
    context = {
        'total_users': User.objects.filter(role='USER').count(),
        'total_transactions': Transaction.objects.count(),
        'users': User.objects.filter(role='USER').order_by('-date_joined')[:10],
    }
    return render(request, 'accounts/admin_dashboard.html', context)


@login_required
def profile(request):
    return render(request, 'accounts/profile.html')


@login_required
def profile_edit(request):
    form = ProfileForm(request.POST or None, instance=request.user)
    if request.method == 'POST':
        if form.is_valid():
            form.save()
            messages.success(request, 'Profile updated.')
            return redirect('profile')
        messages.error(request, 'Please fix the errors below.')
    return render(request, 'accounts/profile_edit.html', {'form': form})