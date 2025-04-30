# Carbon Credits Platform

A comprehensive web application for tracking, managing, and trading carbon credits based on employee commuting habits. The platform helps organizations reduce their carbon footprint while incentivizing sustainable transportation choices.

## Features

- **User Roles**: Admin, Bank, Employer, and Employee access levels
- **Trip Logging**: Employees can log sustainable commute trips
- **Carbon Credits**: Automatic calculation of carbon credits based on trip distance and transport mode
- **Marketplace**: Trading platform for carbon credits between organizations
- **Dashboards**: Role-specific dashboards with analytics and management tools
- **Location Management**: Registration and tracking of office and home locations

## Technology Stack

- **Backend**: Django 5.2 with Django REST Framework
- **Frontend**: HTML/CSS/JavaScript with Tailwind CSS
- **Database**: SQLite (default), can be configured for PostgreSQL
- **Authentication**: Token-based authentication with JWT
- **Maps Integration**: Google Maps API for location services

## Setup Instructions

### Prerequisites

- Python 3.10+
- pip (Python package manager)
- Git

### Installation Steps

1. **Clone the repository**

   ```bash
   git clone https://github.com/yourusername/carbon-credits.git
   cd carbon-credits
   ```

2. **Create and activate a virtual environment**

   ```bash
   # Windows
   python -m venv venv
   venv\Scripts\activate

   # macOS/Linux
   python -m venv venv
   source venv/bin/activate
   ```

3. **Install dependencies**

   ```bash
   pip install -r carbon_backend/requirements.txt
   ```

4. **Environment Setup**

   Create a `.env` file in the `carbon_backend` directory with the following variables:

   ```
   SECRET_KEY=your_secret_key_here
   DEBUG=True
   ALLOWED_HOSTS=localhost,127.0.0.1
   GOOGLE_MAPS_API_KEY=your_google_maps_api_key
   ```

5. **Database Setup**

   ```bash
   cd carbon_backend
   python manage.py migrate
   ```

6. **Create Test Users**

   Create test users with all four roles (Admin, Bank, Employer, Employee) for testing:

   ```bash
   python manage.py create_test_users
   ```

   This will create the following users:
   - **Super Admin**: superadmin@carboncredits.com / SuperAdmin2023!
   - **Bank Admin**: admin@carbonbank.com / BankAdmin2023!
   - **Employer**: jgarcia@greentechsolutions.com / EmployerTest2023!
   - **Employee**: sarah.miller@greentechsolutions.com / EmployeeTest2023!

7. **Collect Static Files**

   ```bash
   python manage.py collectstatic
   ```

## Running the Application

1. **Start the development server**

   ```bash
   python manage.py runserver
   ```

2. **Access the application**

   Open your browser and navigate to:
   - http://127.0.0.1:8000/

3. **Login with test users**

   Use the credentials created in step 6 to log in as different user types.

## Project Structure

```
Carbon-Credits/
├── carbon_backend/       # Main Django project
│   ├── carbon_backend/   # Core project settings
│   ├── core/             # Core functionality & views
│   ├── users/            # User management
│   ├── trips/            # Trip logging & carbon calculation
│   ├── marketplace/      # Carbon credits trading platform
│   └── ...
├── templates/            # HTML templates
│   ├── admin/            # Admin interface templates
│   ├── bank/             # Bank interface templates
│   ├── employee/         # Employee interface templates
│   ├── employer/         # Employer interface templates
│   └── ...
├── static/               # Static files (CSS, JS, images)
└── ...
```

## User Workflows

1. **Employee Workflow**
   - Register and link to employer
   - Set up home location
   - Log daily commute trips
   - Earn carbon credits
   - View personal statistics

2. **Employer Workflow**
   - Register company and office locations
   - Approve employee accounts
   - Verify and approve employee trips
   - Trade carbon credits
   - View company statistics

3. **Bank Workflow**
   - Manage carbon credit marketplace
   - Approve trading transactions
   - Generate reports
   - Oversee system activity

4. **Admin Workflow**
   - Manage all users and roles
   - Configure system settings
   - Access all features
   - View global statistics

## Troubleshooting

- **CSRF Verification Failed**: Make sure cookies are enabled in your browser
- **Message Framework Issues**: Verify MessageMiddleware is in the MIDDLEWARE setting
- **Login Issues**: Ensure users are marked as approved and active

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Contributors

- Your Name
- Other Contributors 