from rest_framework import generics, permissions
from rest_framework.response import Response
from rest_framework_simplejwt.views import TokenObtainPairView
from django.contrib.auth import get_user_model
from .serializers import RegisterSerializer, UserSerializer

User = get_user_model()

class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    permission_classes = (permissions.AllowAny,)
    serializer_class = RegisterSerializer

class ProfileView(generics.RetrieveUpdateAPIView):
    permission_classes = (permissions.IsAuthenticated,)
    serializer_class = UserSerializer

    def get_object(self):
        return self.request.user

class AuthRootView(generics.GenericAPIView):
    permission_classes = (permissions.AllowAny,)

    def get(self, request, *args, **kwargs):
        from rest_framework.reverse import reverse
        return Response({
            'register': reverse('register', request=request, format=kwargs.get('format')),
            'login': reverse('token_obtain_pair', request=request, format=kwargs.get('format')),
            'refresh': reverse('token_refresh', request=request, format=kwargs.get('format')),
            'profile': reverse('profile', request=request, format=kwargs.get('format')),
            'logout': reverse('logout', request=request, format=kwargs.get('format')),
        })

from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.exceptions import TokenError

class LogoutView(generics.GenericAPIView):
    permission_classes = (permissions.IsAuthenticated,)

    def post(self, request):
        try:
            refresh_token = request.data["refresh"]
            token = RefreshToken(refresh_token)
            token.blacklist()
            return Response({"detail": "Successfully logged out."}, status=205)
        except Exception as e:
            return Response({"detail": str(e)}, status=400)
