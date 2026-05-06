from datetime import date

from django.contrib.auth.models import Group, User
from django.test import TestCase
from django.urls import reverse

from .models import Department, Employee


class EmployeeFlowsTests(TestCase):
    def setUp(self):
        self.admin_group, _ = Group.objects.get_or_create(name='admin_rh')
        self.manager_group, _ = Group.objects.get_or_create(name='gerente')

        self.admin = User.objects.create_user(username='admin', password='12345678')
        self.admin.groups.add(self.admin_group)

        self.manager = User.objects.create_user(username='manager', password='12345678')
        self.manager.groups.add(self.manager_group)

        self.department = Department.objects.create(name='Tecnologia')
        self.employee = Employee.objects.create(
            registration='MAT100',
            name='Maria Lima',
            cpf='111.222.333-44',
            age=28,
            position='Analista',
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
                'age': 30,
                'position': 'Dev',
                'salary': 7000,
                'hire_date': '2024-02-01',
                'department': self.department.pk,
                'status': Employee.Status.ACTIVE,
            },
        )
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Employee.objects.filter(registration='MAT101').exists())

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
                'age': 26,
                'position': 'Assistente',
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
