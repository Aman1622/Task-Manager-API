from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password

User = get_user_model()

class UserSerializer(serializers.ModelSerializer):
    role = serializers.StringRelatedField()

    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'role')

class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=True, validators=[validate_password])
    role = serializers.CharField(max_length=10, default='user')

    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'password', 'role')

    def create(self, validated_data):
        from .models import role as RoleModel
        role_name = validated_data.pop('role', 'user')
        role_instance, _ = RoleModel.objects.get_or_create(name=role_name)
        
        user = User.objects.create(
            username=validated_data['username'],
            email=validated_data.get('email', ''),
            role=role_instance
        )
        user.set_password(validated_data['password'])
        user.save()
        return user
