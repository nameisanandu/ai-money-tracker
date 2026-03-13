"""
AI Expense Analyzer - Analyzes spending patterns and generates financial insights.
Uses pandas for data analysis.
"""
import pandas as pd


def transactions_to_dataframe(transactions):
    """
    Convert queryset of transactions into a pandas DataFrame.

    Args:
        transactions: Django QuerySet of Transaction objects

    Returns:
        pandas DataFrame with transaction data
    """
    if not transactions:
        return pd.DataFrame()

    data = []
    for t in transactions:
        data.append({
            'amount': float(t.amount),
            'category': t.category.name if t.category else 'Uncategorized',
            'type': t.type,
            'description': t.description or '',
            'date': t.date,
        })

    return pd.DataFrame(data)


def analyze_expense_patterns(transactions, threshold=0.4):
    """
    Analyze spending patterns and detect categories exceeding threshold.

    Args:
        transactions: Django QuerySet of Transaction objects (typically expenses only)
        threshold: Percentage threshold (default 0.4 = 40%)

    Returns:
        List of natural language insight strings
    """
    insights = []

    if not transactions:
        insights.append("No expense data to analyze yet. Add some expenses to get AI insights.")
        return insights

    df = transactions_to_dataframe(transactions)

    if df.empty or 'expense' not in df['type'].values:
        expense_df = df[df['type'] == 'expense'] if 'type' in df.columns else df
        if expense_df.empty:
            insights.append("No expense data to analyze yet.")
            return insights

    expense_df = df[df['type'] == 'expense'] if 'type' in df.columns else df
    total_expenses = expense_df['amount'].sum()

    if total_expenses <= 0:
        insights.append("Your total expenses are zero or negative. Great savings!")
        return insights

    category_totals = expense_df.groupby('category')['amount'].sum()

    for category, amount in category_totals.items():
        percentage = (amount / total_expenses) * 100
        if percentage >= (threshold * 100):
            insights.append(
                f"You spent {percentage:.1f}% of your expenses on {category} this month. "
                f"Consider reducing spending in this category."
            )

    if not insights:
        insights.append(
            "Your spending is well-distributed across categories. "
            "No single category exceeds 40% of total expenses."
        )

    return insights


def detect_expense_anomalies(transactions, multiplier=2.0):
    """
    Detect unusually large transactions (e.g., 2x larger than average expense).

    Args:
        transactions: Django QuerySet of Transaction objects
        multiplier: Threshold multiplier (default 2.0 = 2x average)

    Returns:
        List of anomaly insight strings
    """
    insights = []
    df = transactions_to_dataframe(transactions)
    expense_df = df[df['type'] == 'expense'] if 'type' in df.columns else pd.DataFrame()

    if expense_df.empty or len(expense_df) < 2:
        return insights

    avg_expense = expense_df['amount'].mean()
    if avg_expense <= 0:
        return insights

    for _, row in expense_df.iterrows():
        if row['amount'] >= multiplier * avg_expense:
            insights.append(
                f"Unusual expense detected: Rs {row['amount']:.2f} on {row['category']} "
                f"({row['amount'] / avg_expense:.1f}x your average). "
                f"Description: {row['description'] or 'N/A'}"
            )

    return insights[:3]


def get_personalized_suggestions(transactions):
    """
    Generate personalized financial suggestions based on spending patterns.

    Args:
        transactions: Django QuerySet of Transaction objects

    Returns:
        List of suggestion strings
    """
    suggestions = []
    df = transactions_to_dataframe(transactions)
    expense_df = df[df['type'] == 'expense'] if 'type' in df.columns else pd.DataFrame()

    if expense_df.empty or expense_df['amount'].sum() <= 0:
        return suggestions

    total = expense_df['amount'].sum()
    category_totals = expense_df.groupby('category')['amount'].sum()

    for cat in ['Shopping', 'Food', 'Travel', 'Entertainment']:
        if cat in category_totals.index:
            pct = (category_totals[cat] / total) * 100
            if pct > 25:
                suggestions.append(
                    f"You spend a large portion on {cat} ({pct:.1f}%). "
                    f"Consider setting a {cat.lower()} budget."
                )

    return suggestions[:3]


