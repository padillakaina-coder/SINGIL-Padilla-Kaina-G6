from datetime import timedelta
from decimal import Decimal

from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.utils import timezone


class Person(models.Model):
    RELATIONSHIPS = [(r, r) for r in ('Friend', 'Family', 'Coworker', 'Classmate', 'Roommate', 'Other')]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='persons')
    person_name = models.CharField(max_length=100)
    relationship = models.CharField(max_length=20, choices=RELATIONSHIPS, blank=True)
    contact_info = models.CharField(max_length=100, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['person_name']
        constraints = [
            models.UniqueConstraint(fields=['user', 'person_name'], name='unique_person_per_user'),
        ]

    def __str__(self):
        return self.person_name


class DebtStatus(models.Model):
    status_name = models.CharField(max_length=20, unique=True)
    description = models.CharField(max_length=150)

    def __str__(self):
        return self.status_name


class Transaction(models.Model):
    LENT = 'LENT'
    BORROWED = 'BORROWED'
    DIRECTION_CHOICES = [(LENT, 'Lent (they owe me)'), (BORROWED, 'Borrowed (I owe them)')]

    person = models.ForeignKey(Person, on_delete=models.PROTECT, related_name='transactions')  # BR-11
    status = models.ForeignKey(DebtStatus, on_delete=models.PROTECT, related_name='transactions')
    direction = models.CharField(max_length=8, choices=DIRECTION_CHOICES)
    principal_amount = models.DecimalField(
        max_digits=12, decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01')), MaxValueValidator(Decimal('999999.99'))],
    )
    remaining_balance = models.DecimalField(max_digits=12, decimal_places=2)
    transaction_date = models.DateField()
    due_date = models.DateField()
    purpose = models.CharField(max_length=150, blank=True)
    notes = models.CharField(max_length=500, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-transaction_date', '-created_at']

    @property
    def amount_paid(self):
        return self.principal_amount - self.remaining_balance

    def compute_status_name(self):
        """BR-19 to BR-24, in priority order."""
        today = timezone.localdate()
        if self.remaining_balance <= 0:
            return 'Paid'
        if self.due_date < today:
            return 'Overdue'
        if self.due_date <= today + timedelta(days=3):
            return 'Due Soon'
        if self.remaining_balance < self.principal_amount:
            return 'Partially Paid'
        return 'Pending'

    def update_status(self):
        """Sets self.status from the rules. Does not save."""
        self.status = DebtStatus.objects.get(status_name=self.compute_status_name())

    def refresh_status(self):
        """Recomputes the status and saves only if it changed."""
        old = self.status_id
        self.update_status()
        if self.status_id != old:
            self.save(update_fields=['status'])


def refresh_statuses(queryset):
    for t in queryset.select_related('status'):
        t.refresh_status()