"""Sayt paneli uchun huquq tekshiruvchilari."""
from functools import wraps

from django.contrib import messages
from django.shortcuts import redirect


def admin_talab(view_func):
    """Faqat sayt admini (rol=admin yoki superuser) kira oladigan sahifalar."""

    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect("accounts:kirish")
        if not request.user.admin_mi:
            messages.error(request, "Bu bo'limga faqat admin kira oladi.")
            return redirect("dashboard:bosh")
        return view_func(request, *args, **kwargs)

    return wrapper
