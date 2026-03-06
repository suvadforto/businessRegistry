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


USE_TZ = True
LANGUAGE_CODE = 'bs'
USE_I18N = True
LANGUAGES = [
    ('bs', 'Bosanski'),
]
USE_I18N = True

LOCALE_PATHS = [
    BASE_DIR / "locale",
]

TIME_ZONE = 'Europe/Sarajevo'

DATE_FORMAT = "d.m.Y"
DATE_INPUT_FORMATS = ["%d.%m.%Y"]