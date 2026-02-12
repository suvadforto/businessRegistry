DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'business_registry',
        'USER': 'registry_user',
        'PASSWORD': 'robot123',
        'HOST': 'localhost',
        'PORT': '5432',
        'CONN_MAX_AGE': 60,
    }
}

AUTH_USER_MODEL = 'registry.User'

TIME_ZONE = 'UTC'
USE_TZ = True
LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'Europe/Sarajevo'
