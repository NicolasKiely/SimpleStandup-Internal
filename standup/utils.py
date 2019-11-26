from typing import Optional, Tuple
from django.http import JsonResponse

from standup import settings


#: Bad secret from external backend
BAD_SECRET_RESPONSE = {
    'payload': {},
    'message': 'Incorrect backend auth token',
    'error': 'BAD_SECRET_RESPONSE',
    'status': 500
}


def check_request_secret(request) -> Tuple[bool, Optional[JsonResponse]]:
    """ Returns boolean check that request has bad backend secret

    :return: Error flag set to true if auth failed, and associated response
    """
    if request.POST.get('BACKEND_SECRET') == settings.BACKEND_SECRET:
        return False, None

    else:
        error_response = JsonResponse(BAD_SECRET_RESPONSE)
        error_response.status_code = 403
        return True, error_response
