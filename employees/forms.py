import re

from django import forms

from .models import Department, Employee


class DepartmentForm(forms.ModelForm):
    class Meta:
        model = Department
        fields = ['name', 'description', 'active']


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
            'hire_date': forms.DateInput(attrs={'type': 'date'}),
        }

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
