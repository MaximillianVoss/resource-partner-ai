from django.urls import path

from . import views

app_name = "portal"

urlpatterns = [
    path("", views.index, name="index"),
    path("role/<str:role>/", views.select_role, name="select_role"),
    path("agent/", views.agent_portal, name="agent"),
    path("agent/protect/", views.protect_lead, name="protect_lead"),
    path("agent/book/<int:property_id>/", views.create_booking, name="create_booking"),
    path("manager/", views.manager_dashboard, name="manager"),
    path("manager/booking/<int:booking_id>/approve/", views.approve_booking, name="approve_booking"),
    path("manager/booking/<int:booking_id>/reject/", views.reject_booking, name="reject_booking"),
    path("rop/", views.rop_dashboard, name="rop"),
    path("ai/", views.ai_assistant, name="ai"),
    path("tools/", views.tool_comparison, name="tools"),
]
