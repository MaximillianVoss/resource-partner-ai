from decimal import Decimal

from django.core.management.base import BaseCommand
from django.utils import timezone

from portal.models import Agency, Booking, Lead, MarketTool, PartnerActivity, Property, Realtor
from portal.services import BookingService, LeadProtectionService


class Command(BaseCommand):
    help = "Seed demo data for the Resource Partner AI MVP."

    def handle(self, *args, **options):
        self.stdout.write("Seeding demo data...")

        Agency.objects.all().delete()
        MarketTool.objects.all().delete()
        Property.objects.all().delete()

        agencies = [
            Agency.objects.create(
                name="Этажи Ижевск",
                contact_person="Марина Кузнецова",
                phone="+7 912 000-10-01",
                status=Agency.Status.ACTIVE,
            ),
            Agency.objects.create(
                name="Самолет Плюс",
                contact_person="Андрей Селиванов",
                phone="+7 912 000-10-02",
                status=Agency.Status.ACTIVE,
            ),
            Agency.objects.create(
                name="Перспектива",
                contact_person="Елена Матвеева",
                phone="+7 912 000-10-03",
                status=Agency.Status.WATCH,
            ),
        ]

        realtors = [
            Realtor.objects.create(
                agency=agencies[0],
                full_name="Анна Орлова",
                phone="+7 912 400-33-22",
                email="orlova@example.ru",
                score=640,
                tier=Realtor.Tier.GOLD,
            ),
            Realtor.objects.create(
                agency=agencies[1],
                full_name="Илья Соколов",
                phone="+7 912 500-44-11",
                email="sokolov@example.ru",
                score=980,
                tier=Realtor.Tier.PLATINUM,
            ),
            Realtor.objects.create(
                agency=agencies[2],
                full_name="Ольга Мартынова",
                phone="+7 912 600-55-99",
                email="martynova@example.ru",
                score=260,
                tier=Realtor.Tier.SILVER,
            ),
        ]

        lots = [
            ("Lighthouse", "A", 4, "41", "1-комн.", 42.4, 6_290_000, Property.Status.AVAILABLE, True, False),
            ("Lighthouse", "A", 6, "62", "2-комн.", 61.8, 8_940_000, Property.Status.AVAILABLE, True, True),
            ("Lighthouse", "A", 8, "83", "2-комн.", 68.3, 10_180_000, Property.Status.AVAILABLE, False, False),
            ("Lighthouse", "B", 9, "91", "3-комн.", 86.2, 13_870_000, Property.Status.AVAILABLE, False, True),
            ("Lighthouse", "B", 11, "112", "4-комн.", 103.6, 17_950_000, Property.Status.AVAILABLE, False, True),
            ("Lighthouse", "B", 12, "121", "3-комн.", 91.1, 15_120_000, Property.Status.SOLD, True, False),
            ("Тетрис", "1", 5, "57", "1-комн.", 35.1, 4_820_000, Property.Status.AVAILABLE, True, False),
            ("Тетрис", "1", 7, "74", "1-комн.", 39.5, 5_260_000, Property.Status.AVAILABLE, True, False),
            ("Новый Сосновый", "2", 3, "32", "2-комн.", 58.6, 6_780_000, Property.Status.AVAILABLE, False, True),
            ("Новый Сосновый", "2", 8, "84", "3-комн.", 77.9, 8_450_000, Property.Status.AVAILABLE, False, True),
        ]
        for project, building, floor, apartment, rooms, area, price, status, finish, priority in lots:
            Property.objects.create(
                project=project,
                building=building,
                floor=floor,
                apartment_number=apartment,
                rooms=rooms,
                area=Decimal(str(area)),
                price=Decimal(str(price)),
                status=status,
                has_finish=finish,
                is_priority=priority,
            )

        LeadProtectionService.protect(
            realtor=realtors[1],
            full_name="Ирина Петрова",
            phone="+7 999 111-22-33",
            notes="Интересуется Lighthouse, 2-комн.",
        )
        LeadProtectionService.protect(
            realtor=realtors[1],
            full_name="Дмитрий Волков",
            phone="+7 999 222-33-44",
            notes="Рассматривает рассрочку.",
        )
        LeadProtectionService.protect(
            realtor=realtors[0],
            full_name="Сергей Климов",
            phone="+7 999 333-44-55",
            notes="Нужна 3-комн. для семьи.",
        )

        lead = Lead.objects.filter(realtor=realtors[1]).first()
        property_obj = Property.objects.filter(project="Lighthouse", status=Property.Status.AVAILABLE).first()
        if lead and property_obj:
            BookingService.create_booking(
                realtor=realtors[1],
                lead_id=lead.id,
                property_id=property_obj.id,
                payment_type=Booking.PaymentType.INSTALLMENT,
                manager_comment="Демо-бронь для показа менеджерского кабинета.",
            )

        PartnerActivity.objects.create(
            realtor=realtors[1],
            activity_type=PartnerActivity.ActivityType.EVENT,
            points=50,
            description="Посещение инженерного тура Lighthouse",
            created_at=timezone.now(),
        )

        MarketTool.objects.bulk_create(
            [
                MarketTool(
                    name="Bitrix24",
                    category="CRM",
                    implementation_cost="Низкая-средняя, зависит от тарифа и интегратора",
                    strengths="Знакомый для отдела продаж интерфейс, сделки, задачи, телефония, открытый REST API.",
                    weaknesses="Не решает задачу агентской витрины и шахматки без отдельного портала.",
                    expected_effect="Упорядочивание воронки и фиксация лидов внутри коммерческого блока.",
                    fit_score=8,
                ),
                MarketTool(
                    name="Profitbase",
                    category="Шахматка и склад недвижимости",
                    implementation_cost="Средняя, зависит от числа объектов и интеграций",
                    strengths="Актуальные статусы лотов, цены, планировки, связка с сайтом застройщика.",
                    weaknesses="Сам по себе не является полноценной PRM-системой для внешних агентов.",
                    expected_effect="Снижение задержек при уточнении наличия квартир и цен.",
                    fit_score=8,
                ),
                MarketTool(
                    name="amoCRM",
                    category="CRM",
                    implementation_cost="Низкая-средняя",
                    strengths="Быстро внедряется, удобная визуальная воронка, много готовых интеграций.",
                    weaknesses="Потребуется перенос процессов из Bitrix24 или параллельное ведение двух CRM.",
                    expected_effect="Может улучшить обработку лидов, но не закрывает проблему шахматки.",
                    fit_score=5,
                ),
                MarketTool(
                    name="Домклик Pro",
                    category="Партнерская платформа",
                    implementation_cost="Зависит от условий партнерства",
                    strengths="Понятен рынку недвижимости, связан с ипотечными сценариями и клиентским поиском.",
                    weaknesses="Ограниченная кастомизация под внутреннюю мотивацию Resource Expert.",
                    expected_effect="Расширение охвата, но слабый контроль собственной партнерской экосистемы.",
                    fit_score=6,
                ),
                MarketTool(
                    name="Собственный AI PRM-портал",
                    category="B2B AI SaaS",
                    implementation_cost="MVP: 1,5-2,5 млн руб.; развитие по этапам",
                    strengths="Защита сделки, личный кабинет агента, AI-подбор, интеграция Bitrix24 и Profitbase.",
                    weaknesses="Нужны разработка, сопровождение и регламент работы с персональными данными.",
                    expected_effect="Сокращение ручных операций, рост лояльности агентств, прозрачность KPI.",
                    fit_score=10,
                ),
            ]
        )

        self.stdout.write(self.style.SUCCESS("Demo data is ready."))
