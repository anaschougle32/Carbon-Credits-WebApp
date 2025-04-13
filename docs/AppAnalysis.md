# 🔍 Carbon Credits Tracking - Application Analysis

## System Architecture Overview

This document provides a detailed analysis of how the Carbon Credits Tracking Web Application works, focusing on the core business logic, data flow, and interaction between different components.

## 🏗️ System Architecture

The application follows a modern Django-based architecture:

1. **Frontend**: Django Templates enhanced with HTMX for dynamic interactions and Tailwind CSS for styling
2. **Backend**: Django application handling request processing, business logic, and template rendering
3. **Database**: PostgreSQL for persistent storage of all application data
4. **External Services**: Google Maps API for geocoding and distance calculations

## 💾 Data Model

### Core Entities

```
┌─────────────┐     ┌──────────────┐     ┌──────────────┐
│  CustomUser │────▶│EmployerProfile│    │EmployeeProfile│
└─────────────┘     └──────────────┘     └──────────────┘
       ▲                   │                    │
       │                   │                    │
       │                   ▼                    ▼
┌─────────────┐      ┌──────────┐         ┌──────┐
│  AdminUser  │      │ Location │◀────────│ Trip │
└─────────────┘      └──────────┘         └──────┘
       │                                      │
       │                                      │
       ▼                                      │
┌─────────────┐                         ┌──────────┐
│ SystemConfig│                         │CarbonCredit│
└─────────────┘                         └──────────┘
                                             │
                                             │
                                             ▼
                                      ┌────────────┐
                                      │Marketplace │
                                      │Transaction │
                                      └────────────┘
```

### Key Models

1. **CustomUser**: 
   - Base user model with role flags (is_employee, is_employer, is_bank_admin, is_super_admin)
   - Authentication fields (email, password)
   - Approval status and registration date

2. **EmployerProfile**:
   - Company information (name, registration number, industry)
   - Approval status and date
   - Related to CustomUser via one-to-one field

3. **EmployeeProfile**:
   - Personal information
   - Home location (coordinates)
   - Employer reference (ForeignKey to EmployerProfile)
   - Approval status

4. **Location**:
   - Geographic coordinates (latitude, longitude)
   - Address details (street, city, etc.)
   - Location type (office, home, other)
   - Associated employer (for office locations)

5. **Trip**:
   - Start and end locations (ForeignKey to Location)
   - Start and end timestamps
   - Transport mode (car, carpool, public transport, bicycle, walking, etc.)
   - Calculated distance and carbon savings
   - Employee reference
   - Proof of trip (optional file upload)
   - Verification status

6. **CarbonCredit**:
   - Credit amount
   - Source (trip ID or system allocation)
   - Owner (employee or employer)
   - Timestamp and expiry
   - Status (active, pending, used, expired)

7. **MarketplaceTransaction**:
   - Seller and buyer (EmployerProfile)
   - Credit amount and price
   - Transaction status
   - Approval reference (BankAdmin)
   - Timestamps for request, approval, and completion

## 🔄 Core Business Processes

### 1. Registration & Approval Flow

```
┌─────────┐     ┌────────────┐     ┌──────────┐
│ Employer │────▶│ Carbon Bank│────▶│ System   │
│ Register │     │ Admin      │     │ Database │
└─────────┘     └────────────┘     └──────────┘
                       │
                       ▼
┌─────────┐     ┌────────────┐     ┌──────────┐
│ Employee │────▶│ Employer   │────▶│ System   │
│ Register │     │ Admin      │     │ Database │
└─────────┘     └────────────┘     └──────────┘
```

1. **Employer Registration**:
   - Employer submits registration form with company details and office locations
   - System creates an EmployerProfile with status "Pending"
   - Carbon Bank Admin receives notification
   - Admin reviews and approves/rejects the employer
   - Upon approval, employer account is activated

