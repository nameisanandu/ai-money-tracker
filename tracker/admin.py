"""
Admin configuration for AI Money Tracker.
"""
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User

from .models import Category, Transaction, MonthlyBudget, Loan, EMIPayment


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name']
    search_fields = ['name']


@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ['user', 'amount', 'category', 'type', 'description', 'date', 'created_at']
    list_filter = ['type', 'category', 'date']
    search_fields = ['description', 'user__username']
    date_hierarchy = 'date'
    ordering = ['-date', '-created_at']


@admin.register(Loan)
class LoanAdmin(admin.ModelAdmin):
    list_display = ['user', 'loan_name', 'total_amount', 'interest_rate', 'tenure_months', 'emi_amount', 'start_date']
    list_filter = ['user', 'start_date']
    search_fields = ['loan_name', 'user__username']


@admin.register(EMIPayment)
class EMIPaymentAdmin(admin.ModelAdmin):
    list_display = ['loan', 'amount', 'payment_date', 'status']
    list_filter = ['status', 'payment_date', 'loan']
    search_fields = ['loan__loan_name', 'loan__user__username']


# Re-register User with custom admin if needed for transaction view
admin.site.unregister(User)


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ['username', 'email', 'first_name', 'last_name', 'is_staff']
    list_filter = ['is_staff', 'is_superuser', 'is_active']
    search_fields = ['username', 'first_name', 'last_name', 'email']
