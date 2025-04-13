# 📁 Project Structure

This document outlines the complete structure of the Carbon Credits Tracking application, which uses Django Templates with HTMX and Tailwind CSS.

## Project Structure (Django)

```
carbon_backend/
│
├── carbon_backend/                    # Main Django project
│   ├── __init__.py
│   ├── asgi.py
│   ├── settings.py                    # Project settings
│   ├── urls.py                        # Main URL routing
│   └── wsgi.py
│
├── users/                             # User management app
│   ├── __init__.py
│   ├── admin.py                       # Admin panel config
│   ├── apps.py
│   ├── forms.py                       # Form classes
│   ├── migrations/                    # Database migrations
│   ├── models.py                      # User, Employer, Employee models
│   ├── tests.py                       # Unit tests
│   ├── urls.py                        # App-specific URLs
│   ├── views.py                       # View functions
│   └── templates/                     # HTML templates
│       └── users/                     # User-specific templates
│           ├── login.html             # Login page
│           ├── register.html          # Registration page
│           ├── profile.html           # User profile
│           └── ...
│
├── trips/                             # Trip logging app
│   ├── __init__.py
│   ├── admin.py
│   ├── apps.py
│   ├── forms.py                       # Trip forms
│   ├── migrations/
│   ├── models.py                      # Trip, Location models
│   ├── services/                      # Business logic
│   │   ├── __init__.py
│   │   ├── distance_calculator.py     # Distance calculation  
│   │   ├── credit_calculator.py       # Carbon credit calculation
│   │   └── fraud_detector.py          # Suspicious trip detection
│   ├── tests.py
│   ├── urls.py
│   ├── views.py                       # Trip view functions
│   └── templates/                     # HTML templates
│       └── trips/                     # Trip-specific templates
│           ├── trip_list.html         # List trips
│           ├── trip_detail.html       # Trip details
│           ├── trip_log.html          # Log new trip
│           └── ...
│
├── marketplace/                       # Credit trading app
│   ├── __init__.py
│   ├── admin.py
│   ├── apps.py
│   ├── forms.py                       # Marketplace forms
│   ├── migrations/
│   ├── models.py                      # Transaction, Offer models
│   ├── services/
│   │   ├── __init__.py
│   │   └── transaction_service.py     # Trading logic
│   ├── tests.py
│   ├── urls.py
│   ├── views.py                       # Marketplace views
│   └── templates/                     # HTML templates
│       └── marketplace/               # Marketplace templates
│           ├── offer_list.html        # List offers
│           ├── create_offer.html      # Create new offer
│           ├── transaction_history.html # Transaction history
│           └── ...
│
├── core/                              # Shared utilities
│   ├── __init__.py
│   ├── admin.py
│   ├── apps.py
│   ├── forms.py                       # Shared forms
│   ├── migrations/
│   ├── models.py                      # Shared models
│   ├── context_processors.py          # Custom context processors
│   ├── templatetags/                  # Custom template tags
│   │   ├── __init__.py
│   │   └── core_tags.py               # Core template tags and filters
│   ├── utils/
│   │   ├── __init__.py
│   │   ├── constants.py               # App-wide constants
│   │   └── geocoding.py               # Map API utilities
│   ├── tests.py
│   ├── views.py                       # Core view functions
│   └── templates/                     # Shared templates
│       ├── core/                      # Core-specific templates
│       │   ├── dashboard.html         # Base dashboard
│       │   └── ...
│       ├── components/                # Reusable components
│       │   ├── navbar.html            # Navigation bar
│       │   ├── sidebar.html           # Sidebar
│       │   ├── modal.html             # Modal dialog
│       │   ├── alert.html             # Alert messages
│       │   └── ...
│       └── layouts/                   # Page layouts
│           ├── base.html              # Base template
│           ├── dashboard_layout.html  # Dashboard layout
│           └── ...
│
├── templates/                         # Project-wide templates
│   ├── admin/                         # Admin templates
│   │   ├── dashboard.html             # Admin dashboard
│   │   └── ...
│   ├── bank/                          # Bank admin templates
│   │   ├── dashboard.html             # Bank admin dashboard
│   │   └── ...
│   ├── employer/                      # Employer templates
│   │   ├── dashboard.html             # Employer dashboard
│   │   └── ...
│   ├── employee/                      # Employee templates
│   │   ├── dashboard.html             # Employee dashboard
│   │   └── ...
│   ├── auth/                          # Authentication templates
│   │   ├── login.html                 # Login page
│   │   ├── register.html              # Register page
│   │   └── ...
│   ├── 403.html                       # Permission denied
│   ├── 404.html                       # Page not found
│   └── 500.html                       # Server error
│
├── static/                            # Static files
│   ├── js/                            # JavaScript files
│   │   ├── htmx.min.js                # HTMX library
│   │   ├── maps.js                    # Google Maps integration
│   │   ├── charts.js                  # Chart.js integration
│   │   └── app.js                     # Custom JavaScript
│   ├── css/                           # CSS files
│   │   ├── tailwind.css               # Compiled Tailwind CSS
│   │   └── custom.css                 # Custom styles
│   └── images/                        # Image assets
│       ├── logo.png                   # App logo
│       └── ...
│
├── media/                             # User uploaded files
│   ├── proof_images/                  # Trip proof images
│   └── profile_pics/                  # User profile pictures
│
├── requirements.txt                   # Python dependencies
├── manage.py                          # Django management script
└── .env                               # Environment variables (gitignored)
```

## Database Schema

