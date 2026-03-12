"""
Expense Prediction Module - Uses Linear Regression to predict next month's expenses.
"""
from decimal import Decimal
import numpy as np
from django.db.models import Sum
from django.db.models.functions import TruncMonth


def predict_next_month_expense(transactions_queryset):
    """
    Predict next month's expenses using scikit-learn Linear Regression.

    Args:
        transactions_queryset: Django QuerySet of Transaction objects (filtered by user)

    Returns:
        Predicted amount as float, or None if insufficient data
    """
    try:
        from sklearn.linear_model import LinearRegression
    except ImportError:
        return None

    expense_qs = transactions_queryset.filter(type='expense')
    monthly = (
        expense_qs
        .annotate(month=TruncMonth('date'))
        .values('month')
        .annotate(total=Sum('amount'))
        .order_by('month')
    )

    data = list(monthly)
    if len(data) < 2:
        return None

    X = np.array([[i] for i in range(len(data))])
    y = np.array([float(d['total']) for d in data])

    model = LinearRegression()
    model.fit(X, y)

    next_idx = len(data)
    prediction = model.predict([[next_idx]])[0]
    return max(0, float(prediction))
