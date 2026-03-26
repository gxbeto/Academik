from django.contrib.auth.views import LoginView


class AcademikLoginView(LoginView):
    template_name = "registration/login.html"
    redirect_authenticated_user = True
