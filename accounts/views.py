from django.contrib.auth import logout
from django.contrib.auth.views import LoginView
from django.shortcuts import redirect


class UserLoginView(LoginView):
    template_name = 'accounts/login.html'
    redirect_authenticated_user = True


def user_logout_view(request):
    logout(request)
    return redirect('accounts:login')
