from django.urls import include, path
from api.views import index, asset

urlpatterns = [
    path("cyberar/api/", include("api.urls")),
    path("cyberar/assets/<str:name>", asset),
    path("cyberar/", index),
]
