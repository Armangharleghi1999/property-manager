from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, viewsets, permissions

from .adapters.rightmove import RightmoveAdapter
from apps.sheets.sheets import append_row
from .models import ProviderConfig
from .serializers import ProviderConfigSerializer


class ScrapeView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request, *args, **kwargs):
        url = request.data.get('url')
        if not url:
            return Response(
                {"error": "You must provide a 'url' in the request body."},
                status=status.HTTP_400_BAD_REQUEST
            )
        try:
            data = RightmoveAdapter.fetch(url)
            append_row([
                data.get('url'),
                data.get('address'),
                data.get('price'),
                data.get('service_charge'),
            ])
            return Response(data, status=status.HTTP_201_CREATED)
        except Exception as exc:
            return Response(
                {"error": str(exc)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class ProviderConfigViewSet(viewsets.ModelViewSet):
    permission_classes = [permissions.IsAdminUser]
    queryset = ProviderConfig.objects.all()
    serializer_class = ProviderConfigSerializer