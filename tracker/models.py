"""
Models for AI Money Tracker application.
"""
from datetime import timedelta

from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone


class Category(models.Model):
    """Category for organizing expenses."""
    name = models.CharField(max_length=100, unique=True)

    class Meta:
        verbose_name_plural = 'Categories'

    def __str__(self):
        return self.name


class Transaction(models.Model):
    """Income or expense transaction."""
    TYPE_CHOICES = [
        ('income', 'Income'),
        ('expense', 'Expense'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='transactions')
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    category = models.ForeignKey(
        Category, on_delete=models.SET_NULL, null=True, blank=True, related_name='transactions'
    )
    type = models.CharField(max_length=10, choices=TYPE_CHOICES)
    description = models.CharField(max_length=255, blank=True)
    date = models.DateField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-date', '-created_at']

    def __str__(self):
        return f"{self.type}: {self.amount} - {self.date}"


class MonthlyBudget(models.Model):
    """Monthly budget set by user."""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='monthly_budgets')
    month = models.PositiveSmallIntegerField()  # 1-12
    year = models.PositiveIntegerField()
    budget_amount = models.DecimalField(max_digits=12, decimal_places=2)

    class Meta:
        ordering = ['-year', '-month']
        constraints = [
            models.UniqueConstraint(fields=['user', 'month', 'year'], name='unique_user_month_year')
        ]

    def __str__(self):
        return f"{self.user.username} - {self.month}/{self.year}: ₹{self.budget_amount}"


class Loan(models.Model):
    """Loan with EMI schedule."""

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='loans')
    loan_name = models.CharField(max_length=255)
    total_amount = models.FloatField()
    interest_rate = models.FloatField(help_text="Annual interest rate in percent")
    tenure_months = models.IntegerField()
    emi_amount = models.FloatField(help_text="Planned EMI amount per month")
    start_date = models.DateField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.loan_name} ({self.user.username})"

    @property
    def total_scheduled_amount(self):
        """Total amount expected to be paid across the full schedule."""
        scheduled_amounts = [payment.amount for payment in self.emi_payments.all()]
        if scheduled_amounts:
            return sum(scheduled_amounts)
        return self.tenure_months * self.emi_amount

    @property
    def paid_emis_count(self):
        """Number of EMI entries already marked paid."""
        return self.emi_payments.filter(status=EMIPayment.STATUS_PAID).count()

    def remaining_emis(self):
        """Count pending EMIs."""
        return self.emi_payments.exclude(status=EMIPayment.STATUS_PAID).count()

    def overdue_emis(self):
        """Count pending EMIs with dates before today."""
        today = timezone.localdate()
        return self.emi_payments.filter(
            status__in=[EMIPayment.STATUS_PENDING, EMIPayment.STATUS_PARTIAL],
            payment_date__lt=today,
        ).count()

    def upcoming_emis(self, days=30):
        """Return pending EMIs due within the next N days."""
        today = timezone.localdate()
        return self.emi_payments.filter(
            status__in=[EMIPayment.STATUS_PENDING, EMIPayment.STATUS_PARTIAL],
            payment_date__gte=today,
            payment_date__lte=today + timedelta(days=days),
        ).order_by('payment_date')

    def next_emi(self):
        """Return the next pending EMI, if any."""
        return self.emi_payments.exclude(status=EMIPayment.STATUS_PAID).order_by('payment_date').first()

    def remaining_balance(self):
        """Sum of pending EMI amounts."""
        return sum(payment.remaining_due for payment in self.emi_payments.exclude(status=EMIPayment.STATUS_PAID))

    def paid_percentage(self):
        """Percentage of loan paid off."""
        total = self.total_scheduled_amount
        paid = self.total_paid
        return (paid / total * 100) if total > 0 else 0

    @property
    def total_paid(self):
        """Total amount paid so far."""
        return sum(payment.paid_amount for payment in self.emi_payments.all())

    @property
    def completion_date(self):
        """Expected payoff date based on the latest scheduled EMI."""
        last_emi = self.emi_payments.order_by('-payment_date').first()
        return last_emi.payment_date if last_emi else None

    @property
    def status_label(self):
        """High-level loan status for UI display."""
        if self.remaining_emis() == 0:
            return 'Closed'
        if self.overdue_emis() > 0:
            return 'Overdue'
        next_payment = self.next_emi()
        if next_payment and next_payment.payment_date <= timezone.localdate() + timedelta(days=7):
            return 'Due Soon'
        return 'On Track'


class EMIPayment(models.Model):
    """Individual EMI payment entry."""

    STATUS_PENDING = 'pending'
    STATUS_PARTIAL = 'partial'
    STATUS_PAID = 'paid'
    STATUS_CHOICES = [
        (STATUS_PENDING, 'Pending'),
        (STATUS_PARTIAL, 'Partial'),
        (STATUS_PAID, 'Paid'),
    ]

    loan = models.ForeignKey(Loan, on_delete=models.CASCADE, related_name='emi_payments')
    amount = models.FloatField()
    paid_amount = models.FloatField(default=0)
    payment_date = models.DateField()
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default=STATUS_PENDING)

    class Meta:
        ordering = ['payment_date', 'id']

    def __str__(self):
        return f"{self.loan.loan_name} - {self.payment_date} - {self.amount} ({self.status})"

    @property
    def remaining_due(self):
        """Outstanding amount still due for this EMI."""
        return max(0, self.amount - self.paid_amount)

    @property
    def is_overdue(self):
        """Return whether this EMI is pending past its due date."""
        return self.status in [self.STATUS_PENDING, self.STATUS_PARTIAL] and self.payment_date < timezone.localdate()

    @property
    def is_due_soon(self):
        """Return whether this EMI is pending and due within the next 7 days."""
        today = timezone.localdate()
        return self.status in [self.STATUS_PENDING, self.STATUS_PARTIAL] and today <= self.payment_date <= today + timedelta(days=7)
