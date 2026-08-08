import re

from django import forms

from .models import Product, User


PERSON_NAME_PATTERN = re.compile(
    r"^[A-Za-zÁÉÍÓÚÜÑáéíóúüñ]+(?:[ '\-][A-Za-zÁÉÍÓÚÜÑáéíóúüñ]+)*$"
)


class LoginForm(forms.Form):
    identification = forms.CharField(label="Identificación")
    password = forms.CharField(label="Contraseña", widget=forms.PasswordInput)


class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = ["code", "name", "cost_price", "sell_price", "stock", "min_stock"]

    def clean_code(self):
        code = self.cleaned_data["code"].strip().upper()
        if not re.fullmatch(r"[A-Z0-9._/-]{1,50}", code):
            raise forms.ValidationError(
                "El código solo puede usar letras, números, punto, guion o barra."
            )
        return code

    def clean_name(self):
        return " ".join(self.cleaned_data["name"].split())


class UserForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput, required=False)

    class Meta:
        model = User
        fields = ["full_name", "identification", "email", "phone", "password", "role"]

    def __init__(self, *args, allowed_roles=None, **kwargs):
        super().__init__(*args, **kwargs)
        allowed_roles = allowed_roles or [User.ROLE_CAJERO]
        self.fields["role"].choices = [
            choice for choice in User.ROLE_CHOICES if choice[0] in allowed_roles
        ]
        if self.instance and self.instance.pk:
            self.fields["identification"].disabled = True
            self.fields["password"].required = False
        else:
            self.fields["password"].required = True

    def clean_full_name(self):
        full_name = " ".join(self.cleaned_data["full_name"].split())
        if not PERSON_NAME_PATTERN.fullmatch(full_name):
            raise forms.ValidationError(
                "El nombre solo puede contener letras, espacios, guiones y apóstrofes."
            )
        return full_name

    def clean_identification(self):
        identification = self.cleaned_data["identification"].strip()
        if not re.fullmatch(r"\d{5,30}", identification):
            raise forms.ValidationError(
                "La identificación debe contener entre 5 y 30 dígitos."
            )
        return identification

    def clean_phone(self):
        phone = self.cleaned_data["phone"].strip()
        if phone and not re.fullmatch(r"\d{7,20}", phone):
            raise forms.ValidationError(
                "El teléfono debe contener entre 7 y 20 dígitos."
            )
        return phone

    def save(self, commit=True):
        user = super().save(commit=False)
        password = self.cleaned_data.get("password")
        if password:
            user.set_password(password)
        if not user.username:
            user.username = user.identification
        if commit:
            user.save()
        return user