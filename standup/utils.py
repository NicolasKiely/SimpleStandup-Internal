from typing import Dict, List, Optional, Tuple, Union
from django.http import JsonResponse

from standup import settings


#: Bad secret from external backend
BAD_SECRET_RESPONSE = {
    'payload': {},
    'message': 'Incorrect backend auth token',
    'error': 'BAD_SECRET_RESPONSE',
    'status': 500
}

#: Stub response
NOT_IMPLEMENTED_RESPONSE = {
    'error': 'INT_NOT_IMPLEMENTED',
    'message': 'Feature not implemented internally',
    'status': 500
}


def json_response(
        payload: Optional[Union[List, Dict]]=None,
        message: str=None, error: str=None, status: int=200
):
    """ Helper function to create Django json response """
    response = {
        'payload': {} if payload is None else payload,
        'status': status
    }
    if message is not None:
        response['message'] = message
    if error is not None:
        response['error'] = error

    return JsonResponse(response)


def check_request_secret(request) -> Tuple[bool, Optional[JsonResponse]]:
    """ Returns boolean check that request has bad backend secret

    :return: Error flag set to true if auth failed, and associated response
    """
    request_secret = request.POST.get('BACKEND_SECRET')
    if request_secret == settings.BACKEND_SECRET:
        print('Bad secret: %s' % request_secret)
        return True, None

    else:
        error_response = JsonResponse(BAD_SECRET_RESPONSE)
        error_response.status_code = 403
        return False, error_response
