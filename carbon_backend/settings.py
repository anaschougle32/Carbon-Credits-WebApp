INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django_htmx',
    'rest_framework',
    'core.apps.CoreConfig',
    'users',
    'trips',
    'marketplace',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'users.middleware.ApprovalMiddleware',
    'django_htmx.middleware.HtmxMiddleware',
]

# CSRF settings
CSRF_USE_SESSIONS = True
CSRF_COOKIE_SECURE = False  # Set to True in production with HTTPS
CSRF_COOKIE_HTTPONLY = True

# Session settings
SESSION_COOKIE_SECURE = False  # Set to True in production with HTTPS
SESSION_COOKIE_AGE = 3600  # 1 hour in seconds
SESSION_EXPIRE_AT_BROWSER_CLOSE = True

# Message settings
MESSAGE_STORAGE = 'django.contrib.messages.storage.session.SessionStorage' 