from django import forms

from .models import Booking
from .services import normalize_phone


class LeadProtectionForm(forms.Form):
    full_name = forms.CharField(
        label="ФИО клиента",
        max_length=160,
        widget=forms.TextInput(attrs={"placeholder": "Например, Ирина Петрова"}),
    )
    phone = forms.CharField(
        label="Телефон",
        max_length=32,
        widget=forms.TextInput(attrs={"placeholder": "+7 999 000-00-00"}),
    )
    notes = forms.CharField(
        label="Комментарий",
        required=False,
        widget=forms.Textarea(attrs={"rows": 3, "placeholder": "Бюджет, сроки, интересующий ЖК"}),
    )

    def clean_phone(self) -> str:
        phone = normalize_phone(self.cleaned_data["phone"])
        if len(phone) < 10:
            raise forms.ValidationError("Введите корректный номер телефона.")
        return phone


class BookingForm(forms.Form):
    lead_id = forms.IntegerField(widget=forms.HiddenInput)
    payment_type = forms.ChoiceField(label="Форма оплаты", choices=Booking.PaymentType.choices)
    manager_comment = forms.CharField(
        label="Комментарий",
        required=False,
        widget=forms.Textarea(attrs={"rows": 2, "placeholder": "Комментарий для менеджера"}),
    )


class AiBriefForm(forms.Form):
    budget = forms.IntegerField(
        label="Бюджет клиента, млн руб.",
        min_value=3,
        max_value=30,
        initial=9,
    )
    rooms = forms.ChoiceField(
        label="Комнатность",
        choices=[
            ("any", "Любая"),
            ("1", "1-комнатная"),
            ("2", "2-комнатная"),
            ("3", "3-комнатная"),
            ("4", "4-комнатная"),
        ],
        required=False,
    )
    payment_type = forms.ChoiceField(label="Форма оплаты", choices=Booking.PaymentType.choices)
    client_profile = forms.CharField(
        label="Профиль клиента",
        widget=forms.Textarea(
            attrs={
                "rows": 3,
                "placeholder": "Например: семья с ребенком, нужна тишина, сомневаются из-за ставки",
            }
        ),
    )
    objection = forms.CharField(
        label="Главное возражение",
        required=False,
        widget=forms.TextInput(attrs={"placeholder": "Дорого / ждем снижения ставки / нужен торг"}),
    )
