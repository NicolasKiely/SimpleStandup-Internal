from django.contrib.auth.models import User

import standup.utils


def get_unread_notifications(request):
    """ GET handler to fetch notifications for a user

    GET Headers:
        - X-USER-EMAIL
    """
    bad_secret, response, args = standup.utils.check_request_secret(request)
    if bad_secret:
        return response

    try:
        user_email = request.headers.get("X-USER-EMAIL")
        user = User.objects.get(email__iexact=user_email)
    except User.DoesNotExist:
        return standup.utils.json_response(**standup.utils.USER_DOES_NOT_EXIST)

    notifications = [
        {
            "timestamp": note.dt_created,
            "message": note.message,
            "role": note.role
        }
        for note in user.notification_set.filter(dismissed=False)
    ]
    return standup.utils.json_response(payload=notifications)
