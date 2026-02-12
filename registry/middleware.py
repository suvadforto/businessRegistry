from .signals import set_current_user


class CurrentUserMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        user = getattr(request, 'user', None)
        if user and user.is_authenticated:
            set_current_user(user)
        else:
            set_current_user(None)

        response = self.get_response(request)
        return response
