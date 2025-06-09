from django.urls import path
from apps.core.views import ScrapeView, ProviderConfigViewSet
from rest_framework.routers import SimpleRouter

router = SimpleRouter()
router.register(r'configs', ProviderConfigViewSet, basename='config')

urlpatterns = [
    path('scrape/', ScrapeView.as_view(), name='scrape'),
] + router.urls