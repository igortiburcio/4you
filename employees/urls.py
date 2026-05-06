from django.urls import path

from .views import (
    EmployeeAnalyticsView,
    DepartmentListCreateView,
    EmployeeCreateView,
    EmployeeListView,
    EmployeeTerminateView,
    EmployeeUpdateView,
)

app_name = 'employees'

urlpatterns = [
    path('', EmployeeListView.as_view(), name='list'),
    path('new/', EmployeeCreateView.as_view(), name='create'),
    path('<int:pk>/edit/', EmployeeUpdateView.as_view(), name='edit'),
    path('<int:pk>/terminate/', EmployeeTerminateView.as_view(), name='terminate'),
    path('departments/', DepartmentListCreateView.as_view(), name='departments'),
    path('analytics/', EmployeeAnalyticsView.as_view(), name='analytics'),
]
