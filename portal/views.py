from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from .forms import AiBriefForm, BookingForm, LeadProtectionForm
from .models import Booking, Lead, MarketTool, Property, Realtor
from .services import (
    AiRecommendationService,
    BookingService,
    DashboardService,
    LeadProtectionService,
)


def _demo_realtor() -> Realtor | None:
    return Realtor.objects.select_related("agency").order_by("-score").first()


def index(request):
    context = {
        "kpi": DashboardService.kpi(),
        "role": request.session.get("role", "agent"),
        "has_data": Realtor.objects.exists(),
    }
    return render(request, "portal/index.html", context)


def select_role(request, role: str):
    if role not in {"agent", "manager", "rop"}:
        role = "agent"
    request.session["role"] = role
    return redirect({"agent": "portal:agent", "manager": "portal:manager", "rop": "portal:rop"}[role])


def agent_portal(request):
    realtor = _demo_realtor()
    if not realtor:
        messages.warning(request, "Демоданные не найдены. Выполните `python manage.py seed_demo`.")
        return redirect("portal:index")

    project = request.GET.get("project", "")
    status = request.GET.get("status", "")
    rooms = request.GET.get("rooms", "")
    properties = Property.objects.all()
    if project:
        properties = properties.filter(project=project)
    if status:
        properties = properties.filter(status=status)
    if rooms:
        properties = properties.filter(rooms__startswith=rooms)

    context = {
        "realtor": realtor,
        "lead_form": LeadProtectionForm(),
        "booking_form": BookingForm(),
        "properties": properties,
        "projects": Property.objects.order_by("project").values_list("project", flat=True).distinct(),
        "active_leads": Lead.objects.filter(realtor=realtor, status=Lead.Status.PROTECTED)[:8],
        "recent_bookings": Booking.objects.filter(realtor=realtor).select_related("lot", "lead")[:6],
        "status_choices": Property.Status.choices,
    }
    return render(request, "portal/agent.html", context)


@require_POST
def protect_lead(request):
    realtor = _demo_realtor()
    if not realtor:
        messages.error(request, "Нет демо-риелтора.")
        return redirect("portal:index")

    form = LeadProtectionForm(request.POST)
    if form.is_valid():
        result = LeadProtectionService.protect(
            realtor=realtor,
            full_name=form.cleaned_data["full_name"],
            phone=form.cleaned_data["phone"],
            notes=form.cleaned_data["notes"],
        )
        if result.status == "conflict":
            messages.error(request, result.message)
        else:
            messages.success(request, result.message)
    else:
        messages.error(request, "Проверьте данные клиента.")
    return redirect("portal:agent")


@require_POST
def create_booking(request, property_id: int):
    realtor = _demo_realtor()
    if not realtor:
        messages.error(request, "Нет демо-риелтора.")
        return redirect("portal:index")

    form = BookingForm(request.POST)
    if form.is_valid():
        try:
            booking = BookingService.create_booking(
                realtor=realtor,
                lead_id=form.cleaned_data["lead_id"],
                property_id=property_id,
                payment_type=form.cleaned_data["payment_type"],
                manager_comment=form.cleaned_data["manager_comment"],
            )
            messages.success(
                request,
                f"Бронь #{booking.id} создана и отправлена менеджеру на подтверждение.",
            )
        except ValueError as exc:
            messages.error(request, str(exc))
    else:
        messages.error(request, "Выберите защищенного клиента и форму оплаты.")
    return redirect("portal:agent")


def manager_dashboard(request):
    bookings = Booking.objects.select_related("lead", "lot", "realtor", "realtor__agency")
    context = {
        "pending_bookings": bookings.filter(status=Booking.Status.PENDING),
        "processed_bookings": bookings.exclude(status=Booking.Status.PENDING)[:10],
        "kpi": DashboardService.kpi(),
    }
    return render(request, "portal/manager.html", context)


@require_POST
def approve_booking(request, booking_id: int):
    booking = BookingService.approve(booking_id)
    messages.success(request, f"Бронь #{booking.id} подтверждена. Агент получил баллы Resource Expert.")
    return redirect("portal:manager")


@require_POST
def reject_booking(request, booking_id: int):
    booking = BookingService.reject(booking_id)
    messages.warning(request, f"Бронь #{booking.id} отклонена. Лот снова доступен в витрине.")
    return redirect("portal:manager")


def rop_dashboard(request):
    context = {
        "kpi": DashboardService.kpi(),
        "agency_activity": DashboardService.agency_activity(),
        "recent_bookings": Booking.objects.select_related("lead", "lot", "realtor")[:8],
        "priority_properties": Property.objects.filter(is_priority=True)[:6],
    }
    return render(request, "portal/rop.html", context)


def ai_assistant(request):
    result = None
    form = AiBriefForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        result = AiRecommendationService.generate(
            budget_mln=form.cleaned_data["budget"],
            rooms=form.cleaned_data["rooms"],
            payment_type=form.cleaned_data["payment_type"],
            client_profile=form.cleaned_data["client_profile"],
            objection=form.cleaned_data["objection"],
        )
    context = {"form": form, "result": result}
    return render(request, "portal/ai.html", context)


def tool_comparison(request):
    tools = MarketTool.objects.all()
    selected = get_object_or_404(MarketTool, pk=request.GET.get("selected")) if request.GET.get("selected") else None
    return render(request, "portal/tools.html", {"tools": tools, "selected": selected})
