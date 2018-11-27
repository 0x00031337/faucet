from django.urls import path
from django.views.generic.base import RedirectView
from django.conf import settings

from . import views

app_name = "transactions"
urlpatterns = [
    path(
        "transactions/",
        views.TransactionsApiView.as_view(),
        name="transactions",
    ),
    path("", views.index, name="index"),
    path(
        "favicon.ico",
        RedirectView.as_view(url=settings.STATIC_URL + "favicon.ico"),
    ),
]
