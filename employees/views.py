from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.core.paginator import Paginator
from django.db.models import Case, Count
from django.db.models import CharField
from django.db.models import Q
from django.db.models import Value, When
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy
from django.views import View
from django.views.generic import CreateView, ListView, TemplateView, UpdateView

from .forms import DepartmentForm, EmployeeForm, PositionForm
from .models import Department, Employee, Position


class GroupRequiredMixin(UserPassesTestMixin):
    allowed_groups = []

    def test_func(self):
        user = self.request.user
        return user.is_superuser or user.groups.filter(
            name__in=self.allowed_groups
        ).exists()

    def handle_no_permission(self):
        messages.error(self.request, 'Voce nao tem permissao para esta acao.')
        return redirect('employees:list')


class EmployeeListView(LoginRequiredMixin, ListView):
    model = Employee
    template_name = 'employees/list.html'
    context_object_name = 'employees'
    paginate_by = 10

    def get_queryset(self):
        queryset = (
            Employee.objects.select_related('department')
            .all()
            .order_by('name')
        )
        query = self.request.GET.get('q', '').strip()
        status = self.request.GET.get('status', '').strip()
        if query:
            queryset = queryset.filter(
                Q(name__icontains=query)
                | Q(position__name__icontains=query)
                | Q(registration__icontains=query)
                | Q(cpf__icontains=query)
            )
        if status in {Employee.Status.ACTIVE, Employee.Status.TERMINATED}:
            queryset = queryset.filter(status=status)
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['query'] = self.request.GET.get('q', '').strip()
        context['status_filter'] = self.request.GET.get('status', '').strip()
        context['can_manage_employees'] = self.request.user.is_superuser or self.request.user.groups.filter(
            name='admin_rh'
        ).exists()
        salaries = [employee.salary for employee in context.get('employees', [])]
        context['max_salary'] = max(salaries) if salaries else 0
        return context

    def render_to_response(self, context, **response_kwargs):
        if self.request.headers.get('HX-Request') == 'true':
            return render(self.request, 'employees/partials/table.html', context)
        return super().render_to_response(context, **response_kwargs)


class EmployeeCreateView(LoginRequiredMixin, GroupRequiredMixin, CreateView):
    model = Employee
    form_class = EmployeeForm
    template_name = 'employees/form.html'
    success_url = reverse_lazy('employees:list')
    allowed_groups = ['admin_rh']

    def form_valid(self, form):
        messages.success(self.request, 'Funcionario cadastrado com sucesso.')
        return super().form_valid(form)


class EmployeeUpdateView(LoginRequiredMixin, GroupRequiredMixin, UpdateView):
    model = Employee
    form_class = EmployeeForm
    template_name = 'employees/form.html'
    success_url = reverse_lazy('employees:list')
    allowed_groups = ['admin_rh']

    def form_valid(self, form):
        messages.success(self.request, 'Funcionario atualizado com sucesso.')
        return super().form_valid(form)


class EmployeeTerminateView(LoginRequiredMixin, GroupRequiredMixin, View):
    allowed_groups = ['admin_rh']

    def post(self, request, pk):
        employee = get_object_or_404(Employee, pk=pk)
        employee.status = Employee.Status.TERMINATED
        employee.save(update_fields=['status', 'updated_at'])
        messages.success(request, f'Funcionario {employee.name} foi desligado.')

        if request.headers.get('HX-Request') == 'true':
            queryset = Employee.objects.select_related('department').order_by('name')
            query = request.GET.get('q', '').strip()
            status = request.GET.get('status', '').strip()
            if query:
                queryset = queryset.filter(
                    Q(name__icontains=query)
                    | Q(position__name__icontains=query)
                    | Q(registration__icontains=query)
                    | Q(cpf__icontains=query)
                )
            if status in {Employee.Status.ACTIVE, Employee.Status.TERMINATED}:
                queryset = queryset.filter(status=status)

            paginator = Paginator(queryset, 10)
            page_obj = paginator.get_page(request.GET.get('page'))

            return render(
                request,
                'employees/partials/table.html',
                {
                    'page_obj': page_obj,
                    'employees': page_obj.object_list,
                    'query': query,
                    'status_filter': status,
                    'max_salary': max(
                        [employee.salary for employee in page_obj.object_list],
                        default=0,
                    ),
                    'can_manage_employees': request.user.is_superuser
                    or request.user.groups.filter(name='admin_rh').exists(),
                    'is_paginated': page_obj.has_other_pages(),
                },
            )
        return HttpResponseRedirect(reverse_lazy('employees:list'))


