from functools import wraps
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect


def role_required(role):
    def decorator(view):
        @login_required
        @wraps(view)
        def wrapper(request, *args, **kwargs):
            if request.user.role != role:
                messages.error(request, 'You are not allowed to open that page.')
                return redirect('dashboard')
            return view(request, *args, **kwargs)
        return wrapper
    return decorator