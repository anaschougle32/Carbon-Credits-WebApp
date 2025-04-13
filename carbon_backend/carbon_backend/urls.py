"""
URL configuration for carbon_backend project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.auth import views as auth_views
from django.contrib.auth import logout
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from django.views.generic import TemplateView
from django.shortcuts import redirect, HttpResponseRedirect

# API URLs
api_urlpatterns = [
    path('token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('users/', include('users.urls')),
    path('trips/', include('trips.urls')),
    path('marketplace/', include('marketplace.urls')),
]

# Landing page view
class LandingPageView(TemplateView):
    template_name = 'landing.html'
    
    def get(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect('dashboard')
        return super().get(request, *args, **kwargs)

# Dashboard redirect function
def dashboard_redirect(request):
    if not request.user.is_authenticated:
        return redirect('login')
        
    if request.user.is_super_admin:
        return redirect('admin_dashboard')
    elif request.user.is_bank_admin:
        return redirect('bank_dashboard')
    elif request.user.is_employer:
        return redirect('employer_dashboard')
    elif request.user.is_employee:
        return redirect('employee_dashboard')
    else:
        # Fallback to employee dashboard if no specific role is set
        return redirect('employee_dashboard')

# Custom logout view function
def logout_view(request):
    logout(request)
    return HttpResponseRedirect('/')

# Template-based URLs
urlpatterns = [
    # Admin site
    path('admin/', admin.site.urls),
    
    # API routes
    path('api/', include(api_urlpatterns)),
    
    # Auth routes
    path('login/', auth_views.LoginView.as_view(template_name='auth/login.html'), name='login'),
    path('logout/', logout_view, name='logout'),
    path('register/', TemplateView.as_view(template_name='auth/register.html'), name='register'),
    path('profile/', TemplateView.as_view(template_name='auth/profile.html'), name='profile'),
    path('password_reset/', auth_views.PasswordResetView.as_view(template_name='auth/password_reset.html'), name='password_reset'),
    path('password_reset/done/', auth_views.PasswordResetDoneView.as_view(template_name='auth/password_reset_done.html'), name='password_reset_done'),
    path('reset/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(template_name='auth/password_reset_confirm.html'), name='password_reset_confirm'),
    path('reset/done/', auth_views.PasswordResetCompleteView.as_view(template_name='auth/password_reset_complete.html'), name='password_reset_complete'),
    
    # Main routes
    path('', LandingPageView.as_view(), name='home'),
    path('dashboard/', dashboard_redirect, name='dashboard'),
    
    # Include app-specific template URLs
    path('admin/dashboard/', include('core.admin_urls')),  # Custom admin views
    path('bank/', include('core.bank_urls')),
    path('employer/', include('core.employer_urls')),
    path('employee/', include('core.employee_urls')),
]

# Serve static and media files in development
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
