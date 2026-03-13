"""
Forms for AI Money Tracker application.
"""
from decimal import Decimal, ROUND_HALF_UP
import math

from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.utils import timezone

from .models import Transaction, Category, MonthlyBudget, Loan, EMIPayment


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

    auto_calculate_emi = forms.BooleanField(
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        label='Auto-calculate EMI from amount, rate, and tenure',
    )
    auto_calculate_interest_rate = forms.BooleanField(
        required=False,
        initial=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        label='Auto-calculate interest rate from amount, tenure, and EMI',
    )
    interest_rate = forms.FloatField(
        required=False,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'step': '0.01',
            'min': '0',
            'placeholder': '8.50',
        }),
        help_text='Enter interest rate manually, or enable auto-calculation if EMI is known.',
    )
    emi_amount = forms.FloatField(
        required=False,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'step': '0.01',
            'min': '0',
            'placeholder': 'Leave blank to auto-calculate',
        }),
        help_text='Leave this blank to let the app calculate the EMI from amount, rate, and tenure.',
    )

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
            'tenure_months': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '1',
                'placeholder': '60',
            }),
            'start_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date',
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['start_date'].initial = self.initial.get('start_date') or timezone.localdate()
        if not self.is_bound:
            self.fields['auto_calculate_emi'].initial = False
            self.fields['auto_calculate_interest_rate'].initial = False

    def clean(self):
        cleaned_data = super().clean()
        total_amount = cleaned_data.get('total_amount')
        interest_rate = cleaned_data.get('interest_rate')
        tenure_months = cleaned_data.get('tenure_months')
        emi_amount = cleaned_data.get('emi_amount')
        auto_calculate_emi = cleaned_data.get('auto_calculate_emi')
        auto_calculate_interest_rate = cleaned_data.get('auto_calculate_interest_rate')

        if total_amount is None or tenure_months is None:
            return cleaned_data

        if total_amount <= 0:
            self.add_error('total_amount', 'Loan amount must be greater than zero.')
        if tenure_months <= 0:
            self.add_error('tenure_months', 'Tenure must be at least 1 month.')
        if interest_rate is not None and interest_rate < 0:
            self.add_error('interest_rate', 'Interest rate cannot be negative.')
        if emi_amount is not None and emi_amount <= 0:
            self.add_error('emi_amount', 'EMI amount must be greater than zero.')
        if auto_calculate_emi and auto_calculate_interest_rate:
            self.add_error(None, 'Choose only one auto-calculation option at a time.')

        if self.errors:
            return cleaned_data

        if self.instance.pk:
            preserved_count = self.instance.emi_payments.exclude(status=EMIPayment.STATUS_PENDING).count()
            if tenure_months < preserved_count:
                self.add_error(
                    'tenure_months',
                    f'Tenure cannot be less than {preserved_count} because that many EMI entries are already paid or partial.',
                )

        if self.errors:
            return cleaned_data

        if auto_calculate_interest_rate:
            if emi_amount in (None, ''):
                self.add_error('emi_amount', 'Enter EMI amount to auto-calculate interest rate.')
            elif emi_amount * tenure_months < total_amount:
                self.add_error(
                    'emi_amount',
                    'This EMI is too low to cover the loan amount across the selected tenure.',
                )
            else:
                cleaned_data['interest_rate'] = self._calculate_interest_rate(
                    total_amount, emi_amount, tenure_months
                )
        elif auto_calculate_emi:
            if interest_rate in (None, ''):
                self.add_error('interest_rate', 'Enter interest rate to auto-calculate EMI.')
            else:
                cleaned_data['emi_amount'] = self._calculate_emi(total_amount, interest_rate, tenure_months)
        else:
            if interest_rate in (None, ''):
                self.add_error('interest_rate', 'Enter interest rate or enable auto-calculation.')
            if emi_amount in (None, ''):
                self.add_error('emi_amount', 'Enter EMI amount or enable auto-calculation.')

        if self.errors:
            return cleaned_data

        if not auto_calculate_interest_rate and not auto_calculate_emi and emi_amount * tenure_months < total_amount:
            self.add_error(
                'emi_amount',
                'This EMI is too low to cover the loan amount across the selected tenure.',
            )

        return cleaned_data

    @staticmethod
    def _calculate_emi(total_amount, annual_interest_rate, tenure_months):
        """Calculate monthly EMI using the standard amortization formula."""
        principal = Decimal(str(total_amount))
        rate = Decimal(str(annual_interest_rate))
        months = Decimal(str(tenure_months))

        if rate == 0:
            emi = principal / months
        else:
            monthly_rate = rate / Decimal('1200')
            factor = (Decimal('1') + monthly_rate) ** int(tenure_months)
            emi = principal * monthly_rate * factor / (factor - Decimal('1'))

        return float(emi.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP))

    @staticmethod
    def _calculate_interest_rate(total_amount, emi_amount, tenure_months):
        """Approximate annual interest rate from principal, EMI, and tenure."""
        principal = float(total_amount)
        emi = float(emi_amount)
        months = int(tenure_months)

        if months <= 0 or principal <= 0 or emi <= 0:
            return 0.0

        zero_rate_emi = principal / months
        if emi <= zero_rate_emi:
            return 0.0

        def emi_for_rate(annual_rate):
            monthly_rate = annual_rate / 1200
            if monthly_rate == 0:
                return principal / months
            factor = math.pow(1 + monthly_rate, months)
            return (principal * monthly_rate * factor) / (factor - 1)

        low = 0.0
        high = 100.0
        while emi_for_rate(high) < emi and high < 1000:
            high *= 2

        for _ in range(80):
            mid = (low + high) / 2
            current_emi = emi_for_rate(mid)
            if current_emi < emi:
                low = mid
            else:
                high = mid

        return float(Decimal(str((low + high) / 2)).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP))


