from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.auth import views as auth_views
from django.contrib.auth import logout
from django.views.generic import TemplateView
from django.shortcuts import redirect
from django.http import HttpResponseRedirect
from users.models import EmployerProfile
from django.contrib import messages

# Landing page view
class LandingPageView(TemplateView):
    template_name = 'landing.html'
    
    def get(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect('dashboard')
        return super().get(request, *args, **kwargs)

# Registration view with employers list
class RegisterView(TemplateView):
    template_name = 'auth/register.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Get all approved employers
        context['employers'] = EmployerProfile.objects.filter(approved=True)
        return context

# Dashboard redirect function - fixed to handle messages properly
def dashboard_redirect(request):
    if not request.user.is_authenticated:
        messages.info(request, "Please log in to access your dashboard.")
        return redirect('login')
        
    try:
        if request.user.is_super_admin:
            return redirect('admin_dashboard')
        elif request.user.is_bank_admin:
            return redirect('bank:bank_dashboard')
        elif request.user.is_employer:
            return redirect('employer:employer_dashboard')
        elif request.user.is_employee:
            return redirect('employee_dashboard')
        else:
            # Fallback to employee dashboard if no specific role is set
            messages.warning(request, "No specific role detected, redirecting to employee dashboard.")
            return redirect('employee_dashboard')
    except Exception as e:
        messages.error(request, f"Error accessing dashboard: {str(e)}")
        return redirect('login')

# Profile redirect function
def profile_redirect(request):
    if not request.user.is_authenticated:
        messages.info(request, "Please log in to access your profile.")
        return redirect('login')
        
    try:
        if request.user.is_super_admin:
            return redirect('admin_profile')
        elif request.user.is_bank_admin:
            return redirect('bank:profile')
        elif request.user.is_employer:
            return redirect('employer:profile')
        elif request.user.is_employee:
            return redirect('employee_profile')
        else:
            # Fallback to login if no specific role is set
            messages.warning(request, "No specific role detected.")
            return redirect('login')
    except Exception as e:
        messages.error(request, f"Error accessing profile: {str(e)}")
        return redirect('login')

# Custom logout view function
def logout_view(request):
    logout(request)
    messages.success(request, "You have been successfully logged out.")
    return HttpResponseRedirect('/')

# Main URL patterns
urlpatterns = [
    # Admin site
    path('admin/', admin.site.urls),
    
    # Auth routes
    path('login/', auth_views.LoginView.as_view(template_name='auth/login.html'), name='login'),
    path('logout/', logout_view, name='logout'),
    path('register/', RegisterView.as_view(), name='register'),
    path('profile/', profile_redirect, name='profile'),
    path('password_reset/', auth_views.PasswordResetView.as_view(template_name='auth/password_reset.html'), name='password_reset'),
    path('password_reset/done/', auth_views.PasswordResetDoneView.as_view(template_name='auth/password_reset_done.html'), name='password_reset_done'),
    path('reset/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(template_name='auth/password_reset_confirm.html'), name='password_reset_confirm'),
    path('reset/done/', auth_views.PasswordResetCompleteView.as_view(template_name='auth/password_reset_complete.html'), name='password_reset_complete'),
    path('registration/pending-approval/', TemplateView.as_view(template_name='registration/pending_approval.html'), name='pending_approval'),
    
    # Main routes
    path('', LandingPageView.as_view(), name='home'),
    path('dashboard/', dashboard_redirect, name='dashboard'),
    
    # API routes
    path('api/users/', include('users.urls')),
    path('api/trips/', include('trips.urls')),
    path('api/marketplace/', include('marketplace.urls')),
    
    # Include app-specific template URLs
    path('systemadmin/', include('core.admin_urls')),  # Custom admin views
    path('bank/', include('core.bank_urls')),
    path('employer/', include('core.employer_urls')),
    path('employee/', include('core.employee_urls')),
]

# Serve static and media files in development
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT) 