2. **Employee Registration**:
   - Employee submits registration with personal details and selects employer
   - System creates EmployeeProfile with status "Pending"
   - Selected employer receives notification
   - Employer approves/rejects employee
   - Upon approval, employee account is activated
   - Employee adds home location to complete setup

### 2. Trip Logging & Credit Calculation

```
┌───────────┐     ┌───────────┐     ┌─────────────┐
│ Start Trip │────▶│ End Trip  │────▶│ System      │
│ (GPS)      │     │ (GPS)     │     │ Verification│
└───────────┘     └───────────┘     └─────────────┘
                                            │
                                            ▼
                                    ┌─────────────┐
                                    │ Distance &  │
                                    │ Mode        │
                                    │ Calculation │
                                    └─────────────┘
                                            │
                                            ▼
                                    ┌─────────────┐
                                    │ Credit      │
                                    │ Allocation  │
                                    └─────────────┘
```

1. **Trip Initiation**:
   - Employee starts trip through web interface
   - System captures current GPS coordinates via browser's Geolocation API
   - Timestamp is recorded as trip start

2. **Trip Completion**:
   - Employee ends trip at destination
   - System captures ending GPS coordinates
   - Employee selects transport mode
   - Optional: Employee uploads proof (ticket, receipt)

3. **Distance Calculation**:
   - System calculates trip distance using Google Maps API
   - If API fails, fallback to Haversine formula
   - System verifies trip is between registered locations (home/office)

4. **Credit Assignment**:
   - System applies transport mode multiplier to distance
   - Credits calculated based on formula: `distance * mode_multiplier * base_rate`
   - Credits added to employee's balance
   - Employer's organizational total updated

5. **Verification (Optional)**:
   - Suspicious trips flagged for review (multiple same-day trips, unrealistic speeds)
   - Admin can verify uploaded proof
   - Verified trips marked as confirmed

### 3. Carbon Credit Trading

```
┌─────────┐     ┌─────────┐     ┌────────────┐
│ Employer │────▶│ Market  │────▶│ Carbon Bank│
│ (Seller) │     │ Listing │     │ Admin      │
└─────────┘     └─────────┘     └────────────┘
                      │                │
                      │                │
                      ▼                ▼
┌─────────┐     ┌─────────┐     ┌────────────┐
│ Employer │────▶│Transaction│◀───│ Approval   │
│ (Buyer)  │     │ Complete │    │ (for large │
└─────────┘     └─────────┘     │ transactions│
                                 └────────────┘
```

1. **Credit Listing**:
   - Employer creates offer to sell credits (amount and price)
   - System lists offer in marketplace

2. **Purchase Process**:
   - Buyer employer views and selects offer
   - System verifies buyer has sufficient funds
   - For large transactions, request sent to Carbon Bank Admin for approval
   - For small transactions, processed automatically

3. **Transaction Completion**:
   - Upon approval, credits transferred from seller to buyer
   - Transaction record created with status "Completed"
   - Both parties notified of successful transaction
   - Market analytics updated

## 🧠 Core Algorithms

### 1. Distance Calculation

```python
def calculate_distance(start_coords, end_coords):
    """
    Calculate distance between two geographical points.
    Primary: Google Maps API
    Fallback: Haversine formula
    """
    try:
        # Try Google Maps Distance Matrix API first
        distance = google_maps_distance_api(start_coords, end_coords)
        return distance
    except APIError:
        # Fallback to Haversine formula
        return haversine_distance(start_coords, end_coords)
        
def haversine_distance(start_coords, end_coords):
    """
    Calculate the great circle distance between two points
    on the earth (specified in decimal degrees)
    """
    lat1, lon1 = start_coords
    lat2, lon2 = end_coords
    
    # Convert decimal degrees to radians
    lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
    
    # Haversine formula
    dlon = lon2 - lon1
    dlat = lat2 - lat1
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    c = 2 * asin(sqrt(a))
    r = 6371  # Radius of earth in kilometers
    
    return c * r
```

