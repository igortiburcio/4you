import re

from django import forms
from django.db.models import Q

from .models import Department, Employee


class DepartmentForm(forms.ModelForm):
    class Meta:
        model = Department
        fields = ['name', 'description', 'active']
        labels = {
            'name': 'Nome',
            'description': 'Descricao',
            'active': 'Ativo',
        }


class EmployeeForm(forms.ModelForm):
    class Meta:
        model = Employee
        fields = [
            'registration',
            'name',
            'cpf',
            'age',
            'position',
            'salary',
            'hire_date',
            'department',
            'status',
        ]
        widgets = {
            'hire_date': forms.DateInput(
                format='%Y-%m-%d',
                attrs={'type': 'date'},
            ),
        }
        labels = {
            'registration': 'Matricula',
            'name': 'Nome',
            'cpf': 'CPF',
            'age': 'Idade',
            'position': 'Cargo',
            'salary': 'Salario',
            'hire_date': 'Data de admissao',
            'department': 'Departamento',
            'status': 'Status',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['hire_date'].input_formats = ['%Y-%m-%d', '%d/%m/%Y']
        active_departments = Department.objects.filter(active=True)

        if self.instance and self.instance.pk and self.instance.department_id:
            self.fields['department'].queryset = Department.objects.filter(
                Q(active=True) | Q(pk=self.instance.department_id)
            ).order_by('name')
            return

        self.fields['department'].queryset = active_departments.order_by('name')

    def clean_cpf(self):
        cpf = re.sub(r'\D', '', self.cleaned_data['cpf'])
        if len(cpf) != 11:
            raise forms.ValidationError('CPF deve conter 11 digitos.')

        formatted = f'{cpf[:3]}.{cpf[3:6]}.{cpf[6:9]}-{cpf[9:]}'

        queryset = Employee.objects.filter(cpf=formatted)
        if self.instance.pk:
            queryset = queryset.exclude(pk=self.instance.pk)
        if queryset.exists():
            raise forms.ValidationError('Ja existe um funcionario com este CPF.')
        return formatted

    def clean_registration(self):
        registration = self.cleaned_data['registration'].strip()
        queryset = Employee.objects.filter(registration=registration)
        if self.instance.pk:
            queryset = queryset.exclude(pk=self.instance.pk)
        if queryset.exists():
            raise forms.ValidationError('Matricula ja cadastrada.')
        return registration
