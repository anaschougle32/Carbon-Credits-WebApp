# 📦 Carbon Credits Tracking - Development Plan

## 🚀 Project Overview

This web application tracks and manages carbon credits based on employees' commute behavior. The system involves four user roles:
- **Super Admin**: Full control over the platform
- **Carbon Bank Admin**: Approves employers and manages trading
- **Employer**: Manages organization and employees
- **Employee**: Logs trips and earns carbon credits

### Tech Stack:
- **Frontend**: Django Templates with HTMX and Tailwind CSS
- **Backend**: Django + Django Templates
- **Database**: PostgreSQL
- **Maps & Geolocation**: Google Maps API
- **Authentication**: Django's built-in authentication system

---

## 🛠️ Step-by-Step Development Workflow

### 🧱 1. Project Initialization

#### Backend and Frontend (Django)

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install Django and dependencies
pip install django django-htmx django-compressor django-tailwind psycopg2-binary

# Start Django project
django-admin startproject carbon_backend
cd carbon_backend

# Create core apps
python manage.py startapp users
python manage.py startapp trips
python manage.py startapp marketplace
python manage.py startapp core

# Set up Tailwind CSS
python manage.py tailwind init
python manage.py tailwind install
```

### 🧩 2. Directory Structure

#### Project Structure (Django with Templates)
```
carbon_backend/
│
├── users/                    # Auth, user roles, employer/employee models
│   ├── models.py             # User models
│   ├── views.py              # View functions/classes
│   ├── forms.py              # Form definitions
│   ├── urls.py               # URL patterns
│   └── templates/            # HTML templates
│       └── users/            # User-specific templates
│
├── trips/                    # Trip logs, GPS tracking, carbon points
│   ├── models.py
│   ├── views.py
│   ├── forms.py
│   ├── urls.py
│   └── templates/
│       └── trips/
│
├── marketplace/              # Trading system
│   ├── models.py
│   ├── views.py
│   ├── forms.py
│   ├── urls.py
│   └── templates/
│       └── marketplace/
│
├── core/                     # Shared utilities and models
│   ├── models.py
│   ├── views.py
│   ├── templatetags/         # Custom template tags
│   ├── static/               # Static files (CSS, JS)
│   │   ├── js/               # JavaScript files including HTMX extensions
│   │   ├── css/              # Compiled Tailwind CSS
│   │   └── images/           # Image assets
│   └── templates/            # Base templates and common components
│       ├── base.html         # Base template with common structure
│       ├── components/       # Reusable template components
│       └── layouts/          # Layout templates for different user roles
│
├── carbon_backend/           # Main settings
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
│
├── templates/                # Project-wide templates
│   ├── auth/                 # Authentication templates
│   ├── admin/                # Admin dashboard templates
│   ├── bank/                 # Bank admin templates
│   ├── employer/             # Employer templates
│   └── employee/             # Employee templates
│
├── static/                   # Collected static files
├── media/                    # User-uploaded files
└── manage.py
```

### 🔐 3. Authentication & Authorization

#### Implementation:
- Implement `CustomUser` model with role flags
- Use Django's built-in authentication system
- Role-based access control with custom middleware and decorators
- Email verification for new registrations

#### Template-based Auth:
- Custom login/registration templates
- Role-specific redirects after login
- Session-based authentication
- Password reset workflows with Django's auth views

### 🌍 4. Core Features Implementation

#### 📌 User Management System

**Implementation:**
- `CustomUser` model with roles
- `EmployerProfile` & `EmployeeProfile` models
- Approval workflows and status tracking
- Admin creation by Super Admin

**Templates & HTMX:**
- Role-specific registration forms
- Multi-step registration with HTMX for partial page updates
- Status indicators for approval process
- User profile management screens with inline editing

#### 📌 Location Management

**Implementation:**
- Models for storing office locations (employers)
- Home location storage for employees
- Geocoding and reverse geocoding utilities
- Location validation logic

**Templates & HTMX:**
- Google Maps integration for location picking
- Address autocomplete and verification
- Office selection for employees with dynamic updates
- Location management screens for employers with HTMX for smooth interactions

#### 📌 Trip Logging System

**Implementation:**
- Trip model with transport mode, timestamps, locations
- Distance calculation using Haversine formula or Maps API
- Points calculation based on transport mode multipliers
- Trip validation and fraud detection logic

**Templates & HTMX:**
- "Log Trip" interface with transport mode selection
- GPS detection using Geolocation API
- Optional proof upload functionality with preview
- Trip history and details view with pagination

#### 📌 Carbon Credit System

**Implementation:**
- Credit calculation engine based on trip types and distances
- Monthly credit allocation and tracking
- Organization-level aggregation
- Historical data for reporting

**Templates & HTMX:**
- Dashboard with credit statistics and visualizations
- Monthly and all-time summaries with Chart.js
- Leaderboards and achievements with real-time updates
- Export functionality for reports

#### 📌 Marketplace Module

**Implementation:**
- Credit trading models (offers, transactions)
- Approval workflow for Carbon Bank Admin
- Transaction history and audit logs
- Rate limiting and fraud prevention

**Templates & HTMX:**
- Buy/sell interface for credits with real-time validation
- Transaction history and status tracking with HTMX updates
- Approval notifications with Django Messages
- Market analytics for admins with interactive charts

### 🔍 5. Solutions to Core Problems

| Problem | Solution |
|---------|----------|
| **Tracking Home-Work Travel** | Implement Geolocation API to record GPS coordinates at trip start/end. Match against stored locations. |
| **Office Location** | Employers define office locations during registration. Employees select from their employer's offices. |
| **Transport Mode Detection** | Manual selection with descriptive options and proof upload capability. |
| **Distance Calculation** | Primary: Google Maps Distance Matrix API. Fallback: Haversine formula between coordinates. |
| **Credit Calculation** | Algorithm based on: <br>- Distance saved from not using car <br>- Transport mode multiplier <br>- Monthly baseline comparison |
| **Trip Validation** | Implement flags for suspicious patterns (multiple same-day trips, unrealistic distances). Admin review for flagged trips. |
| **Secure Trading** | Two-step verification for trades. Carbon Bank Admin approval required for large transactions. |

### 🧪 6. Testing Strategy

**Backend & Templates:**
- Unit tests for models and utility functions
- Integration tests for view functions
- Template tests for proper rendering
- Performance testing for credit calculations and HTMX interactions

**Frontend (HTMX & JavaScript):**
- JavaScript unit tests for complex client-side functions
- Integration tests for HTMX interactions
- UI tests with Selenium for critical flows (registration, trip logging)
- Responsive design testing across devices

### 🔄 7. Frontend-Backend Integration

- Use Django's templating system for rendering HTML
- Enhance templates with HTMX for dynamic interactions without full page reloads
- Implement partial template updates for improved performance
- Use Django Messages for notifications
- Leverage HTML's native form validation enhanced with JavaScript

### 📱 8. Responsive Design

- Mobile-first approach using Tailwind CSS
- Role-specific layouts optimized for device size
- Simplified trip logging interface for mobile
- Progressive enhancement for map features
- Responsive components using Tailwind's breakpoint system

### 🚀 9. Deployment Plan

**Development:**
- Local development with Django's development server
- Git workflow with feature branches and PR reviews

**Staging:**
- Deploy to Render/Railway
- CI/CD with GitHub Actions

**Production:**
- Deploy to scalable cloud service
- Set up PostgreSQL with proper backups
- CDN for static assets
- Monitoring and error tracking integration

### ⏳ 10. Implementation Timeline (4-Week Plan)

| Week | Focus | Key Deliverables |
|------|-------|------------------|
| **Week 1** | Project Setup & Auth | - Project initialization<br>- User models and authentication<br>- Registration flows<br>- Basic template structure |
| **Week 2** | Core Features | - Location management<br>- Trip logging functionality<br>- Credit calculation engine<br>- Basic reporting |
| **Week 3** | Marketplace & Admin | - Credit trading system<br>- Admin approval workflows<br>- Data visualization<br>- Advanced reporting |
| **Week 4** | Testing & Polish | - Comprehensive testing<br>- UI/UX improvements<br>- Performance optimization<br>- Documentation |

## 📝 Development Guidelines

### Coding Standards
- Follow PEP 8 for Python code
- Follow BEM methodology for CSS classes
- Use JavaScript modules for organization
- Document all view functions and models

### Security Practices
- Regular dependency updates
- Input validation on both server and client side
- CSRF protection for all forms
- Proper permission checking on all views

### Collaboration
- Daily standups
- Feature-based branch strategy
- Code reviews before merging
- Comprehensive documentation

---

## 🔍 Understanding the Application Flow

### Registration Process
1. Employers register their organization and office locations
2. Carbon Bank Admin approves employer registrations
3. Employees register and select their employer
4. Employers approve their employees
5. Employees set their home location

### Daily Usage (Employee)
1. Employee logs into the system
2. Starts a trip using "Start Trip" button (captures starting GPS)
3. Selects transport mode (carpool, public transit, bike, etc.)
4. Ends trip at destination (captures ending GPS)
5. System calculates distance and awards carbon credits
6. Dashboard updates with new credits and statistics

### Employer Features
1. Approve/manage employees
2. View organization-wide carbon savings
3. Trade carbon credits in marketplace
4. Generate reports and analytics

### Carbon Bank Admin Features
1. Approve employer registrations
2. Monitor credit trading activity
3. Approve/reject large trades
4. Set system-wide policies and multipliers

### Super Admin Features
1. System configuration and monitoring
2. Create/manage Carbon Bank Admins
3. Access to all data and reports
4. Emergency interventions 