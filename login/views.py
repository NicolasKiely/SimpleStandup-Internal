from django.http import JsonResponse

import standup.utils


# Create your views here.
def register_user(request):
    """ POST handler for registering a user """
    bad_secret, response = standup.utils.check_request_secret(request)
    if bad_secret:
        return response

    return standup.utils.json_response(
        **standup.utils.NOT_IMPLEMENTED_RESPONSE
    )
