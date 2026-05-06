from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView

from employees.models import Department, Employee


class DashboardView(LoginRequiredMixin, TemplateView):
    template_name = 'core/dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(
            {
                'total_employees': Employee.objects.count(),
                'active_employees': Employee.objects.filter(
                    status=Employee.Status.ACTIVE
                ).count(),
                'terminated_employees': Employee.objects.filter(
                    status=Employee.Status.TERMINATED
                ).count(),
                'total_departments': Department.objects.filter(active=True).count(),
            }
        )
        return context
