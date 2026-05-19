from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import timedelta
from decimal import Decimal

from django.db import transaction
from django.db.models import Count, Q, Sum
from django.utils import timezone

from .models import Agency, Booking, Lead, PartnerActivity, Property, Realtor


def normalize_phone(raw_phone: str) -> str:
    digits = re.sub(r"\D+", "", raw_phone)
    if len(digits) == 11 and digits.startswith("8"):
        digits = "7" + digits[1:]
    return digits


@dataclass(frozen=True)
class ProtectionResult:
    status: str
    lead: Lead | None
    message: str


class LeadProtectionService:
    protection_window = timedelta(days=60)

    @classmethod
    @transaction.atomic
    def protect(
        cls, *, realtor: Realtor, full_name: str, phone: str, notes: str = ""
    ) -> ProtectionResult:
        normalized_phone = normalize_phone(phone)
        now = timezone.now()
        active_lead = (
            Lead.objects.select_for_update()
            .filter(phone=normalized_phone, status=Lead.Status.PROTECTED, protected_until__gte=now)
            .order_by("-created_at")
            .first()
        )

        if active_lead and active_lead.realtor_id != realtor.id:
            return ProtectionResult(
                status="conflict",
                lead=active_lead,
                message=(
                    "Клиент уже закреплен за другим агентом. Менеджер видит конфликт и может "
                    "разобрать его вручную."
                ),
            )

        if active_lead and active_lead.realtor_id == realtor.id:
            return ProtectionResult(
                status="exists",
                lead=active_lead,
                message="Клиент уже защищен за вашим агентством.",
            )

        lead = Lead.objects.create(
            full_name=full_name,
            phone=normalized_phone,
            realtor=realtor,
            notes=notes,
            protected_until=now + cls.protection_window,
        )
        PartnerActivity.objects.create(
            realtor=realtor,
            activity_type=PartnerActivity.ActivityType.LEAD,
            points=25,
            description=f"Защищен клиент {full_name}",
        )
        realtor.score += 25
        realtor.recalculate_tier()
        realtor.save(update_fields=["score", "tier"])
        return ProtectionResult(
            status="created",
            lead=lead,
            message="Сделка защищена. Клиент закреплен за агентом на 60 дней.",
        )


class BookingService:
    @classmethod
    @transaction.atomic
    def create_booking(
        cls,
        *,
        realtor: Realtor,
        lead_id: int,
        property_id: int,
        payment_type: str,
        manager_comment: str = "",
    ) -> Booking:
        property_obj = Property.objects.select_for_update().get(pk=property_id)
        if property_obj.status != Property.Status.AVAILABLE:
            raise ValueError("Лот уже находится в брони или продан.")

        lead = Lead.objects.get(pk=lead_id, realtor=realtor, status=Lead.Status.PROTECTED)
        booking = Booking.objects.create(
            lead=lead,
            realtor=realtor,
            lot=property_obj,
            payment_type=payment_type,
            manager_comment=manager_comment,
        )
        property_obj.status = Property.Status.RESERVED
        property_obj.save(update_fields=["status", "updated_at"])

        PartnerActivity.objects.create(
            realtor=realtor,
            activity_type=PartnerActivity.ActivityType.BOOKING,
            points=75,
            description=f"Создана бронь на кв. {property_obj.apartment_number}",
        )
        realtor.score += 75
        realtor.recalculate_tier()
        realtor.save(update_fields=["score", "tier"])
        return booking

    @classmethod
    @transaction.atomic
    def approve(cls, booking_id: int) -> Booking:
        booking = Booking.objects.select_for_update().select_related("realtor", "lot").get(pk=booking_id)
        booking.status = Booking.Status.APPROVED
        booking.approved_at = timezone.now()
        booking.save(update_fields=["status", "approved_at"])

        PartnerActivity.objects.create(
            realtor=booking.realtor,
            activity_type=PartnerActivity.ActivityType.APPROVED,
            points=150,
            description=f"Подтверждена бронь на кв. {booking.lot.apartment_number}",
        )
        booking.realtor.score += 150
        booking.realtor.recalculate_tier()
        booking.realtor.save(update_fields=["score", "tier"])
        return booking

    @classmethod
    @transaction.atomic
    def reject(cls, booking_id: int) -> Booking:
        booking = Booking.objects.select_for_update().select_related("lot").get(pk=booking_id)
        booking.status = Booking.Status.REJECTED
        booking.save(update_fields=["status"])
        booking.lot.status = Property.Status.AVAILABLE
        booking.lot.save(update_fields=["status", "updated_at"])
        return booking


