from django import forms
from django.contrib.auth.forms import AuthenticationForm
from .helpers import check_turnstile

class EmailUpdateForm(forms.Form):
    email = forms.EmailField(required=False)

class AuthAdminForm(AuthenticationForm):
    def clean(self):
        request = self.request
        if not check_turnstile(request):
            raise forms.ValidationError("Invalid captcha.")
        return super().clean()