class TransactionImportForm(forms.Form):
    """Form for importing transactions from CSV."""
    csv_file = forms.FileField(
        label='CSV File',
        help_text='Expected columns: date, description, category, amount, type',
        widget=forms.FileInput(attrs={'class': 'form-control', 'accept': '.csv'})
    )


class EMIPaymentForm(forms.ModelForm):
    """Form for editing an EMI entry."""

    class Meta:
        model = EMIPayment
        fields = ['payment_date', 'amount', 'paid_amount', 'status']
        widgets = {
            'payment_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'amount': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0'}),
            'paid_amount': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
        }

    def clean(self):
        cleaned_data = super().clean()
        amount = cleaned_data.get('amount')
        paid_amount = cleaned_data.get('paid_amount')
        status = cleaned_data.get('status')

        if amount is None or paid_amount is None or status is None:
            return cleaned_data

        if amount <= 0:
            self.add_error('amount', 'EMI amount must be greater than zero.')
        if paid_amount < 0:
            self.add_error('paid_amount', 'Paid amount cannot be negative.')
        if paid_amount > amount:
            self.add_error('paid_amount', 'Paid amount cannot be more than the EMI amount.')

        if self.errors:
            return cleaned_data

        if status == EMIPayment.STATUS_PAID:
            cleaned_data['paid_amount'] = amount
        elif status == EMIPayment.STATUS_PENDING:
            if paid_amount > 0:
                self.add_error('status', 'Use Partial if some amount has already been paid.')
        elif status == EMIPayment.STATUS_PARTIAL:
            if not (0 < paid_amount < amount):
                self.add_error('paid_amount', 'Partial payments must be more than 0 and less than the EMI amount.')

        return cleaned_data


class ExtraPaymentForm(forms.Form):
    """Form for applying an extra loan payment across outstanding EMIs."""

    amount = forms.FloatField(
        widget=forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0.01'}),
        help_text='This amount will be applied to the oldest unpaid EMI first.',
    )
    payment_date = forms.DateField(
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        initial=timezone.localdate,
    )
    description = forms.CharField(
        required=False,
        max_length=255,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Optional note'}),
    )

    def __init__(self, *args, loan=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.loan = loan

    def clean_amount(self):
        amount = self.cleaned_data['amount']
        if amount <= 0:
            raise forms.ValidationError('Extra payment must be greater than zero.')
        if self.loan and amount > self.loan.remaining_balance():
            raise forms.ValidationError('Extra payment cannot exceed the remaining balance.')
        return amount