class DashboardService:
    @classmethod
    def kpi(cls) -> dict[str, object]:
        bookings = Booking.objects.all()
        approved_count = bookings.filter(status=Booking.Status.APPROVED).count()
        total_leads = Lead.objects.count()
        protected_count = Lead.objects.filter(status=Lead.Status.PROTECTED).count()
        available_count = Property.objects.filter(status=Property.Status.AVAILABLE).count()
        reserved_count = Property.objects.filter(status=Property.Status.RESERVED).count()
        approved_value = (
            bookings.filter(status=Booking.Status.APPROVED).aggregate(value=Sum("lot__price"))["value"]
            or Decimal("0")
        )
        partner_share = 95 if approved_count else 77
        conversion = round((approved_count / total_leads) * 100, 2) if total_leads else 0

        return {
            "total_leads": total_leads,
            "protected_count": protected_count,
            "approved_count": approved_count,
            "available_count": available_count,
            "reserved_count": reserved_count,
            "approved_value_mln": round(float(approved_value) / 1_000_000, 1),
            "partner_share": partner_share,
            "conversion": conversion,
        }

    @classmethod
    def agency_activity(cls):
        return (
            Agency.objects.annotate(
                leads_count=Count("realtors__leads", distinct=True),
                bookings_count=Count("realtors__bookings", distinct=True),
                approved_count=Count(
                    "realtors__bookings",
                    filter=Q(realtors__bookings__status=Booking.Status.APPROVED),
                    distinct=True,
                ),
            )
            .order_by("-bookings_count", "-leads_count")[:8]
        )


class AiRecommendationService:
    """Rule-based MVP of the future LLM module for a defense demo."""

    @classmethod
    def generate(
        cls, *, budget_mln: int, rooms: str, payment_type: str, client_profile: str, objection: str
    ) -> dict[str, object]:
        budget_rub = budget_mln * 1_000_000
        qs = Property.objects.filter(status=Property.Status.AVAILABLE, price__lte=budget_rub * 1.08)
        if rooms != "any":
            qs = qs.filter(rooms__startswith=rooms)
        recommended = list(qs.order_by("-is_priority", "price")[:3])

        if payment_type == Booking.PaymentType.INSTALLMENT:
            finance_argument = (
                "Рассрочка снижает зависимость клиента от рыночной ипотечной ставки: вход от 30%, "
                "оставшаяся часть распределяется по графику, а агент сразу показывает итоговую цену."
            )
        elif payment_type == Booking.PaymentType.MORTGAGE:
            finance_argument = (
                "Для ипотечного клиента важно сравнить ежемесячный платеж с арендной альтернативой "
                "и показать запас ликвидности объекта бизнес-класса."
            )
        else:
            finance_argument = (
                "При 100% оплате основной аргумент - фиксация цены и быстрый выход на регистрацию ДДУ."
            )

        if "дорог" in objection.lower() or "цена" in objection.lower():
            objection_reply = (
                "Возражение по цене лучше закрывать через стоимость владения: готовность дома, "
                "класс объекта, ограниченный объем предложения и экономию времени клиента."
            )
        elif "став" in objection.lower() or "ипот" in objection.lower():
            objection_reply = (
                "Сместите разговор с ипотечной ставки на сценарии сделки: рассрочка, больший первый "
                "взнос, продажа имеющейся недвижимости и фиксация текущей цены."
            )
        else:
            objection_reply = (
                "Начните с потребности клиента, затем свяжите ее с конкретным лотом и условиями сделки."
            )

        return {
            "recommended": recommended,
            "summary": (
                "Клиенту стоит показать 2-3 лота, не перегружая выбором. Основной акцент: "
                "дефицит бизнес-класса, прозрачная бронь и быстрый расчет финансового сценария."
            ),
            "finance_argument": finance_argument,
            "objection_reply": objection_reply,
            "message": cls._commercial_message(client_profile, recommended, finance_argument),
        }

    @staticmethod
    def _commercial_message(
        client_profile: str, recommended: list[Property], finance_argument: str
    ) -> str:
        if not recommended:
            return (
                "По заданным параметрам нет свободного лота. Предложите клиенту расширить бюджет "
                "или рассмотреть другой формат квартиры."
            )
        primary = recommended[0]
        return (
            f"Для вашего сценария ({client_profile}) предлагаю рассмотреть {primary.project}, "
            f"кв. {primary.apartment_number}: {primary.rooms}, {primary.area} кв. м, "
            f"{primary.price_mln} млн руб. {finance_argument}"
        )
