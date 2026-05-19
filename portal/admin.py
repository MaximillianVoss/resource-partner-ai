from django.contrib import admin

from .models import Agency, Booking, Lead, MarketTool, PartnerActivity, Property, Realtor


@admin.register(Agency)
class AgencyAdmin(admin.ModelAdmin):
    list_display = ("name", "city", "contact_person", "status")
    search_fields = ("name", "contact_person", "phone")
    list_filter = ("status", "city")


@admin.register(Realtor)
class RealtorAdmin(admin.ModelAdmin):
    list_display = ("full_name", "agency", "phone", "score", "tier")
    search_fields = ("full_name", "phone", "agency__name")
    list_filter = ("tier", "agency")


@admin.register(Property)
class PropertyAdmin(admin.ModelAdmin):
    list_display = (
        "project",
        "building",
        "apartment_number",
        "rooms",
        "area",
        "price",
        "status",
        "is_priority",
    )
    list_filter = ("project", "status", "rooms", "is_priority")
    search_fields = ("project", "building", "apartment_number")


@admin.register(Lead)
class LeadAdmin(admin.ModelAdmin):
    list_display = ("full_name", "phone", "realtor", "status", "protected_until", "created_at")
    list_filter = ("status", "created_at")
    search_fields = ("full_name", "phone", "realtor__full_name")


@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = ("lead", "lot", "realtor", "status", "payment_type", "created_at")
    list_filter = ("status", "payment_type", "created_at")
    search_fields = ("lead__full_name", "lot__apartment_number", "realtor__full_name")


@admin.register(PartnerActivity)
class PartnerActivityAdmin(admin.ModelAdmin):
    list_display = ("realtor", "activity_type", "points", "created_at")
    list_filter = ("activity_type", "created_at")


@admin.register(MarketTool)
class MarketToolAdmin(admin.ModelAdmin):
    list_display = ("name", "category", "implementation_cost", "fit_score")
    list_filter = ("category", "fit_score")
