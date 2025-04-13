from rest_framework import serializers
from .models import CustomUser, EmployerProfile, EmployeeProfile, Location


class UserSerializer(serializers.ModelSerializer):
    """Serializer for the CustomUser model."""
    
    class Meta:
        model = CustomUser
        fields = ['id', 'email', 'username', 'first_name', 'last_name', 
                  'is_employee', 'is_employer', 'is_bank_admin', 'is_super_admin',
                  'approved', 'date_joined']
        read_only_fields = ['id', 'date_joined', 'approved', 
                           'is_employee', 'is_employer', 'is_bank_admin', 'is_super_admin']
        extra_kwargs = {
            'password': {'write_only': True, 'min_length': 8}
        }
    
    def create(self, validated_data):
        """Create and return a new user."""
        user = CustomUser.objects.create_user(**validated_data)
        return user


class LocationSerializer(serializers.ModelSerializer):
    """Serializer for the Location model."""
    
    class Meta:
        model = Location
        fields = ['id', 'created_by', 'latitude', 'longitude', 'address',
                  'location_type', 'employer', 'is_primary', 'created_at']
        read_only_fields = ['id', 'created_by', 'created_at']


class EmployerProfileSerializer(serializers.ModelSerializer):
    """Serializer for the EmployerProfile model."""
    
    user = UserSerializer(read_only=True)
    office_locations = LocationSerializer(many=True, read_only=True)
    
    class Meta:
        model = EmployerProfile
        fields = ['id', 'user', 'company_name', 'registration_number', 
                  'industry', 'approved', 'created_at', 'office_locations']
        read_only_fields = ['id', 'user', 'approved', 'created_at']


class EmployeeProfileSerializer(serializers.ModelSerializer):
    """Serializer for the EmployeeProfile model."""
    
    user = UserSerializer(read_only=True)
    employer = EmployerProfileSerializer(read_only=True)
    
    class Meta:
        model = EmployeeProfile
        fields = ['id', 'user', 'employer', 'approved', 'created_at']
        read_only_fields = ['id', 'user', 'approved', 'created_at']


class EmployerRegistrationSerializer(serializers.Serializer):
    """Serializer for employer registration."""
    
    # User fields
    email = serializers.EmailField()
    username = serializers.CharField(max_length=150)
    password = serializers.CharField(min_length=8, write_only=True)
    first_name = serializers.CharField(max_length=150)
    last_name = serializers.CharField(max_length=150)
    
    # Employer profile fields
    company_name = serializers.CharField(max_length=100)
    registration_number = serializers.CharField(max_length=50)
    industry = serializers.CharField(max_length=100)
    
    # Office location fields
    office_latitude = serializers.DecimalField(max_digits=10, decimal_places=7)
    office_longitude = serializers.DecimalField(max_digits=10, decimal_places=7)
    office_address = serializers.CharField(max_length=255)


class EmployeeRegistrationSerializer(serializers.Serializer):
    """Serializer for employee registration."""
    
    # User fields
    email = serializers.EmailField()
    username = serializers.CharField(max_length=150)
    password = serializers.CharField(min_length=8, write_only=True)
    first_name = serializers.CharField(max_length=150)
    last_name = serializers.CharField(max_length=150)
    
    # Employee profile fields
    employer_id = serializers.IntegerField()
    
    # Home location fields
    home_latitude = serializers.DecimalField(max_digits=10, decimal_places=7, required=False)
    home_longitude = serializers.DecimalField(max_digits=10, decimal_places=7, required=False)
    home_address = serializers.CharField(max_length=255, required=False) 