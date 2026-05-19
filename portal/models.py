from __future__ import annotations

from datetime import timedelta

from django.db import models
from django.utils import timezone


class Agency(models.Model):
    class Status(models.TextChoices):
        ACTIVE = "active", "Активно"
        WATCH = "watch", "Нужен контакт"
        PAUSED = "paused", "Пауза"

    name = models.CharField("Название", max_length=160)
    city = models.CharField("Город", max_length=80, default="Ижевск")
    contact_person = models.CharField("Контактное лицо", max_length=120, blank=True)
    phone = models.CharField("Телефон", max_length=32, blank=True)
    status = models.CharField("Статус", max_length=20, choices=Status.choices, default=Status.ACTIVE)
    notes = models.TextField("Заметки", blank=True)

    class Meta:
        verbose_name = "Агентство"
        verbose_name_plural = "Агентства"
        ordering = ["name"]

    def __str__(self) -> str:
        return self.name


class Realtor(models.Model):
    class Tier(models.TextChoices):
        SILVER = "silver", "Silver"
        GOLD = "gold", "Gold"
        PLATINUM = "platinum", "Platinum"

    agency = models.ForeignKey(
        Agency, verbose_name="Агентство", on_delete=models.CASCADE, related_name="realtors"
    )
    full_name = models.CharField("ФИО", max_length=160)
    phone = models.CharField("Телефон", max_length=32)
    email = models.EmailField("Email", blank=True)
    score = models.PositiveIntegerField("Баллы Resource Expert", default=0)
    tier = models.CharField("Статус", max_length=20, choices=Tier.choices, default=Tier.SILVER)

    class Meta:
        verbose_name = "Риелтор"
        verbose_name_plural = "Риелторы"
        ordering = ["agency__name", "full_name"]

    def __str__(self) -> str:
        return f"{self.full_name}, {self.agency.name}"

    def recalculate_tier(self) -> None:
        if self.score >= 900:
            self.tier = self.Tier.PLATINUM
        elif self.score >= 450:
            self.tier = self.Tier.GOLD
        else:
            self.tier = self.Tier.SILVER


class Property(models.Model):
    class Status(models.TextChoices):
        AVAILABLE = "available", "Свободно"
        RESERVED = "reserved", "Бронь"
        SOLD = "sold", "Продано"

    project = models.CharField("Проект", max_length=120)
    building = models.CharField("Корпус", max_length=40)
    floor = models.PositiveSmallIntegerField("Этаж")
    apartment_number = models.CharField("Квартира", max_length=20)
    rooms = models.CharField("Комнатность", max_length=20)
    area = models.DecimalField("Площадь, кв. м", max_digits=6, decimal_places=2)
    price = models.DecimalField("Цена, руб.", max_digits=12, decimal_places=2)
    status = models.CharField("Статус", max_length=20, choices=Status.choices, default=Status.AVAILABLE)
    has_finish = models.BooleanField("Чистовая отделка", default=False)
    is_priority = models.BooleanField("Приоритетный лот", default=False)
    updated_at = models.DateTimeField("Обновлено", auto_now=True)

    class Meta:
        verbose_name = "Лот"
        verbose_name_plural = "Лоты"
        ordering = ["project", "building", "floor", "apartment_number"]

    def __str__(self) -> str:
        return f"{self.project}, кв. {self.apartment_number}"

    @property
    def price_mln(self) -> float:
        return round(float(self.price) / 1_000_000, 2)

    @property
    def installment_price(self) -> float:
        return round(float(self.price) * 1.15, 2)


class Lead(models.Model):
    class Status(models.TextChoices):
        PROTECTED = "protected", "Защищен"
        CONFLICT = "conflict", "Конфликт"
        EXPIRED = "expired", "Истек"

    full_name = models.CharField("ФИО клиента", max_length=160)
    phone = models.CharField("Телефон", max_length=32, db_index=True)
    realtor = models.ForeignKey(
        Realtor, verbose_name="Риелтор", on_delete=models.CASCADE, related_name="leads"
    )
    status = models.CharField("Статус", max_length=20, choices=Status.choices, default=Status.PROTECTED)
    protected_until = models.DateTimeField("Защита до")
    notes = models.TextField("Комментарий", blank=True)
    created_at = models.DateTimeField("Создан", auto_now_add=True)

    class Meta:
        verbose_name = "Лид"
        verbose_name_plural = "Лиды"
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"{self.full_name} ({self.phone})"

    @classmethod
    def default_protection_until(cls) -> timezone.datetime:
        return timezone.now() + timedelta(days=60)

    @property
    def is_active(self) -> bool:
        return self.status == self.Status.PROTECTED and self.protected_until >= timezone.now()