def get_financial_insights(transactions, loans=None):
    """
    Generate comprehensive natural language financial insights from transactions.
    Includes: spending concentration, anomaly detection, personalized suggestions.

    Args:
        transactions: Django QuerySet of Transaction objects
        loans: optional queryset/list of Loan objects

    Returns:
        List of insight strings for display on dashboard
    """
    if not transactions:
        return ["Add transactions to receive AI-powered spending insights."]

    df = transactions_to_dataframe(transactions)

    if df.empty:
        return ["Add transactions to receive AI-powered spending insights."]

    if 'date' in df.columns:
        df['date'] = pd.to_datetime(df['date'], errors='coerce')

    insights = []
    insights.extend(analyze_expense_patterns(transactions, threshold=0.4))
    insights.extend(detect_expense_anomalies(transactions, multiplier=2.0))
    insights.extend(get_personalized_suggestions(transactions))

    expense_df = df[df['type'] == 'expense'].copy()
    income_df = df[df['type'] == 'income'].copy()

    if not expense_df.empty and 'date' in expense_df.columns:
        expense_df['date'] = pd.to_datetime(expense_df['date'], errors='coerce')
    if not income_df.empty and 'date' in income_df.columns:
        income_df['date'] = pd.to_datetime(income_df['date'], errors='coerce')

    total_income = income_df['amount'].sum()
    total_expense = expense_df['amount'].sum()
    balance = total_income - total_expense

    if total_expense > 0 and total_income > 0:
        savings_rate = (balance / total_income) * 100
        if savings_rate > 20:
            insights.append(
                f"Great job! You're saving {savings_rate:.1f}% of your income. "
                "Keep up the good financial habits."
            )
        elif savings_rate < 0:
            insights.append(
                "Your expenses exceed your income. Consider cutting back on non-essential spending "
                "or finding ways to increase income."
            )

    if not expense_df.empty and 'date' in expense_df.columns:
        this_week = expense_df[expense_df['date'] >= (expense_df['date'].max() - pd.Timedelta(days=7))]
        monthly_avg = total_expense / max(1, len(expense_df['date'].dt.to_period('M').unique()))
        if len(this_week) > 0:
            week_total = this_week['amount'].sum()
            if monthly_avg > 0 and week_total > monthly_avg * 0.5:
                insights.append(
                    f"You spent unusually high this week (Rs {week_total:.0f}) compared to your "
                    "monthly average. Review recent transactions."
                )

    if loans:
        total_monthly_emi = sum(getattr(loan, 'emi_amount', 0) for loan in loans)
        if total_monthly_emi and total_income > 0 and not income_df.empty:
            avg_monthly_income = total_income / max(1, len(income_df['date'].dt.to_period('M').unique()))
            if avg_monthly_income > 0:
                emi_pct = (total_monthly_emi / avg_monthly_income) * 100
                if emi_pct >= 40:
                    insights.append(
                        f"Your monthly EMIs (Rs {total_monthly_emi:.0f}) are {emi_pct:.1f}% of your average monthly income. "
                        "High EMI burden can impact savings; consider reducing debt or refinancing."
                    )

        for loan in loans:
            overdue_count = getattr(loan, 'overdue_emis', lambda: 0)()
            next_emi = getattr(loan, 'next_emi', lambda: None)()
            rem_emis = getattr(loan, 'remaining_emis', lambda: 0)()

            if overdue_count > 0:
                insights.append(
                    f"{loan.loan_name} has {overdue_count} overdue EMI(s). Prioritize clearing overdue payments "
                    "to keep the loan on track."
                )

            if rem_emis > 0:
                due_hint = ""
                if next_emi is not None:
                    due_hint = f" Next EMI due on {next_emi.payment_date.strftime('%b %d, %Y')}."
                insights.append(
                    f"You have {rem_emis} EMIs remaining on \"{loan.loan_name}\". "
                    f"Approximate remaining balance is Rs {loan.remaining_balance():.0f}.{due_hint}"
                )

    return insights[:10]
