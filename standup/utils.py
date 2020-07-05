from django.http import JsonResponse
import json
from typing import Dict, List, Optional, Tuple, Union

from standup import settings


#: Bad secret from external backend
BAD_SECRET_RESPONSE = {
    'payload': {},
    'message': 'Incorrect backend auth token',
    'error': 'BAD_SECRET_RESPONSE',
    'status': 500
}

#: Bad POST encoding
BAD_ENCODE_RESPONSE = {
    'payload': {},
    'message': 'Could not decode request',
    'error': 'BAD_ENCODE',
    'status': 400
}

#: Stub response
NOT_IMPLEMENTED_RESPONSE = {
    'error': 'INT_NOT_IMPLEMENTED',
    'message': 'Feature not implemented internally',
    'json_status': 500,
    'http_status': 500
}

#: User not found
USER_DOES_NOT_EXIST = {
    "message": "Could not identify user",
    "error": "NO_USER",
    "json_status": 400,
    "http_status": 400
}

#: Notification not found
NOTIFICATION_DOES_NOT_EXIST = {
    "message": "Could not find notification",
    "error": "NO_NOTIFICATION",
    "json_status": 404,
    "http_status": 404
}


def json_response(
        payload: Optional[Union[List, Dict]] = None,
        message: str = None, error: str = None, json_status: int = 200,
        http_status: int = 200
):
    """ Helper function to create Django json response

    :param payload: Response payload
    :param message: Optional user-friendly message about status of request
    :param error: Optional error label
    :param json_status: External response status passed in json response
    :param http_status: Internal response status passed as http code
    """
    response = {
        'payload': {} if payload is None else payload,
        'status': json_status
    }
    if message is not None:
        response['message'] = message
    if error is not None:
        response['error'] = error

    j_response = JsonResponse(response)
    j_response.status_code = http_status
    return j_response


def get_request_args(request):
    """ Returns dict of request parameters """
    if request.body:
        return json.loads(request.body.decode('utf-8'))
    else:
        return request.POST


def check_request_secret(request) -> Tuple[bool, Optional[JsonResponse], Dict]:
    """ Returns boolean check that request has bad backend secret

    :return: Error flag set to true if auth failed, associated response,
    and parsed args
    """
    try:
        request_args = get_request_args(request)
    except UnicodeDecodeError:
        error_response = JsonResponse(BAD_ENCODE_RESPONSE)
        error_response.status_code = 400
        return True, error_response, {}

    request_secret = request_args.get('BACKEND_SECRET')
    if request_secret is None:
        request_secret = request.headers.get("X-BACKEND-SECRET")
    if request_secret == settings.BACKEND_SECRET:
        return False, None, request_args

    else:
        error_response = JsonResponse(BAD_SECRET_RESPONSE)
        error_response.status_code = 403
        return True, error_response, request_args


def parse_bool(value: Union[bool, str]) -> bool:
    """ Parses value as boolean """
    if isinstance(value, bool):
        return value

    if isinstance(value, str):
        lvalue = value.lower()
        if lvalue == "true":
            return True
        if lvalue == "false":
            return False
        raise ValueError("Invalid boolean value")
    raise ValueError("Invalid boolean type")


def assert_required_args(args: Dict, *names: str) -> Optional[JsonResponse]:
    """ Asserts that arguments are in dictionary

    :param args: Dictionary of argument values
    :param names: Name of arguments to load
    :return: Error response if failed, or None if okay
    """
    for arg_name in names:
        if arg_name not in args:
            err_response = json_response(
                error="MISSING_ARG",
                message="No value for %s" % arg_name,
                json_status=400,
                http_status=400
            )
            return err_response
    return None