class Booking(models.Model):
    class Status(models.TextChoices):
        PENDING = "pending", "Ожидает менеджера"
        APPROVED = "approved", "Подтверждена"
        REJECTED = "rejected", "Отклонена"
        CANCELLED = "cancelled", "Отменена"

    class PaymentType(models.TextChoices):
        INSTALLMENT = "installment", "Рассрочка 30/70 +15%"
        MORTGAGE = "mortgage", "Ипотека"
        CASH = "cash", "100% оплата"

    lead = models.ForeignKey(Lead, verbose_name="Лид", on_delete=models.PROTECT, related_name="bookings")
    lot = models.ForeignKey(
        Property, verbose_name="Лот", on_delete=models.PROTECT, related_name="bookings"
    )
    realtor = models.ForeignKey(
        Realtor, verbose_name="Риелтор", on_delete=models.PROTECT, related_name="bookings"
    )
    status = models.CharField("Статус", max_length=20, choices=Status.choices, default=Status.PENDING)
    payment_type = models.CharField(
        "Форма оплаты", max_length=20, choices=PaymentType.choices, default=PaymentType.INSTALLMENT
    )
    down_payment_percent = models.PositiveSmallIntegerField("Первоначальный взнос, %", default=30)
    markup_percent = models.PositiveSmallIntegerField("Удорожание, %", default=15)
    manager_comment = models.TextField("Комментарий менеджера", blank=True)
    created_at = models.DateTimeField("Создана", auto_now_add=True)
    approved_at = models.DateTimeField("Подтверждена", null=True, blank=True)

    class Meta:
        verbose_name = "Бронь"
        verbose_name_plural = "Брони"
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"{self.lot} -> {self.lead}"

    @property
    def commission_amount(self) -> float:
        commission_rate = 0.04 if self.lot.is_priority else 0.03
        return round(float(self.lot.price) * commission_rate, 2)

    @property
    def expected_extra_margin(self) -> float:
        if self.payment_type != self.PaymentType.INSTALLMENT:
            return 0
        return round(float(self.lot.price) * 0.15 - self.commission_amount, 2)


class PartnerActivity(models.Model):
    class ActivityType(models.TextChoices):
        LEAD = "lead", "Заведен лид"
        BOOKING = "booking", "Создана бронь"
        APPROVED = "approved", "Бронь подтверждена"
        EVENT = "event", "Участие в мероприятии"

    realtor = models.ForeignKey(
        Realtor, verbose_name="Риелтор", on_delete=models.CASCADE, related_name="activities"
    )
    activity_type = models.CharField("Тип", max_length=20, choices=ActivityType.choices)
    points = models.PositiveIntegerField("Баллы", default=0)
    description = models.CharField("Описание", max_length=240)
    created_at = models.DateTimeField("Дата", auto_now_add=True)

    class Meta:
        verbose_name = "Активность партнера"
        verbose_name_plural = "Активность партнеров"
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"{self.realtor}: {self.description}"


class MarketTool(models.Model):
    name = models.CharField("Инструмент", max_length=120)
    category = models.CharField("Категория", max_length=80)
    implementation_cost = models.CharField("Стоимость внедрения", max_length=120)
    strengths = models.TextField("Плюсы")
    weaknesses = models.TextField("Минусы")
    expected_effect = models.TextField("Ожидаемый эффект")
    fit_score = models.PositiveSmallIntegerField("Соответствие задаче, 1-10", default=5)

    class Meta:
        verbose_name = "Рыночный инструмент"
        verbose_name_plural = "Рыночные инструменты"
        ordering = ["-fit_score", "name"]

    def __str__(self) -> str:
        return self.name
