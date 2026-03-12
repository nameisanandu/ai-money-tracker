"""
Models for AI Money Tracker application.
"""
from django.db import models
from django.contrib.auth.models import User


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


    def remaining_emis(self):
        """Count pending EMIs."""
        return self.emi_payments.filter(status=EMIPayment.STATUS_PENDING).count()

    def remaining_balance(self):
        """Sum of pending EMI amounts."""
        return sum(p.amount for p in self.emi_payments.filter(status=EMIPayment.STATUS_PENDING))

    def paid_percentage(self):
        """Percentage of loan paid off."""
        total = self.tenure_months * self.emi_amount
        paid = sum(p.amount for p in self.emi_payments.filter(status=EMIPayment.STATUS_PAID))
        return (paid / total * 100) if total > 0 else 0

    @property
    def total_paid(self):
        """Total amount paid so far."""
        return sum(p.amount for p in self.emi_payments.filter(status=EMIPayment.STATUS_PAID))


class EMIPayment(models.Model):
    """Individual EMI payment entry."""

    STATUS_PENDING = 'pending'
    STATUS_PAID = 'paid'
    STATUS_CHOICES = [
        (STATUS_PENDING, 'Pending'),
        (STATUS_PAID, 'Paid'),
    ]

    loan = models.ForeignKey(Loan, on_delete=models.CASCADE, related_name='emi_payments')
    amount = models.FloatField()
    payment_date = models.DateField()
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default=STATUS_PENDING)

    class Meta:
        ordering = ['payment_date', 'id']

    def __str__(self):
        return f"{self.loan.loan_name} - {self.payment_date} - {self.amount} ({self.status})"
