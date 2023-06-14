import requests
from django.conf import settings
from django.contrib import messages
import os

def check_turnstile(request):
    turnstile_token = request.POST.get('cf-turnstile-response')
    if turnstile_token:
        siteverify_url = 'https://challenges.cloudflare.com/turnstile/v0/siteverify'
        data = {
            'secret': settings.TURNSTILE_SECRET_KEY,
            'response': turnstile_token,
        }
        response = requests.post(siteverify_url, data=data)
        result = response.json()

        if result['success']:
            return True
        else:
            messages.error(request, 'Invalid captcha')
            return False
    else:
        messages.error(request, 'Captcha missing')
        return False

def get_secret(secret_name):
    secret = os.getenv(secret_name)

    if secret is None:
        try:
            with open(f'/run/secrets/{secret_name}') as secret_file:
                secret = secret_file.read().strip()
        except IOError:
            pass

    return secret