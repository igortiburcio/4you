from django.contrib import admin

from .models import Department, Employee


@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ('name', 'active', 'updated_at')
    search_fields = ('name',)
    list_filter = ('active',)


@admin.register(Employee)
class EmployeeAdmin(admin.ModelAdmin):
    list_display = (
        'name',
        'registration',
        'cpf',
        'position',
        'department',
        'status',
    )
    search_fields = ('name', 'registration', 'cpf', 'position')
    list_filter = ('status', 'department', 'hire_date')

# Register your models here.
