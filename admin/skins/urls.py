"""URL configuration for AgentSkin admin views.

Per AgentSkin UIX T8 (TR-AGS-004)
"""

from django.urls import path
from .views import SkinListView, SkinDetailView, SkinApproveView

app_name = 'skins'

urlpatterns = [
    # List and create skins
    path('', SkinListView.as_view(), name='skin-list'),
    
    # Get, update, delete specific skin
    path('<uuid:skin_id>/', SkinDetailView.as_view(), name='skin-detail'),
    
    # Approve/reject skin
    path('<uuid:skin_id>/approve/', SkinApproveView.as_view(), name='skin-approve'),
]
