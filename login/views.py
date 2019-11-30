import standup.utils


ARGS_INVALID_EMAIL = {
    'message': 'Invalid email address',
    'error': 'INVALID_EMAIL',
    'json_status': 400,
    'http_status': 400
}


# Create your views here.
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

    return standup.utils.json_response(
        **standup.utils.NOT_IMPLEMENTED_RESPONSE
    )