```
┌─────────────────┐       ┌────────────────┐       ┌─────────────────┐
│   CustomUser    │       │ EmployerProfile│       │ EmployeeProfile │
├─────────────────┤       ├────────────────┤       ├─────────────────┤
│ id              │───┐   │ id             │───┐   │ id              │
│ email           │   │   │ user_id        │◄──┘   │ user_id         │◄──┐
│ password        │   └──▶│ company_name   │       │ employer_id     │───┘
│ first_name      │       │ registration_no│       │ home_location   │
│ last_name       │       │ industry       │       │ approved        │
│ is_employee     │       │ approved       │       │ created_at      │
│ is_employer     │       │ created_at     │       └─────────────────┘
│ is_bank_admin   │       └────────────────┘               │
│ is_super_admin  │              │                         │
│ date_joined     │              │                         │
└─────────────────┘              ▼                         │
        │            ┌────────────────┐                    │
        │            │ Location       │                    │
        │            ├────────────────┤                    │
        │            │ id             │                    │
        └───────────▶│ created_by     │                    │
                     │ latitude       │                    │
                     │ longitude      │                    │
                     │ address        │                    │
                     │ location_type  │                    │
                     │ employer_id    │                    │
                     └────────────────┘                    │
                             ▲                             │
                             │                             │
                      ┌──────┴─────────┐                   │
                      │ Trip           │◀──────────────────┘
                      ├────────────────┤
                      │ id             │
                      │ employee_id    │
                      │ start_location │
                      │ end_location   │
                      │ start_time     │
                      │ end_time       │
                      │ transport_mode │
                      │ distance       │
                      │ carbon_savings │
                      │ credits_earned │
                      │ proof_image    │
                      │ verified       │
                      └────────────────┘
                              │
                              │
                              ▼
                     ┌─────────────────┐      ┌─────────────────┐
                     │ CarbonCredit    │      │ MarketOffer     │
                     ├─────────────────┤      ├─────────────────┤
                     │ id              │      │ id              │
                     │ amount          │      │ seller_id       │
                     │ source_trip     │      │ credit_amount   │
                     │ owner_type      │      │ price_per_credit│
                     │ owner_id        │      │ total_price     │
                     │ timestamp       │      │ status          │
                     │ status          │      │ created_at      │
                     └─────────────────┘      └─────────────────┘
                              │                      │
                              │                      │
                              ▼                      ▼
                     ┌─────────────────────────────────────────┐
                     │ MarketplaceTransaction                  │
                     ├─────────────────────────────────────────┤
                     │ id                                      │
                     │ offer_id                                │
                     │ seller_id                               │
                     │ buyer_id                                │
                     │ credit_amount                           │
                     │ total_price                             │
                     │ status                                  │
                     │ admin_approval_required                 │
                     │ approved_by                             │
                     │ created_at                              │
                     │ completed_at                            │
                     └─────────────────────────────────────────┘
```

## URL Patterns

### Authentication URLs
- `/login/` - User login
- `/logout/` - User logout
- `/register/` - New user registration
- `/register/employer/` - Employer registration
- `/register/employee/` - Employee registration
- `/password-reset/` - Password reset request
- `/password-reset/done/` - Password reset request confirmation
- `/reset/<uidb64>/<token>/` - Password reset form
- `/reset/done/` - Password reset complete

### Dashboard URLs
- `/` - Home page / redirects to appropriate dashboard
- `/dashboard/` - User dashboard (redirects based on role)
- `/admin/dashboard/` - Super admin dashboard
- `/bank/dashboard/` - Bank admin dashboard
- `/employer/dashboard/` - Employer dashboard
- `/employee/dashboard/` - Employee dashboard

### User Management URLs
- `/users/profile/` - View/edit user profile
- `/users/employees/` - List employees (employer only)
- `/users/employees/<id>/` - View employee details
- `/users/employees/<id>/approve/` - Approve employee
- `/users/employers/` - List employers (admin only)
- `/users/employers/<id>/` - View employer details
- `/users/employers/<id>/approve/` - Approve employer

### Trip Management URLs
- `/trips/` - List user's trips
- `/trips/<id>/` - View trip details
- `/trips/start/` - Start new trip
- `/trips/<id>/end/` - End trip
- `/trips/<id>/upload-proof/` - Upload trip proof
- `/trips/<id>/verify/` - Verify trip (admin only)
- `/trips/stats/` - View trip statistics

### Carbon Credit URLs
- `/credits/` - View user's credit balance
- `/credits/history/` - View credit history
- `/credits/stats/` - View credit statistics
- `/employer/credits/stats/` - View organization stats (employer only)

### Marketplace URLs
- `/marketplace/offers/` - List credit offers
- `/marketplace/offers/create/` - Create new offer (employer only)
- `/marketplace/offers/<id>/` - View offer details
- `/marketplace/buy/<offer_id>/` - Buy credits
- `/marketplace/transactions/` - View transaction history
- `/marketplace/transactions/<id>/` - View transaction details
- `/marketplace/transactions/<id>/approve/` - Approve transaction (admin only)

### Admin URLs
- `/admin/users/` - Manage users (admin only)
- `/admin/config/` - System configuration (admin only)
- `/admin/reports/` - Generate reports (admin only)
- `/admin/employers/pending/` - View pending employer registrations
- `/admin/transactions/pending/` - View pending transactions

### HTMX Partial URLs
These endpoints return HTML fragments for HTMX integration:

- `/htmx/trips/recent/` - Recent trips list
- `/htmx/users/search/` - User search results
- `/htmx/credits/balance/` - Current credit balance
- `/htmx/notifications/` - User notifications
- `/htmx/dashboard/stats/` - Dashboard statistics
- `/htmx/marketplace/offers/latest/` - Latest marketplace offers
- `/htmx/transactions/pending/` - Pending transaction approvals 