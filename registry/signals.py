from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from threading import local

from .models import (
    AuditLog,
    Business,
    Owner,
    BusinessOwner,
    License,
    Inspection,
    Document,
)

# --------------------------------
# Thread-local storage for user
# --------------------------------

_user = local()

def set_current_user(user):
    _user.value = user

def get_current_user():
    return getattr(_user, 'value', None)


# --------------------------------
# Models we want to audit
# --------------------------------

AUDITED_MODELS = (
    Business,
    Owner,
    BusinessOwner,
    License,
    Inspection,
    Document,
)


# --------------------------------
# CREATE / UPDATE
# --------------------------------

@receiver(post_save)
def log_save(sender, instance, created, **kwargs):
    if sender not in AUDITED_MODELS:
        return

    AuditLog.objects.create(
        user=get_current_user(),
        action='create' if created else 'update',
        table_name=sender.__name__,
        record_id=instance.pk,
    )


# --------------------------------
# DELETE
# --------------------------------

@receiver(post_delete)
def log_delete(sender, instance, **kwargs):
    if sender not in AUDITED_MODELS:
        return

    AuditLog.objects.create(
        user=get_current_user(),
        action='delete',
        table_name=sender.__name__,
        record_id=instance.pk,
    )
