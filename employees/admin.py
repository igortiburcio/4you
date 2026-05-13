from django.contrib import admin

from .models import Department, Employee, Position


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
    search_fields = ('name', 'registration', 'cpf', 'position__name')
    list_filter = ('status', 'department', 'hire_date')


@admin.register(Position)
class PositionAdmin(admin.ModelAdmin):
    list_display = ('name', 'department', 'base_salary', 'active')
    search_fields = ('name', 'department__name')
    list_filter = ('department', 'active')

# Register your models here.