class DepartmentListCreateView(LoginRequiredMixin, GroupRequiredMixin, View):
    allowed_groups = ['admin_rh']
    template_name = 'employees/departments.html'

    def get(self, request):
        form = DepartmentForm()
        position_form = PositionForm()
        departments = Department.objects.filter(active=True)
        positions = Position.objects.filter(active=True).select_related('department').order_by('department__name', 'name')
        return render(
            request,
            self.template_name,
            {
                'form': form,
                'departments': departments,
                'position_form': position_form,
                'positions': positions,
            },
        )

    def post(self, request):
        form = DepartmentForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Departamento criado com sucesso.')
            return redirect('employees:departments')
        departments = Department.objects.filter(active=True)
        position_form = PositionForm()
        positions = Position.objects.filter(active=True).select_related('department').order_by('department__name', 'name')
        return render(
            request,
            self.template_name,
            {
                'form': form,
                'departments': departments,
                'position_form': position_form,
                'positions': positions,
            },
        )


class DepartmentDeactivateView(LoginRequiredMixin, GroupRequiredMixin, View):
    allowed_groups = ['admin_rh']

    def post(self, request, pk):
        department = get_object_or_404(Department, pk=pk)
        if not department.active:
            messages.info(request, 'Departamento ja esta inativo.')
            return redirect('employees:departments')

        department.active = False
        department.save(update_fields=['active', 'updated_at'])
        messages.success(request, f'Departamento {department.name} foi inativado.')
        return redirect('employees:departments')


class PositionCreateView(LoginRequiredMixin, GroupRequiredMixin, View):
    allowed_groups = ['admin_rh']

    def post(self, request):
        form = PositionForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Cargo criado com sucesso.')
        else:
            messages.error(request, form.errors.as_text())
        return redirect('employees:departments')


class PositionDeactivateView(LoginRequiredMixin, GroupRequiredMixin, View):
    allowed_groups = ['admin_rh']

    def post(self, request, pk):
        position = get_object_or_404(Position, pk=pk)
        if not position.active:
            messages.info(request, 'Cargo ja esta inativo.')
            return redirect('employees:departments')

        position.active = False
        position.save(update_fields=['active', 'updated_at'])
        messages.success(request, f'Cargo {position.name} foi inativado.')
        return redirect('employees:departments')


class EmployeeAnalyticsView(LoginRequiredMixin, GroupRequiredMixin, TemplateView):
    template_name = 'employees/analytics.html'
    allowed_groups = ['admin_rh', 'gerente']

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        departments_data = (
            Department.objects.filter(active=True)
            .annotate(total=Count('employees'))
            .order_by('name')
        )

        status_data = (
            Employee.objects.values('status')
            .annotate(total=Count('id'))
            .order_by('status')
        )

        salary_range_data = (
            Employee.objects.annotate(
                salary_range=Case(
                    When(salary__lt=2000, then=Value('Ate R$ 1.999')),
                    When(
                        salary__gte=2000,
                        salary__lt=3000,
                        then=Value('R$ 2.000 a R$ 2.999'),
                    ),
                    When(
                        salary__gte=3000,
                        salary__lt=4000,
                        then=Value('R$ 3.000 a R$ 3.999'),
                    ),
                    When(
                        salary__gte=4000,
                        salary__lt=5000,
                        then=Value('R$ 4.000 a R$ 4.999'),
                    ),
                    When(
                        salary__gte=5000,
                        salary__lt=6500,
                        then=Value('R$ 5.000 a R$ 6.499'),
                    ),
                    When(
                        salary__gte=6500,
                        salary__lt=8000,
                        then=Value('R$ 6.500 a R$ 7.999'),
                    ),
                    When(
                        salary__gte=8000,
                        salary__lt=10000,
                        then=Value('R$ 8.000 a R$ 9.999'),
                    ),
                    default=Value('R$ 10.000 ou mais'),
                    output_field=CharField(),
                )
            )
            .values('salary_range')
            .annotate(total=Count('id'))
        )

        status_labels_map = {
            Employee.Status.ACTIVE: 'Ativos',
            Employee.Status.TERMINATED: 'Desligados',
        }

        context['department_labels'] = [item.name for item in departments_data]
        context['department_counts'] = [item.total for item in departments_data]
        context['status_labels'] = [status_labels_map[item['status']] for item in status_data]
        context['status_counts'] = [item['total'] for item in status_data]
        salary_range_order = [
            'Ate R$ 1.999',
            'R$ 2.000 a R$ 2.999',
            'R$ 3.000 a R$ 3.999',
            'R$ 4.000 a R$ 4.999',
            'R$ 5.000 a R$ 6.499',
            'R$ 6.500 a R$ 7.999',
            'R$ 8.000 a R$ 9.999',
            'R$ 10.000 ou mais',
        ]
        salary_lookup = {
            item['salary_range']: item['total'] for item in salary_range_data
        }
        context['salary_range_labels'] = salary_range_order
        context['salary_range_counts'] = [
            salary_lookup.get(label, 0) for label in salary_range_order
        ]
        return context
