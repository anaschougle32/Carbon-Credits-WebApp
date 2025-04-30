from django.contrib import admin
from django.urls import path, include
from django.views.generic import RedirectView
from django.contrib.auth import views as auth_views
from django.conf import settings
from django.conf.urls.static import static
from users.views import RegisterView

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # Auth URLs
    path('login/', auth_views.LoginView.as_view(template_name='auth/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('register/', RegisterView.as_view(template_name='auth/register.html'), name='register'),
    
    # Users URLs
    path('api/users/', include('users.urls')),
    
    # Admin section URLs
    path('admin-dashboard/', include('core.admin_urls')),
    
    # Bank section URLs
    path('bank/', include('core.bank_urls')),
    
    # Employer section URLs
    path('employer/', include('core.employer_urls')),
    
    # Employee section URLs
    path('employee/', include('core.employee_urls')),
    
    # Home page redirect
    path('', RedirectView.as_view(pattern_name='login', permanent=False), name='home'),
]

# Add static and media URLs in development
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT) 