from django.contrib import auth
from django.contrib.auth.models import User

import standup.utils


ARGS_INVALID_EMAIL = {
    'message': 'Invalid email address',
    'error': 'INVALID_EMAIL',
    'json_status': 400,
    'http_status': 400
}


def register_user(request):
    """ POST handler for registering a user

    POST Parameters:
    - user_email: Email to register user under
    - user_pass: Password for user
    - user_fname: First name for user (optional)
    - user_lname: Last name for user (optional)
    """
    bad_secret, response, args = standup.utils.check_request_secret(request)
    if bad_secret:
        return response

    user_email = args.get('user_email', '')
    user_pass = args.get('user_pass', '')
    user_lname = args.get('user_lname', '')
    user_fname = args.get('user_fname', '')

    # Validate request
    if not user_email:
        return standup.utils.json_response(
            message='No email address given',
            error='INVALID_EMAIL',
            json_status=400,
            http_status=400
        )

    if not user_pass:
        return standup.utils.json_response(
            message='No password given',
            error='INVALID_PASS',
            json_status=400,
            http_status=400
        )

    if user_email.count('@') != 1:
        return standup.utils.json_response(**ARGS_INVALID_EMAIL)

    user_email_name, user_email_host = user_email.split('@')
    if len(user_email_name) == 0 or len(user_email_host) == 0:
        return standup.utils.json_response(**ARGS_INVALID_EMAIL)

    if User.objects.filter(email__iexact=user_email).count() > 0:
        return standup.utils.json_response(
            payload={},
            message='Email address already registered',
            error='EMAIL_USED',
            json_status=400,
            http_status=400
        )

    # No problems found so far. Create user account.
    user = User.objects.create_user(
        username=user_email, email=user_email, password=user_pass,
        first_name=user_fname, last_name=user_lname
    )

    return standup.utils.json_response(
        payload={
            'email': user.email,
            'fname': user.first_name,
            'lname': user.last_name
        },
        message='Account created'
    )


def authenticate_user(request):
    """ POST Handler for authenticating frontend user

    POST Parameters:
    - user_email: Account address to login under
    - user_pass: Given account password
    """
    bad_secret, response, args = standup.utils.check_request_secret(request)
    if bad_secret:
        return response

    user_email = args.get('user_email', '')
    user_pass = args.get('user_pass', '')

    user = auth.authenticate(username=user_email, password=user_pass)
    if user and user.is_active:
        return standup.utils.json_response(
            payload={'email': user.email},
            message='User authenticated'
        )

    else:
        return standup.utils.json_response(
            payload={},
            message='Cannot authenticate account',
            error='AUTH_FAILED',
            json_status=403
        )


def get_user_settings(request):
    """ GET handler for fetching user's settings """
    bad_secret, response, args = standup.utils.check_request_secret(request)
    if bad_secret:
        return response

    user_email = request.headers.get("X-USER-EMAIL").lower()
    try:
        user = User.objects.get(email__iexact=user_email)
    except User.DoesNotExist:
        return standup.utils.json_response(**standup.utils.USER_DOES_NOT_EXIST)

    return standup.utils.json_response(
        payload={
            "user": {
                "first_name": user.first_name,
                "last_name": user.last_name,
                "email": user.email
            }
        }
    )


def set_user_name(request):
    """ POST hander for setting user's name """
    bad_secret, response, args = standup.utils.check_request_secret(request)
    if bad_secret:
        return response

    err = standup.utils.assert_required_args(args, "first_name", "last_name")
    if err:
        return err

    first_name = args["first_name"].strip()
    last_name = args["last_name"].strip()
    user_email = request.headers.get("X-USER-EMAIL").lower()
    try:
        user = User.objects.get(email__iexact=user_email)
    except User.DoesNotExist:
        return standup.utils.json_response(**standup.utils.USER_DOES_NOT_EXIST)

    name_len = len(user.first_name) + len(user.last_name)
    if name_len > 32:
        return standup.utils.json_response(
            message="User name is too long",
            error="BAD_NAME",
            json_status=400,
            http_status=400
        )

    if name_len <= 0:
        return standup.utils.json_response(
            message="USer name is too short",
            error="BAD_NAME",
            json_status=400,
            http_status=400
        )

    user.first_name = first_name
    user.last_name = last_name
    user.save()

    return standup.utils.json_response(
        payload={
            "user": {
                "email": user.email,
                "first_name": user.first_name,
                "last_name": user.last_name
            }
        }
    )
