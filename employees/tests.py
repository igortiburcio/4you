from datetime import date

from django.contrib.auth.models import Group, User
from django.core.management import call_command
from django.test import TestCase
from django.urls import reverse

from .forms import EmployeeForm
from .models import Department, Employee, Position


class EmployeeFlowsTests(TestCase):
    def setUp(self):
        self.admin_group, _ = Group.objects.get_or_create(name='admin_rh')
        self.manager_group, _ = Group.objects.get_or_create(name='gerente')

        self.admin = User.objects.create_user(username='admin', password='12345678')
        self.admin.groups.add(self.admin_group)

        self.manager = User.objects.create_user(username='manager', password='12345678')
        self.manager.groups.add(self.manager_group)

        self.department = Department.objects.create(name='Tecnologia')
        self.position = Position.objects.create(name='Analista', department=self.department, base_salary=5000)
        self.employee = Employee.objects.create(
            registration='MAT100',
            name='Maria Lima',
            cpf='111.222.333-44',
            birth_date=date(1996, 1, 10),
            position=self.position,
            salary=5000,
            hire_date=date(2024, 1, 10),
            department=self.department,
        )

    def test_search_by_name(self):
        self.client.login(username='admin', password='12345678')
        response = self.client.get(reverse('employees:list'), {'q': 'Maria'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Maria Lima')

    def test_admin_can_create_employee(self):
        self.client.login(username='admin', password='12345678')
        response = self.client.post(
            reverse('employees:create'),
            {
                'registration': 'MAT101',
                'name': 'Joao Silva',
                'cpf': '12312312399',
                'birth_date': '1994-05-17',
                'position': self.position.pk,
                'salary': 7000,
                'hire_date': '2024-02-01',
                'department': self.department.pk,
                'status': Employee.Status.ACTIVE,
            },
        )
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Employee.objects.filter(registration='MAT101').exists())
        created = Employee.objects.get(registration='MAT101')
        self.assertEqual(created.position_id, self.position.pk)

    def test_manager_cannot_create_employee(self):
        self.client.login(username='manager', password='12345678')
        response = self.client.get(reverse('employees:create'))
        self.assertEqual(response.status_code, 302)

    def test_terminate_changes_status(self):
        self.client.login(username='admin', password='12345678')
        response = self.client.post(reverse('employees:terminate', args=[self.employee.pk]))
        self.assertEqual(response.status_code, 302)
        self.employee.refresh_from_db()
        self.assertEqual(self.employee.status, Employee.Status.TERMINATED)

    def test_duplicate_cpf_is_rejected(self):
        self.client.login(username='admin', password='12345678')
        response = self.client.post(
            reverse('employees:create'),
            {
                'registration': 'MAT102',
                'name': 'Outra Pessoa',
                'cpf': '11122233344',
                'birth_date': '1998-08-20',
                'position': self.position.pk,
                'salary': 2500,
                'hire_date': '2024-03-01',
                'department': self.department.pk,
                'status': Employee.Status.ACTIVE,
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Ja existe um funcionario com este CPF.')

    def test_analytics_page_for_admin(self):
        self.client.login(username='admin', password='12345678')
        response = self.client.get(reverse('employees:analytics'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Analises de RH')

    def test_analytics_page_for_manager(self):
        self.client.login(username='manager', password='12345678')
        response = self.client.get(reverse('employees:analytics'))
        self.assertEqual(response.status_code, 200)

    def test_admin_can_create_department(self):
        self.client.login(username='admin', password='12345678')
        response = self.client.post(
            reverse('employees:departments'),
            {
                'name': 'Operacoes',
                'description': 'Departamento operacional',
                'active': 'on',
            },
        )
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Department.objects.filter(name='Operacoes').exists())

    def test_admin_can_soft_delete_department(self):
        self.client.login(username='admin', password='12345678')
        dep = Department.objects.create(name='Marketing', active=True)

        response = self.client.post(
            reverse('employees:department-deactivate', args=[dep.pk]),
        )

        self.assertEqual(response.status_code, 302)
        dep.refresh_from_db()
        self.assertFalse(dep.active)
        self.assertTrue(Department.objects.filter(pk=dep.pk).exists())

        list_response = self.client.get(reverse('employees:departments'))
        self.assertEqual(list_response.status_code, 200)
        department_names = [department.name for department in list_response.context['departments']]
        self.assertNotIn('Marketing', department_names)

    def test_manager_cannot_soft_delete_department(self):
        self.client.login(username='manager', password='12345678')
        dep = Department.objects.create(name='Compras', active=True)

        response = self.client.post(
            reverse('employees:department-deactivate', args=[dep.pk]),
        )

        self.assertEqual(response.status_code, 302)
        dep.refresh_from_db()
        self.assertTrue(dep.active)

    def test_department_deactivation_migrates_employees_to_transitional(self):
        self.client.login(username='admin', password='12345678')
        dep = Department.objects.create(name='Operacoes', active=True)
        pos = Position.objects.create(name='Operador', department=dep, base_salary=3000, active=True)
        employee = Employee.objects.create(
            registration='MAT777',
            name='Paulo Operacao',
            cpf='987.654.321-10',
            birth_date=date(1994, 5, 3),
            position=pos,
            salary=3200,
            hire_date=date(2024, 1, 10),
            department=dep,
            status=Employee.Status.ACTIVE,
        )

        response = self.client.post(reverse('employees:department-deactivate', args=[dep.pk]))
        self.assertEqual(response.status_code, 302)

        dep.refresh_from_db()
        pos.refresh_from_db()
        employee.refresh_from_db()

        self.assertFalse(dep.active)
        self.assertFalse(pos.active)
        self.assertTrue(employee.needs_profile_update)

        transitional_dep = Department.objects.get(name='Transitorio')
        transitional_pos = Position.objects.get(
            department=transitional_dep,
            name='Cargo transitorio',
        )
        self.assertEqual(employee.department_id, transitional_dep.id)
        self.assertEqual(employee.position_id, transitional_pos.id)

    def test_employee_update_clears_profile_update_flag(self):
        self.client.login(username='admin', password='12345678')
        transitional_dep = Department.objects.create(name='Transitorio', active=True)
        transitional_pos = Position.objects.create(
            name='Cargo transitorio',
            department=transitional_dep,
            base_salary=0,
            active=True,
        )

        self.employee.department = transitional_dep
        self.employee.position = transitional_pos
        self.employee.needs_profile_update = True
        self.employee.save(update_fields=['department', 'position', 'needs_profile_update'])

        response = self.client.post(
            reverse('employees:edit', args=[self.employee.pk]),
            {
                'registration': self.employee.registration,
                'name': self.employee.name,
                'cpf': self.employee.cpf,
                'birth_date': self.employee.birth_date.strftime('%Y-%m-%d'),
                'position': self.position.pk,
                'salary': '5000.00',
                'hire_date': self.employee.hire_date.strftime('%Y-%m-%d'),
                'department': self.department.pk,
                'status': Employee.Status.ACTIVE,
            },
        )

        self.assertEqual(response.status_code, 302)
        self.employee.refresh_from_db()
        self.assertFalse(self.employee.needs_profile_update)

    def test_create_form_shows_only_active_departments(self):
        Department.objects.create(name='Inativo', active=False)
        form = EmployeeForm()
        department_names = [dep.name for dep in form.fields['department'].queryset]
        self.assertIn('Tecnologia', department_names)
        self.assertNotIn('Inativo', department_names)

    def test_edit_form_keeps_current_inactive_department_visible(self):
        self.department.active = False
        self.department.save(update_fields=['active'])

        form = EmployeeForm(instance=self.employee)
        department_ids = [dep.id for dep in form.fields['department'].queryset]
        self.assertIn(self.department.id, department_ids)

    def test_edit_form_shows_hire_date_in_html_date_format(self):
        form = EmployeeForm(instance=self.employee)
        rendered = str(form['hire_date'])
        self.assertIn('value="2024-01-10"', rendered)

    def test_create_position_and_soft_delete_position(self):
        self.client.login(username='admin', password='12345678')
        response = self.client.post(
            reverse('employees:position-create', args=[self.department.pk]),
            {
                'department': self.department.pk,
                'name': 'Tech Lead',
                'base_salary': '8000.00',
                'active': 'on',
            },
        )
        self.assertEqual(response.status_code, 302)
        position = Position.objects.get(department=self.department, name='Tech Lead')
        self.assertTrue(position.active)

        response = self.client.post(reverse('employees:position-deactivate', args=[position.pk]))
        self.assertEqual(response.status_code, 302)
        position.refresh_from_db()
        self.assertFalse(position.active)

    def test_department_detail_lists_positions_and_base_salary(self):
        self.client.login(username='admin', password='12345678')
        self.position.base_salary = 4500
        self.position.save(update_fields=['base_salary'])

        response = self.client.get(reverse('employees:department-detail', args=[self.department.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Cargos do departamento')
        self.assertContains(response, '4500')

    def test_position_base_salary_endpoint(self):
        self.client.login(username='admin', password='12345678')
        self.position.base_salary = 5000
        self.position.save(update_fields=['base_salary'])

        response = self.client.get(reverse('employees:position-base-salary', args=[self.position.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['base_salary'], 5000.0)

    def test_employee_create_ajax_positions_only_from_selected_department(self):
        self.client.login(username='admin', password='12345678')
        finance = Department.objects.create(name='Financeiro')
        Position.objects.create(name='Analista Financeiro', department=finance, base_salary=4200)

        response = self.client.get(
            reverse('employees:create'),
            {'department': self.department.pk},
            HTTP_X_REQUESTED_WITH='XMLHttpRequest',
        )
        self.assertEqual(response.status_code, 200)
        payload = response.json()['positions']
        names = [item['text'] for item in payload]
        self.assertIn('Analista', names)
        self.assertNotIn('Analista Financeiro', names)

    def test_employee_form_rejects_position_from_other_department(self):
        finance = Department.objects.create(name='Financeiro')
        finance_position = Position.objects.create(name='Analista Financeiro', department=finance)

        form = EmployeeForm(
            data={
                'registration': 'MAT103',
                'name': 'Carlos Teste',
                'cpf': '98765432100',
                'birth_date': '1990-01-01',
                'position': finance_position.pk,
                'salary': 5000,
                'hire_date': '2024-01-01',
                'department': self.department.pk,
                'status': Employee.Status.ACTIVE,
            }
        )
        self.assertFalse(form.is_valid())
        self.assertIn('position', form.errors)

    def test_seed_creates_superadmin_with_full_access_and_group(self):
        call_command('seed_initial_data')
        superadmin = User.objects.get(username='superadmin')
        self.assertTrue(superadmin.is_active)
        self.assertTrue(superadmin.is_staff)
        self.assertTrue(superadmin.is_superuser)
        self.assertTrue(superadmin.groups.filter(name='admin_rh').exists())
