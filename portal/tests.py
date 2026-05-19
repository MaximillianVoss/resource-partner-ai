from django.test import TestCase

from .models import Agency, Lead, Property, Realtor
from .services import BookingService, LeadProtectionService


class PortalWorkflowTests(TestCase):
    def setUp(self):
        self.agency = Agency.objects.create(name="Test Agency")
        self.realtor = Realtor.objects.create(
            agency=self.agency,
            full_name="Test Realtor",
            phone="+7 999 000-00-00",
        )
        self.property = Property.objects.create(
            project="Lighthouse",
            building="A",
            floor=5,
            apartment_number="55",
            rooms="2-комн.",
            area=60,
            price=9_000_000,
        )

    def test_lead_protection_creates_active_lead(self):
        result = LeadProtectionService.protect(
            realtor=self.realtor,
            full_name="Test Client",
            phone="+7 999 111-22-33",
        )

        self.assertEqual(result.status, "created")
        self.assertEqual(Lead.objects.count(), 1)
        self.assertTrue(result.lead.is_active)

    def test_booking_reserves_property(self):
        result = LeadProtectionService.protect(
            realtor=self.realtor,
            full_name="Test Client",
            phone="+7 999 111-22-33",
        )
        booking = BookingService.create_booking(
            realtor=self.realtor,
            lead_id=result.lead.id,
            property_id=self.property.id,
            payment_type="installment",
        )

        self.property.refresh_from_db()
        self.assertEqual(booking.status, "pending")
        self.assertEqual(self.property.status, Property.Status.RESERVED)
