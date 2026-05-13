from datetime import date

from django.db import migrations


def _estimate_birth_date(age):
    today = date.today()
    year = today.year - age
    try:
        return date(year, 7, 1)
    except ValueError:
        return date(year, 6, 30)


def forwards(apps, schema_editor):
    Employee = apps.get_model('employees', 'Employee')
    Position = apps.get_model('employees', 'Position')

    for employee in Employee.objects.select_related('department').all():
        position_name = (employee.position or '').strip() or 'Sem cargo'
        department = employee.department

        position_obj, _ = Position.objects.get_or_create(
            department=department,
            name=position_name,
            defaults={'active': True},
        )

        age = getattr(employee, 'age', None)
        if age is not None:
            employee.birth_date = _estimate_birth_date(age)
        elif employee.birth_date is None:
            employee.birth_date = date(2000, 1, 1)

        employee.position_ref_id = position_obj.id
        employee.save(update_fields=['birth_date', 'position_ref'])


def backwards(apps, schema_editor):
    return


class Migration(migrations.Migration):
    dependencies = [
        ('employees', '0003_remove_employee_age_employee_birth_date_position_and_more'),
    ]

    operations = [
        migrations.RunPython(forwards, backwards),
    ]
