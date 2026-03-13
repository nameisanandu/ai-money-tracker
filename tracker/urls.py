"""
URL configuration for tracker app.
"""
from django.urls import path
from . import views

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('add/', views.add_transaction, name='add_transaction'),
    path('transactions/', views.transaction_list, name='transaction_list'),
    path('transactions/<int:pk>/edit/', views.edit_transaction, name='edit_transaction'),
    path('transactions/<int:pk>/delete/', views.delete_transaction, name='delete_transaction'),
    path('budget/', views.set_budget, name='set_budget'),
    path('export/csv/', views.export_transactions_csv, name='export_csv'),
    path('export/excel/', views.export_excel, name='export_excel'),
    path('import/', views.import_transactions, name='import_transactions'),
    path('import/sample/', views.download_sample_csv, name='download_sample_csv'),
    path('loans/', views.loan_list, name='loan_list'),
    path('loans/add/', views.add_loan, name='add_loan'),
    path('loans/<int:pk>/edit/', views.edit_loan, name='edit_loan'),
    path('loans/<int:pk>/delete/', views.delete_loan, name='delete_loan'),
    path('loans/<int:pk>/extra-payment/', views.add_extra_payment, name='add_extra_payment'),
    path('loans/<int:pk>/', views.loan_detail, name='loan_detail'),
    path('loans/emis/', views.emi_payments, name='emi_payments'),
    path('loans/emis/<int:pk>/edit/', views.edit_emi_payment, name='edit_emi_payment'),
    path('loans/emis/<int:pk>/mark-paid/', views.mark_emi_paid, name='mark_emi_paid'),
    path('register/', views.register_user, name='register'),
    path('login/', views.login_user, name='login'),
    path('logout/', views.logout_user, name='logout'),
]
