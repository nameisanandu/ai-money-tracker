"""
Views for AI Money Tracker application.
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Sum, Q
from django.db import transaction as db_transaction
from django.core.paginator import Paginator
from django.http import HttpResponse
from django.utils import timezone
from django.db.models.functions import TruncMonth
from django.utils.safestring import mark_safe
from decimal import Decimal
import csv
import io
import json
from datetime import datetime, date, timedelta
import calendar

from .models import Transaction, Category, MonthlyBudget, Loan, EMIPayment
from .forms import (
    RegisterForm, TransactionForm, MonthlyBudgetForm, TransactionImportForm,
    LoanForm, EMIPaymentForm, ExtraPaymentForm,
)
from .ai_analyzer import get_financial_insights
from .expense_predictor import predict_next_month_expense


def register_user(request):
    """Handle user registration."""
    if request.user.is_authenticated:
        return redirect('dashboard')

    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, 'Account created successfully! Welcome to AI Money Tracker.')
            return redirect('dashboard')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = RegisterForm()

    return render(request, 'register.html', {'form': form})


def login_user(request):
    """Handle user login."""
    if request.user.is_authenticated:
        return redirect('dashboard')

    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            messages.success(request, f'Welcome back, {user.username}!')
            return redirect('dashboard')
        else:
            messages.error(request, 'Invalid username or password.')

    return render(request, 'login.html')


def logout_user(request):
    """Handle user logout."""
    logout(request)
    messages.info(request, 'You have been logged out.')
    return redirect('login')


@login_required
def dashboard(request):
    """Display dashboard with stats, charts, and AI insights."""
    user_transactions = Transaction.objects.filter(user=request.user)
    expense_transactions = user_transactions.filter(type='expense')

    # Calculate totals
    total_income = user_transactions.filter(type='income').aggregate(
        total=Sum('amount')
    )['total'] or Decimal('0')
    total_expense = expense_transactions.aggregate(total=Sum('amount'))['total'] or Decimal('0')
    balance = total_income - total_expense

    # Expense distribution for pie chart (by category)
    category_expenses = (
        expense_transactions.values('category__name')
        .annotate(total=Sum('amount'))
        .order_by('-total')
    )

    chart_labels = []
    chart_data = []
    chart_colors = [
        '#4e73df', '#1cc88a', '#36b9cc', '#f6c23e', '#e74a3b',
        '#858796', '#5a5c69', '#2e59d9', '#17a673', '#2c9faf',
    ]
    for i, item in enumerate(category_expenses):
        label = item['category__name'] or 'Uncategorized'
        chart_labels.append(label)
        chart_data.append(float(item['total']))
    chart_colors = chart_colors[:len(chart_labels)]

    # Monthly expense trend
    monthly_expenses = (
        expense_transactions
        .annotate(month=TruncMonth('date'))
        .values('month')
        .annotate(total=Sum('amount'))
        .order_by('month')
    )
    trend_labels = [item['month'].strftime('%b %Y') for item in monthly_expenses]
    trend_data = [float(item['total']) for item in monthly_expenses]

    # Income vs Expense bar chart (by month)
    monthly_income = (
        user_transactions.filter(type='income')
        .annotate(month=TruncMonth('date'))
        .values('month')
        .annotate(total=Sum('amount'))
        .order_by('month')
    )

    # Loans & EMI stats
    user_loans = Loan.objects.filter(user=request.user).prefetch_related('emi_payments')
    total_monthly_emi = sum(l.emi_amount for l in user_loans if l.remaining_emis() > 0)
    loan_progress_list = [
        {
            'name': loan.loan_name,
            'paid_pct': round(loan.paid_percentage(), 1),
            'remaining_balance': loan.remaining_balance(),
            'remaining_emis': loan.remaining_emis(),
            'status': loan.status_label,
        }
        for loan in user_loans
    ]






    income_by_month = {item['month']: float(item['total']) for item in monthly_income}
    expense_by_month = {item['month']: float(item['total']) for item in monthly_expenses}
    all_months = sorted(set(income_by_month.keys()) | set(expense_by_month.keys()))
    income_vs_labels = [m.strftime('%b %Y') for m in all_months]
    income_vs_income = [income_by_month.get(m, 0) for m in all_months]
    income_vs_expense = [expense_by_month.get(m, 0) for m in all_months]
    # For simplicity, plot the same total_monthly_emi against each month as a reference band
    income_vs_emi = [total_monthly_emi for _ in all_months]

    # Balance trend over time (cumulative)
    balance_labels = []
    balance_data = []
    running = 0
    for m in all_months:
        inc = income_by_month.get(m, 0)
        exp = expense_by_month.get(m, 0)
        running += inc - exp
        balance_labels.append(m.strftime('%b %Y'))
        balance_data.append(running)

    # Budget for current month
    now = timezone.now()
    budget_obj = MonthlyBudget.objects.filter(
        user=request.user, month=now.month, year=now.year
    ).first()
    current_month_expense = expense_transactions.filter(
        date__month=now.month, date__year=now.year
    ).aggregate(total=Sum('amount'))['total'] or Decimal('0')
    budget_amount = budget_obj.budget_amount if budget_obj else None
    budget_spent = float(current_month_expense)
    budget_remaining = float(budget_amount - current_month_expense) if budget_amount else None
    budget_alert = None
    if budget_amount and budget_amount > 0:
        pct = float(current_month_expense) / float(budget_amount) * 100
        if pct >= 100:
            budget_alert = 'danger'
        elif pct >= 80:
            budget_alert = 'warning'



    # Expense prediction
    predicted_expense = predict_next_month_expense(user_transactions)

    # AI insights (include loan context)
    insights = get_financial_insights(user_transactions, loans=user_loans)

    context = {
        'total_income': total_income,
        'total_expense': total_expense,
        'balance': balance,
        'chart_labels': mark_safe(json.dumps(chart_labels)),
        'chart_data': mark_safe(json.dumps(chart_data)),
        'chart_colors': mark_safe(json.dumps(chart_colors)),
        'has_chart_data': len(chart_data) > 0,
        'trend_labels': mark_safe(json.dumps(trend_labels)),
        'trend_data': mark_safe(json.dumps(trend_data)),
        'has_trend_data': len(trend_data) > 0,
        'income_vs_labels': mark_safe(json.dumps(income_vs_labels)),
        'income_vs_income': mark_safe(json.dumps(income_vs_income)),
        'income_vs_expense': mark_safe(json.dumps(income_vs_expense)),
        'income_vs_emi': mark_safe(json.dumps(income_vs_emi)),
        'has_income_vs_data': len(all_months) > 0,
        'balance_labels': mark_safe(json.dumps(balance_labels)),
        'balance_data': mark_safe(json.dumps(balance_data)),
        'has_balance_data': len(balance_data) > 0,
        'budget_amount': budget_amount,
        'budget_spent': budget_spent,
        'budget_remaining': budget_remaining,
        'budget_alert': budget_alert,
        'predicted_expense': predicted_expense,
        'total_monthly_emi': total_monthly_emi,
        'loan_progress_list': loan_progress_list,
        'insights': insights,
    }
    return render(request, 'dashboard.html', context)


def _resolve_category_from_form(form):
    """Resolve category from form: use new_category (get_or_create) if provided, else dropdown."""
    new_name = (form.cleaned_data.get('new_category') or '').strip()
    if new_name:
        category = Category.objects.filter(name__iexact=new_name).first()
        if not category:
            category = Category.objects.create(name=new_name)
        return category
    return form.cleaned_data.get('category')


@login_required
def add_transaction(request):
    """Add a new income or expense transaction."""
    if request.method == 'POST':
        form = TransactionForm(request.POST)
        if form.is_valid():
            transaction = form.save(commit=False)
            transaction.user = request.user
            transaction.category = _resolve_category_from_form(form)
            transaction.save()
            msg = 'Income' if transaction.type == 'income' else 'Expense'
            messages.success(request, f'{msg} added successfully!')
            return redirect('transaction_list')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = TransactionForm(initial={'date': timezone.now().date()})

    return render(request, 'add_transaction.html', {'form': form})


def _add_months(d, months):
    """Return date d shifted by given number of months."""
    month = d.month - 1 + months
    year = d.year + month // 12
    month = month % 12 + 1
    day = min(d.day, calendar.monthrange(year, month)[1])
    return date(year, month, day)


def _sync_emi_status(emi):
    """Normalize EMI status based on scheduled vs paid amount."""
    if emi.paid_amount >= emi.amount:
        emi.paid_amount = emi.amount
        emi.status = EMIPayment.STATUS_PAID
    elif emi.paid_amount > 0:
        emi.status = EMIPayment.STATUS_PARTIAL
    else:
        emi.paid_amount = 0
        emi.status = EMIPayment.STATUS_PENDING


def _record_loan_payment(user, amount, payment_date, loan_name, description):
    """Create an expense transaction for a loan payment delta."""
    if amount <= 0:
        return
    category, _ = Category.objects.get_or_create(name='Loan EMI')
    Transaction.objects.create(
        user=user,
        amount=amount,
        category=category,
        type='expense',
        description=description or f"Payment for {loan_name}",
        date=payment_date,
    )


def _rebuild_pending_emi_schedule(loan):
    """Regenerate only unpaid future EMI rows after loan terms change."""
    preserved_payments = list(
        loan.emi_payments.exclude(status=EMIPayment.STATUS_PENDING).order_by('payment_date', 'id')
    )
    loan.emi_payments.filter(status=EMIPayment.STATUS_PENDING).delete()

    start_index = len(preserved_payments)
    for idx in range(start_index, loan.tenure_months):
        EMIPayment.objects.create(
            loan=loan,
            amount=loan.emi_amount,
            payment_date=_add_months(loan.start_date, idx),
            paid_amount=0,
            status=EMIPayment.STATUS_PENDING,
        )


def _apply_extra_payment_to_loan(loan, amount):
    """Apply a payment amount across the oldest unpaid EMIs."""
    remaining_amount = amount
    touched = 0
    for emi in loan.emi_payments.exclude(status=EMIPayment.STATUS_PAID).order_by('payment_date', 'id'):
        if remaining_amount <= 0:
            break
        remaining_due = emi.remaining_due
        if remaining_due <= 0:
            continue
        applied = min(remaining_due, remaining_amount)
        emi.paid_amount += applied
        _sync_emi_status(emi)
        emi.save(update_fields=['paid_amount', 'status'])
        remaining_amount -= applied
        touched += 1
    return amount - remaining_amount, touched


@login_required
def loan_list(request):
    """List all loans for the current user."""
    loans = Loan.objects.filter(user=request.user).prefetch_related('emi_payments')
    total_remaining_balance = sum(loan.remaining_balance() for loan in loans)
    active_loans = sum(1 for loan in loans if loan.remaining_emis() > 0)
    overdue_loans = sum(1 for loan in loans if loan.overdue_emis() > 0)
    due_soon_count = sum(loan.upcoming_emis(days=7).count() for loan in loans)
    context = {
        'loans': loans,
        'total_remaining_balance': total_remaining_balance,
        'active_loans': active_loans,
        'overdue_loans': overdue_loans,
        'due_soon_count': due_soon_count,
    }
    return render(request, 'loan_list.html', context)


@login_required
def add_loan(request):
    """Create a new loan and generate EMI schedule."""
    if request.method == 'POST':
        form = LoanForm(request.POST)
        if form.is_valid():
            loan = form.save(commit=False)
            loan.user = request.user
            loan.save()
            # Generate EMI schedule
            for i in range(loan.tenure_months):
                pay_date = _add_months(loan.start_date, i)
                EMIPayment.objects.create(
                    loan=loan,
                    amount=loan.emi_amount,
                    payment_date=pay_date,
                    status=EMIPayment.STATUS_PENDING,
                )
            messages.success(request, 'Loan created and EMI schedule generated.')
            return redirect('loan_list')
        messages.error(request, 'Please correct the errors below.')
    else:
        form = LoanForm(initial={'start_date': timezone.localdate()})
    return render(request, 'add_loan.html', {'form': form})


@login_required
def edit_loan(request, pk):
    """Edit an existing loan and refresh unpaid schedule if terms changed."""
    loan = get_object_or_404(Loan.objects.prefetch_related('emi_payments'), pk=pk, user=request.user)
    if request.method == 'POST':
        original_values = {
            'start_date': loan.start_date,
            'tenure_months': loan.tenure_months,
            'emi_amount': loan.emi_amount,
        }
        form = LoanForm(request.POST, instance=loan)
        if form.is_valid():
            with db_transaction.atomic():
                loan = form.save()
                schedule_changed = any(
                    getattr(loan, key) != original_values[key]
                    for key in original_values
                )
                if schedule_changed:
                    _rebuild_pending_emi_schedule(loan)
            if schedule_changed:
                messages.success(request, 'Loan updated. Unpaid EMI schedule was refreshed.')
            else:
                messages.success(request, 'Loan details updated successfully.')
            return redirect('loan_detail', pk=loan.pk)
        messages.error(request, 'Please correct the errors below.')
    else:
        form = LoanForm(instance=loan)
    return render(request, 'edit_loan.html', {'form': form, 'loan': loan})


@login_required
def delete_loan(request, pk):
    """Delete a loan and all its EMI records."""
    loan = get_object_or_404(Loan, pk=pk, user=request.user)
    if request.method == 'POST':
        loan_name = loan.loan_name
        loan.delete()
        messages.success(request, f'{loan_name} was deleted successfully.')
        return redirect('loan_list')
    return render(request, 'delete_loan.html', {'loan': loan})


@login_required
def loan_detail(request, pk):
    """Show details and progress for a single loan."""
    loan = get_object_or_404(
        Loan.objects.prefetch_related('emi_payments'),
        pk=pk,
        user=request.user,
    )
    emis = loan.emi_payments.all().order_by('payment_date')
    overdue_emis = emis.filter(status=EMIPayment.STATUS_PENDING, payment_date__lt=timezone.localdate())
    upcoming_emis = emis.filter(
        status=EMIPayment.STATUS_PENDING,
        payment_date__gte=timezone.localdate(),
        payment_date__lte=timezone.localdate() + timedelta(days=30),
    )
    next_emi = loan.next_emi()
    total_paid = loan.total_paid
    remaining_balance = loan.remaining_balance()
    remaining_emis = loan.remaining_emis()
    context = {
        'loan': loan,
        'emis': emis,
        'total_paid': total_paid,
        'remaining_balance': remaining_balance,
        'remaining_emis': remaining_emis,
        'overdue_emis': overdue_emis,
        'upcoming_emis': upcoming_emis,
        'next_emi': next_emi,
        'extra_payment_form': ExtraPaymentForm(loan=loan),
    }
    return render(request, 'loan_detail.html', context)


@login_required
def emi_payments(request):
    """List EMI payments across all loans."""
    payments = list(
        EMIPayment.objects.filter(loan__user=request.user)
        .select_related('loan')
        .order_by('payment_date', 'loan__loan_name')
    )
    payments.sort(key=lambda payment: (payment.status == EMIPayment.STATUS_PAID, payment.payment_date))
    overdue_count = sum(1 for payment in payments if payment.is_overdue)
    due_soon_count = sum(1 for payment in payments if payment.is_due_soon)
    context = {
        'payments': payments,
        'overdue_count': overdue_count,
        'due_soon_count': due_soon_count,
    }
    return render(request, 'emi_payments.html', context)


@login_required
def edit_emi_payment(request, pk):
    """Edit a scheduled EMI entry."""
    emi = get_object_or_404(EMIPayment.objects.select_related('loan'), pk=pk, loan__user=request.user)
    old_paid_amount = emi.paid_amount
    if request.method == 'POST':
        form = EMIPaymentForm(request.POST, instance=emi)
        if form.is_valid():
            emi = form.save(commit=False)
            _sync_emi_status(emi)
            emi.save()
            payment_delta = emi.paid_amount - old_paid_amount
            if payment_delta > 0:
                _record_loan_payment(
                    request.user,
                    payment_delta,
                    emi.payment_date,
                    emi.loan.loan_name,
                    f"Manual EMI update for {emi.loan.loan_name}",
                )
            elif payment_delta < 0:
                messages.warning(request, 'Paid amount was reduced. Existing expense records were not reversed automatically.')
            messages.success(request, 'EMI details updated successfully.')
            return redirect('loan_detail', pk=emi.loan.pk)
        messages.error(request, 'Please correct the errors below.')
    else:
        form = EMIPaymentForm(instance=emi)
    return render(request, 'edit_emi_payment.html', {'form': form, 'emi': emi})


@login_required
def add_extra_payment(request, pk):
    """Apply an extra payment across the oldest unpaid EMIs for a loan."""
    loan = get_object_or_404(Loan.objects.prefetch_related('emi_payments'), pk=pk, user=request.user)
    if request.method == 'POST':
        form = ExtraPaymentForm(request.POST, loan=loan)
        if form.is_valid():
            amount = form.cleaned_data['amount']
            payment_date = form.cleaned_data['payment_date']
            description = form.cleaned_data['description'].strip()
            with db_transaction.atomic():
                applied_amount, touched = _apply_extra_payment_to_loan(loan, amount)
                _record_loan_payment(
                    request.user,
                    applied_amount,
                    payment_date,
                    loan.loan_name,
                    description or f"Extra payment for {loan.loan_name}",
                )
            messages.success(
                request,
                f'Applied Rs {applied_amount:,.2f} across {touched} EMI(s) for {loan.loan_name}.',
            )
            return redirect('loan_detail', pk=loan.pk)
        messages.error(request, 'Please correct the errors below.')
    else:
        form = ExtraPaymentForm(loan=loan)
    return render(request, 'extra_payment.html', {'form': form, 'loan': loan})


@login_required
def mark_emi_paid(request, pk):
    """Mark a single EMI as paid and create an expense transaction."""
    emi = get_object_or_404(EMIPayment, pk=pk, loan__user=request.user)
    if request.method == 'POST':
        if emi.status != EMIPayment.STATUS_PAID:
            payment_delta = emi.remaining_due
            emi.paid_amount = emi.amount
            emi.status = EMIPayment.STATUS_PAID
            emi.save(update_fields=['paid_amount', 'status'])
            _record_loan_payment(
                request.user,
                payment_delta,
                emi.payment_date,
                emi.loan.loan_name,
                f"EMI payment for {emi.loan.loan_name}",
            )
            messages.success(request, 'EMI marked as paid and expense recorded.')
        else:
            messages.info(request, 'This EMI is already marked as paid.')
    next_url = request.POST.get('next')
    if next_url:
        return redirect(next_url)
    return redirect('emi_payments')


@login_required
def transaction_list(request):
    """List all transactions with filters, search, and pagination."""
    transactions = Transaction.objects.filter(user=request.user).select_related('category')

    # Search by description or category name
    search = request.GET.get('search', '').strip()
    if search:
        transactions = transactions.filter(
            Q(description__icontains=search) |
            Q(category__name__icontains=search)
        )

    # Filter by category
    category_filter = request.GET.get('category')
    if category_filter and category_filter.isdigit():
        transactions = transactions.filter(category_id=category_filter)

    # Filter by type (income/expense)
    type_filter = request.GET.get('type')
    if type_filter in ('income', 'expense'):
        transactions = transactions.filter(type=type_filter)

    # Filter by date range
    date_from = request.GET.get('date_from')
    date_to = request.GET.get('date_to')
    if date_from:
        try:
            df = datetime.strptime(date_from, '%Y-%m-%d').date()
            transactions = transactions.filter(date__gte=df)
        except ValueError:
            pass
    if date_to:
        try:
            dt = datetime.strptime(date_to, '%Y-%m-%d').date()
            transactions = transactions.filter(date__lte=dt)
        except ValueError:
            pass

    transactions = transactions.order_by('-date', '-created_at')

    # Pagination
    paginator = Paginator(transactions, 15)
    page_num = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_num)

    categories = Category.objects.all().order_by('name')

    context = {
        'page_obj': page_obj,
        'transactions': page_obj.object_list,
        'categories': categories,
        'selected_category': category_filter or '',
        'selected_type': type_filter or '',
        'search': search,
        'date_from': date_from or '',
        'date_to': date_to or '',
    }
    return render(request, 'transactions.html', context)


@login_required
def export_transactions_csv(request):
    """Export transactions to CSV (bonus feature)."""
    transactions = Transaction.objects.filter(user=request.user).select_related('category')

    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="transactions.csv"'

    writer = csv.writer(response)
    writer.writerow(['Date', 'Type', 'Amount', 'Category', 'Description', 'Created'])

    for t in transactions:
        writer.writerow([
            t.date,
            t.type,
            t.amount,
            t.category.name if t.category else '',
            t.description,
            t.created_at.strftime('%Y-%m-%d %H:%M'),
        ])

    return response


@login_required
def edit_transaction(request, pk):
    """Edit an existing transaction."""
    transaction = get_object_or_404(Transaction, pk=pk, user=request.user)
    if request.method == 'POST':
        form = TransactionForm(request.POST, instance=transaction)
        if form.is_valid():
            transaction = form.save(commit=False)
            transaction.category = _resolve_category_from_form(form)
            transaction.save()
            messages.success(request, 'Transaction updated successfully!')
            return redirect('transaction_list')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = TransactionForm(instance=transaction)
    return render(request, 'edit_transaction.html', {'form': form, 'transaction': transaction})


@login_required
def delete_transaction(request, pk):
    """Delete a transaction."""
    transaction = get_object_or_404(Transaction, pk=pk, user=request.user)
    if request.method == 'POST':
        transaction.delete()
        messages.success(request, 'Transaction deleted successfully!')
        return redirect('transaction_list')
    return render(request, 'confirm_delete.html', {'transaction': transaction})


@login_required
def set_budget(request):
    """Set or update monthly budget."""
    now = timezone.now()
    if request.method == 'POST':
        form = MonthlyBudgetForm(request.POST)
        if form.is_valid():
            budget = form.save(commit=False)
            budget.user = request.user
            MonthlyBudget.objects.update_or_create(
                user=request.user,
                month=budget.month,
                year=budget.year,
                defaults={'budget_amount': budget.budget_amount}
            )
            messages.success(request, f'Budget for {budget.month:02d}/{budget.year} set to ₹{budget.budget_amount:,.2f}')
            return redirect('dashboard')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = MonthlyBudgetForm(initial={'month': now.month, 'year': now.year})
    return render(request, 'set_budget.html', {'form': form})


@login_required
def export_excel(request):
    """Export transactions to Excel (monthly report)."""
    try:
        import openpyxl
        from openpyxl.styles import Font, Alignment
    except ImportError:
        messages.error(request, 'Excel export is not available.')
        return redirect('transaction_list')

    transactions = Transaction.objects.filter(user=request.user).select_related('category').order_by('-date')
    month_filter = request.GET.get('month')
    year_filter = request.GET.get('year')
    if month_filter and year_filter and month_filter.isdigit() and year_filter.isdigit():
        transactions = transactions.filter(
            date__month=int(month_filter),
            date__year=int(year_filter)
        )

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = 'Transactions'
    ws.append(['Date', 'Category', 'Type', 'Amount', 'Description'])
    for row in ws.iter_rows(min_row=1, max_row=1):
        for cell in row:
            cell.font = Font(bold=True)
    for t in transactions:
        ws.append([
            t.date.strftime('%Y-%m-%d'),
            t.category.name if t.category else '',
            t.type,
            float(t.amount),
            t.description or '',
        ])

    response = HttpResponse(
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    fname = f'transactions_{year_filter or "all"}_{month_filter or "all"}.xlsx'
    response['Content-Disposition'] = f'attachment; filename="{fname}"'
    wb.save(response)
    return response


def _get_csv_value(row, *possible_keys):
    """Get value from CSV row with flexible column name matching (case-insensitive)."""
    row_lower = {k.strip().lower(): v for k, v in row.items()}
    for key in possible_keys:
        if key.lower() in row_lower and row_lower[key.lower()]:
            return str(row_lower[key.lower()]).strip()
    return ''


def _parse_csv_date(date_str):
    """Parse date string with multiple format support."""
    if not date_str:
        return None
    date_str = str(date_str).strip()
    # Strip time portion if present (e.g. "2025-01-15 00:00:00")
    if ' ' in date_str:
        date_str = date_str.split()[0]
    formats = [
        '%Y-%m-%d', '%Y/%m/%d', '%Y.%m.%d',
        '%m/%d/%Y', '%m-%d-%Y', '%m.%d.%Y',
        '%d/%m/%Y', '%d-%m-%Y', '%d.%m.%Y',
        '%d/%b/%Y', '%d-%b-%Y', '%b %d, %Y', '%B %d, %Y',
    ]
    for fmt in formats:
        try:
            return datetime.strptime(date_str, fmt).date()
        except (ValueError, TypeError):
            continue
    return None


def _parse_csv_amount(amt_str):
    """Parse amount string, handling currency symbols and commas."""
    if not amt_str:
        return Decimal('0')
    amt_str = str(amt_str).strip().replace(',', '').replace('$', '').replace('₹', '').replace('€', '').replace('£', '')
    amt_str = amt_str.replace('(', '-').replace(')', '')
    try:
        return Decimal(amt_str)
    except Exception:
        return None


@login_required
def import_transactions(request):
    """Import transactions from CSV file."""
    if request.method == 'POST':
        form = TransactionImportForm(request.POST, request.FILES)
        if form.is_valid():
            f = request.FILES['csv_file']
            if not f.name.lower().endswith('.csv'):
                messages.error(request, 'Please upload a CSV file.')
                return redirect('import_transactions')
            raw = f.read()
            try:
                decoded = raw.decode('utf-8-sig')  # Handles BOM from Excel
            except UnicodeDecodeError:
                try:
                    decoded = raw.decode('latin-1')
                except UnicodeDecodeError:
                    decoded = raw.decode('utf-8', errors='replace')
            decoded = decoded.strip('\ufeff')  # Strip BOM if present
            try:
                dialect = csv.Sniffer().sniff(decoded[:4096], delimiters=',;\t')
            except csv.Error:
                dialect = 'excel'
            reader = csv.DictReader(io.StringIO(decoded), dialect=dialect)
            created = 0
            errors = []
            for i, row in enumerate(reader):
                if not row or all(not str(v).strip() for v in row.values()):
                    continue
                try:
                    date_str = _get_csv_value(row, 'date', 'Date', 'DATE')
                    desc = _get_csv_value(row, 'description', 'Description', 'desc', 'DESCRIPTION')
                    cat_name = _get_csv_value(row, 'category', 'Category', 'CATEGORY')
                    amt_str = _get_csv_value(row, 'amount', 'Amount', 'AMOUNT')
                    ttype = _get_csv_value(row, 'type', 'Type', 'TYPE', 'transaction_type')
                    if not ttype:
                        ttype = 'expense'
                    ttype = ttype.lower().strip()
                    if ttype not in ('income', 'expense'):
                        ttype = 'expense'
                    if not date_str or not amt_str:
                        continue
                    date_obj = _parse_csv_date(date_str)
                    if not date_obj:
                        errors.append(f'Row {i+2}: Invalid date "{date_str}"')
                        continue
                    amount = _parse_csv_amount(amt_str)
                    if amount is None:
                        errors.append(f'Row {i+2}: Invalid amount "{amt_str}"')
                        continue
                    if amount < 0 and ttype == 'expense':
                        amount = abs(amount)
                    elif amount < 0 and ttype == 'income':
                        amount = abs(amount)
                    category = None
                    if cat_name:
                        category = Category.objects.filter(name__iexact=cat_name).first()
                    Transaction.objects.create(
                        user=request.user,
                        amount=amount,
                        category=category,
                        type=ttype,
                        description=(desc or '')[:255],
                        date=date_obj,
                    )
                    created += 1
                except Exception as e:
                    errors.append(f'Row {i+2}: {str(e)}')
            if created:
                messages.success(request, f'Successfully imported {created} transaction(s).')
            if errors:
                for err in errors[:5]:
                    messages.warning(request, err)
            return redirect('transaction_list')
        else:
            for field, errs in form.errors.items():
                for e in errs:
                    messages.error(request, f'{field}: {e}')
    else:
        form = TransactionImportForm()
    return render(request, 'import_transactions.html', {'form': form})


@login_required
def download_sample_csv(request):
    """Download a sample CSV template for importing transactions."""
    response = HttpResponse(content_type='text/csv; charset=utf-8')
    response['Content-Disposition'] = 'attachment; filename="sample_transactions.csv"'
    writer = csv.writer(response)
    writer.writerow(['date', 'description', 'category', 'amount', 'type'])
    writer.writerow(['2025-01-15', 'Grocery shopping', 'Food', '85.50', 'expense'])
    writer.writerow(['2025-01-16', 'Salary', '', '3500.00', 'income'])
    writer.writerow(['2025-01-17', 'Restaurant dinner', 'Food', '45.00', 'expense'])
    return response
