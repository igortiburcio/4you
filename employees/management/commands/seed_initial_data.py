from django.contrib.auth.models import Group, User
from django.core.management.base import BaseCommand

from employees.models import Department, Employee, Position


class Command(BaseCommand):
    help = 'Cria grupos, admin inicial, departamentos e funcionarios de exemplo.'

    def handle(self, *args, **options):
        for group_name in ['admin_rh', 'gerente', 'funcionario']:
            Group.objects.get_or_create(name=group_name)

        admin_user, created = User.objects.get_or_create(
            username='admin.rh',
            defaults={
                'first_name': 'Admin',
                'last_name': 'RH',
                'email': 'adminrh@4you.local',
            },
        )
        if created:
            admin_user.set_password('admin1234')
            admin_user.is_staff = True
            admin_user.save()

        admin_group = Group.objects.get(name='admin_rh')
        admin_user.groups.add(admin_group)

        superadmin_user, superadmin_created = User.objects.get_or_create(
            username='superadmin',
            defaults={
                'first_name': 'Super',
                'last_name': 'Admin',
                'email': 'superadmin@4you.local',
            },
        )
        if superadmin_created:
            superadmin_user.set_password('superadmin1234')

        superadmin_user.is_active = True
        superadmin_user.is_staff = True
        superadmin_user.is_superuser = True
        superadmin_user.save()
        superadmin_user.groups.add(admin_group)

        departments = [
            'Tecnologia',
            'Financeiro',
            'Juridico',
            'Vendas',
            'RH',
        ]
        department_objects = {}
        for dep in departments:
            department, _ = Department.objects.get_or_create(name=dep)
            department_objects[dep] = department

        positions_by_department = {
            'Tecnologia': ['Desenvolvedor', 'Tech Lead', 'QA'],
            'Financeiro': ['Financeiro Jr', 'Analista Financeiro'],
            'Juridico': ['Assistente Juridico', 'Analista Juridico'],
            'Vendas': ['Gerente Comercial', 'Executivo de Vendas'],
            'RH': ['Analista RH', 'Coordenador RH'],
        }
        position_objects = {}
        for dep_name, position_names in positions_by_department.items():
            for position_name in position_names:
                position, _ = Position.objects.get_or_create(
                    department=department_objects[dep_name],
                    name=position_name,
                    defaults={'active': True},
                )
                position_objects[(dep_name, position_name)] = position

        if not Employee.objects.exists():
            samples = [
                ('MAT001', 'Ana Souza', '123.456.789-01', '1995-07-01', 'Analista RH', 4200.00, 'RH'),
                ('MAT002', 'Bruno Lima', '123.456.789-02', '1990-07-01', 'Desenvolvedor', 6800.00, 'Tecnologia'),
                ('MAT003', 'Carla Nunes', '123.456.789-03', '1993-07-01', 'Financeiro Jr', 3900.00, 'Financeiro'),
                ('MAT004', 'Diego Rocha', '123.456.789-04', '1984-07-01', 'Gerente Comercial', 9200.00, 'Vendas'),
                ('MAT005', 'Elisa Prado', '123.456.789-05', '1997-07-01', 'Assistente Juridico', 3500.00, 'Juridico'),
            ]
            for reg, name, cpf, birth_date, position_name, salary, dep in samples:
                Employee.objects.create(
                    registration=reg,
                    name=name,
                    cpf=cpf,
                    birth_date=birth_date,
                    position=position_objects[(dep, position_name)],
                    salary=salary,
                    hire_date='2024-01-15',
                    department=department_objects[dep],
                    status=Employee.Status.ACTIVE,
                )

        self.stdout.write(self.style.SUCCESS('Seed inicial concluido com sucesso.'))
        self.stdout.write(self.style.SUCCESS('Usuario superadmin garantido com acesso total.'))
