from django import forms

from .models import Product, User


class LoginForm(forms.Form):
    identification = forms.CharField(label="Identificacion")
    password = forms.CharField(label="Contrasena", widget=forms.PasswordInput)


class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = ["code", "name", "cost_price", "sell_price", "stock", "min_stock"]


class UserForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput, required=False)

    class Meta:
        model = User
        fields = ["full_name", "identification", "email", "phone", "password", "role"]

    def __init__(self, *args, allowed_roles=None, **kwargs):
        super().__init__(*args, **kwargs)
        allowed_roles = allowed_roles or [User.ROLE_CAJERO]
        self.fields["role"].choices = [choice for choice in User.ROLE_CHOICES if choice[0] in allowed_roles]
        if self.instance and self.instance.pk:
            self.fields["identification"].disabled = True
            self.fields["password"].required = False
        else:
            self.fields["password"].required = True

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
