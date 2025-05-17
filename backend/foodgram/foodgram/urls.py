from django.contrib import admin
from django.urls import include, path

from api.utils import redirect_to_recipe

urlpatterns = [
    path('r/<str:short_id>/', redirect_to_recipe, name='short_url'),
    path('admin/', admin.site.urls),
    path('api/', include('api.urls')),
]
