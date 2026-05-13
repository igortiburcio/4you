from django.db import models
from django.db.models import Q


class Department(models.Model):
    name = models.CharField(max_length=120)
    description = models.TextField(blank=True)
    active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name


class Position(models.Model):
    name = models.CharField(max_length=120)
    base_salary = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    department = models.ForeignKey(
        Department,
        on_delete=models.PROTECT,
        related_name='positions',
    )
    active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']
        constraints = [
            models.UniqueConstraint(
                fields=['department', 'name'],
                name='unique_position_per_department',
            ),
            models.CheckConstraint(
                check=Q(base_salary__gte=0),
                name='position_base_salary_non_negative',
            ),
        ]

    def __str__(self):
        return f'{self.name} - {self.department.name}'


class Employee(models.Model):
    class Status(models.TextChoices):
        ACTIVE = 'active', 'Ativo'
        TERMINATED = 'terminated', 'Desligado'

    registration = models.CharField(max_length=20, unique=True)
    name = models.CharField(max_length=180)
    cpf = models.CharField(max_length=14, unique=True)
    birth_date = models.DateField()
    position = models.ForeignKey(
        Position,
        on_delete=models.PROTECT,
        related_name='employees',
    )
    salary = models.DecimalField(max_digits=10, decimal_places=2)
    hire_date = models.DateField()
    department = models.ForeignKey(
        Department,
        on_delete=models.PROTECT,
        related_name='employees',
    )
    status = models.CharField(
        max_length=12,
        choices=Status.choices,
        default=Status.ACTIVE,
    )
    needs_profile_update = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']
        constraints = [
            models.CheckConstraint(
                check=Q(salary__gte=0),
                name='employee_salary_non_negative',
            )
        ]

    def __str__(self):
        return f'{self.name} ({self.registration})'
