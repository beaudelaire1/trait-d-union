"""URL configuration for the simulateur app."""
from django.urls import path

from .views import (
    AcseView,
    CacView,
    ElasticiteView,
    FragmentationView,
    FrictionView,
    HubView,
    PlafondView,
    PointMortView,
    RetentionView,
    SimulateurView,
    ValleeMortView,
)

app_name = 'simulateur'

urlpatterns = [
    path('', HubView.as_view(), name='hub'),
    path('devis/', SimulateurView.as_view(), name='devis'),
    path('point-mort/', PointMortView.as_view(), name='point-mort'),
    path('cac/', CacView.as_view(), name='cac'),
    path('friction/', FrictionView.as_view(), name='friction'),
    path('fragmentation/', FragmentationView.as_view(), name='fragmentation'),
    path('acse/', AcseView.as_view(), name='acse'),
    path('plafond/', PlafondView.as_view(), name='plafond'),
    path('elasticite/', ElasticiteView.as_view(), name='elasticite'),
    path('vallee-mort/', ValleeMortView.as_view(), name='vallee-mort'),
    path('retention/', RetentionView.as_view(), name='retention'),
]
