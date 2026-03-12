"""
Forms for AI Money Tracker application.
"""
from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User

from .models import Transaction, Category, MonthlyBudget, Loan


class RegisterForm(UserCreationForm):
    """User registration form."""
    email = forms.EmailField(required=True, widget=forms.EmailInput(attrs={'class': 'form-control form-control-lg'}))
    username = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control form-control-lg'}))
    password1 = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control form-control-lg'}))
    password2 = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control form-control-lg'}))

    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2']


class TransactionForm(forms.ModelForm):
    """Form for adding income or expense transactions."""
    new_category = forms.CharField(
        required=False,
        max_length=100,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Type a new category name',
            'autocomplete': 'off',
        }),
        label='Or type new category',
    )

    class Meta:
        model = Transaction
        fields = ['amount', 'category', 'type', 'description', 'date']
        widgets = {
            'amount': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0',
                'placeholder': '0.00',
            }),
            'category': forms.Select(attrs={'class': 'form-select'}),
            'type': forms.Select(attrs={'class': 'form-select'}),
            'description': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter description',
                'maxlength': '255',
            }),
            'date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date',
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['category'].queryset = Category.objects.all().order_by('name')
        self.fields['category'].required = False
        self.fields['category'].empty_label = 'Choose a category'
        self.fields['category'].label = 'Category (select from list)'
        # Add placeholder for type dropdown
        self.fields['type'].choices = [('', 'Select type (Income or Expense)')] + list(Transaction.TYPE_CHOICES)


MONTH_CHOICES = [
    (1, '01 - January'), (2, '02 - February'), (3, '03 - March'),
    (4, '04 - April'), (5, '05 - May'), (6, '06 - June'),
    (7, '07 - July'), (8, '08 - August'), (9, '09 - September'),
    (10, '10 - October'), (11, '11 - November'), (12, '12 - December'),
]


class MonthlyBudgetForm(forms.ModelForm):
    """Form for setting monthly budget."""
    month = forms.TypedChoiceField(
        choices=MONTH_CHOICES,
        coerce=int,
        widget=forms.Select(attrs={'class': 'form-select'}),
        label='Month',
    )

    class Meta:
        model = MonthlyBudget
        fields = ['month', 'year', 'budget_amount']
        widgets = {
            'year': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '2020',
                'max': '2030',
                'placeholder': '2025',
            }),
            'budget_amount': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0',
                'placeholder': '2000.00',
            }),
        }


class LoanForm(forms.ModelForm):
    """Form for creating a new loan."""

    class Meta:
        model = Loan
        fields = ['loan_name', 'total_amount', 'interest_rate', 'tenure_months', 'emi_amount', 'start_date']
        widgets = {
            'loan_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g. Home Loan',
            }),
            'total_amount': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0',
                'placeholder': '1000000',
            }),
            'interest_rate': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0',
                'placeholder': '8.50',
            }),
            'tenure_months': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '1',
                'placeholder': '60',
            }),
            'emi_amount': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0',
                'placeholder': '20000',
            }),
            'start_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date',
            }),
        }


class TransactionImportForm(forms.Form):
    """Form for importing transactions from CSV."""
    csv_file = forms.FileField(
        label='CSV File',
        help_text='Expected columns: date, description, category, amount, type',
        widget=forms.FileInput(attrs={'class': 'form-control', 'accept': '.csv'})
    )