### 2. Carbon Credit Calculation

```python
def calculate_carbon_credits(distance_km, transport_mode):
    """
    Calculate carbon credits based on distance and transport mode.
    Base formula: credits = distance * mode_multiplier * base_rate
    """
    # Transport mode multipliers
    mode_multipliers = {
        'car': 0,  # No credits for single-occupancy car
        'carpool': 1.5,
        'public_transport': 2.0,
        'bicycle': 3.0,
        'walking': 3.5,
        'work_from_home': 2.0  # Credits for not commuting at all
    }
    
    # Base rate per kilometer
    base_rate = 0.1  # 0.1 credits per km
    
    # Apply multiplier based on transport mode
    multiplier = mode_multipliers.get(transport_mode, 0)
    
    # Calculate credits
    credits = distance_km * multiplier * base_rate
    
    return round(credits, 2)
```

### 3. Fraud Detection

```python
def check_for_suspicious_activity(employee, trip):
    """
    Flag potentially fraudulent trip activity.
    """
    flags = []
    
    # Check for multiple trips in short timeframe
    recent_trips = Trip.objects.filter(
        employee=employee,
        start_time__gte=timezone.now() - timedelta(hours=3)
    ).exclude(id=trip.id).count()
    
    if recent_trips > 2:
        flags.append("Multiple trips in short timeframe")
    
    # Check for unrealistic speeds
    if trip.duration.total_seconds() > 0:
        speed_kmh = trip.distance_km / (trip.duration.total_seconds() / 3600)
        
        # Speed thresholds based on transport mode
        speed_thresholds = {
            'walking': 7,  # km/h
            'bicycle': 30,
            'public_transport': 100,
            'car': 130,
            'carpool': 130
        }
        
        if speed_kmh > speed_thresholds.get(trip.transport_mode, 150):
            flags.append(f"Unrealistic speed for {trip.transport_mode}")
    
    # Check if trip is between registered locations
    if not trip.is_between_registered_locations():
        flags.append("Trip not between registered locations")
    
    return flags
```

## 🔒 Security Considerations

1. **Authentication**: 
   - Django's built-in authentication system
   - Password strength requirements and account lockout after failed attempts
   - Email verification for account validation

2. **Authorization**:
   - Role-based access control using Django's permission system
   - Object-level permissions (employees can only see their trips)
   - Rate limiting for sensitive operations

3. **Data Protection**:
   - Location data anonymization for reports
   - Encryption for sensitive data in transit and at rest
   - Compliance with privacy regulations (GDPR, etc.)

4. **API Security**:
   - CSRF protection on all forms
   - Input validation on all forms
   - Prevention of common vulnerabilities (XSS, SQL Injection)
   - HTTPS enforcement for all communications

## 📊 Reporting and Analytics

### Employee Dashboard
- Daily/Weekly/Monthly carbon savings
- Trip history with statistics
- Personal achievements and impact visualization
- Comparison with peers (optional/anonymous)

### Employer Dashboard
- Organization-wide carbon savings
- Employee participation rates
- Department-level breakdowns
- Credit trading history and balance
- Environmental impact metrics

### Carbon Bank Admin Dashboard
- System-wide statistics
- Employer approval queue
- Credit trading volume and trends
- Suspicious activity monitoring
- Policy effectiveness analytics

## 📱 Mobile Considerations

The application will be responsive with mobile-first design using Tailwind CSS. Special considerations include:

1. **Simplified Trip Logging**:
   - One-tap trip start/end with mobile-optimized UI
   - Progressive web app capabilities for better mobile experience
   - Offline capability using browser storage

2. **Location Optimization**:
   - Battery-efficient location services
   - Reduced precision for general location awareness
   - Smart polling based on movement detection

3. **Mobile-Specific Features**:
   - Mobile-optimized forms and interactions
   - Camera integration for proof uploads
   - Responsive data visualization 