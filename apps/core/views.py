"""
Views for the core app of the Property Manager project.

This file contains:
- API views for scraping property data and appending it to Google Sheets
- ViewSets for managing provider configurations
"""

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, viewsets, permissions
from apps.sheets.sheets import append_row

from .adapters.rightmove import RightmoveAdapter
from .models import ProviderConfig
from .serializers import ProviderConfigSerializer


class ScrapeView(APIView):
    """API view to scrape property data from a given URL and append it to Google Sheets."""

    permission_classes = [permissions.AllowAny]

    def post(self, request):
        """Handle POST requests to scrape property data from the provided URL.

        Args:
            request: The HTTP request object containing the 'url' in the body.

        Returns:
            Response: A JSON response with the scraped data or an error message.
        """
        url = request.data.get("url")
        if not url:
            return Response(
                {"error": "You must provide a 'url' in the request body."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        try:
            data = RightmoveAdapter.fetch(url)
            append_row(
                [
                    data.get("url"),
                    data.get("address"),
                    data.get("price"),
                    data.get("service_charge"),
                ]
            )
            return Response(data, status=status.HTTP_201_CREATED)
        except ValueError as exc:
            return Response(
                {"error": str(exc)}, status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as exc:
            return Response(
                {"error": "An unexpected error occurred: " + str(exc)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class ProviderConfigViewSet(viewsets.ModelViewSet):
    """ViewSet for managing ProviderConfig objects."""

    permission_classes = [permissions.IsAdminUser]
    queryset = ProviderConfig.objects.all()
    serializer_class = ProviderConfigSerializer
