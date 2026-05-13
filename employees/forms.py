import re

from django import forms
from django.db.models import Q
from django.utils import timezone

from .models import Department, Employee, Position


class DepartmentForm(forms.ModelForm):
    class Meta:
        model = Department
        fields = ['name', 'description', 'active']
        labels = {
            'name': 'Nome',
            'description': 'Descricao',
            'active': 'Ativo',
        }


class PositionForm(forms.ModelForm):
    class Meta:
        model = Position
        fields = ['department', 'name', 'base_salary', 'active']
        labels = {
            'department': 'Departamento',
            'name': 'Cargo',
            'base_salary': 'Salario base',
            'active': 'Ativo',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['department'].queryset = Department.objects.filter(active=True).order_by('name')

    def clean(self):
        cleaned_data = super().clean()
        department = cleaned_data.get('department')
        name = (cleaned_data.get('name') or '').strip()
        if not department or not name:
            return cleaned_data

        queryset = Position.objects.filter(department=department, name__iexact=name)
        if self.instance.pk:
            queryset = queryset.exclude(pk=self.instance.pk)
        if queryset.exists():
            raise forms.ValidationError('Este cargo ja existe neste departamento.')
        cleaned_data['name'] = name
        return cleaned_data


class DepartmentPositionForm(forms.ModelForm):
    class Meta:
        model = Position
        fields = ['name', 'base_salary', 'active']
        labels = {
            'name': 'Cargo',
            'base_salary': 'Salario base',
            'active': 'Ativo',
        }

    def __init__(self, *args, department=None, **kwargs):
        self.department = department
        super().__init__(*args, **kwargs)

    def clean_name(self):
        name = (self.cleaned_data['name'] or '').strip()
        if not self.department or not name:
            return name
        queryset = Position.objects.filter(
            department=self.department,
            name__iexact=name,
        )
        if self.instance.pk:
            queryset = queryset.exclude(pk=self.instance.pk)
        if queryset.exists():
            raise forms.ValidationError('Este cargo ja existe neste departamento.')
        return name

    def save(self, commit=True):
        obj = super().save(commit=False)
        obj.department = self.department
        if commit:
            obj.save()
        return obj


class EmployeeForm(forms.ModelForm):
    class Meta:
        model = Employee
        fields = [
            'registration',
            'name',
            'cpf',
            'birth_date',
            'position',
            'salary',
            'hire_date',
            'department',
            'status',
        ]
        widgets = {
            'birth_date': forms.DateInput(
                format='%Y-%m-%d',
                attrs={'type': 'date'},
            ),
            'hire_date': forms.DateInput(
                format='%Y-%m-%d',
                attrs={'type': 'date'},
            ),
        }
        labels = {
            'registration': 'Matricula',
            'name': 'Nome',
            'cpf': 'CPF',
            'department': 'Departamento',
            'birth_date': 'Data de nascimento',
            'position': 'Cargo',
            'salary': 'Salario',
            'hire_date': 'Data de admissao',
            'status': 'Status',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['birth_date'].input_formats = ['%Y-%m-%d', '%d/%m/%Y']
        self.fields['hire_date'].input_formats = ['%Y-%m-%d', '%d/%m/%Y']
        active_departments = Department.objects.filter(active=True)

        selected_department_id = None
        if self.is_bound:
            selected_department_id = self.data.get('department')
        elif self.instance and self.instance.pk:
            selected_department_id = self.instance.department_id

        if selected_department_id:
            self.fields['position'].queryset = Position.objects.filter(
                Q(active=True) | Q(pk=getattr(self.instance, 'position_id', None)),
                department_id=selected_department_id,
            ).select_related('department').order_by('name')
        else:
            self.fields['position'].queryset = Position.objects.none()

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

    def clean(self):
        cleaned_data = super().clean()
        department = cleaned_data.get('department')
        position = cleaned_data.get('position')
        birth_date = cleaned_data.get('birth_date')
        hire_date = cleaned_data.get('hire_date')
        if not department or not position:
            return cleaned_data

        if position.department_id != department.id:
            self.add_error('position', 'O cargo selecionado nao pertence ao departamento informado.')

        if birth_date and birth_date > timezone.localdate():
            self.add_error('birth_date', 'Data de nascimento nao pode estar no futuro.')

        if hire_date and birth_date and hire_date < birth_date:
            self.add_error('hire_date', 'Data de admissao nao pode ser anterior a data de nascimento.')

        return cleaned_data
