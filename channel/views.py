from django.contrib.auth.models import User

from channel import models
from channel import utils
import standup.utils


ARGS_NO_CHANNEL_NAME = {
    "message": "No channel name given",
    "error": "INVALID_NAME",
    "json_status": 400,
    "http_status": 400
}

USER_DOES_NOT_EXIST = {
    "message": "Could not identify user",
    "error": "NO_USER",
    "json_status": 400,
    "http_status": 400
}

CHANNEL_ALREADY_EXISTS = {
    "message": "Channel already exists",
    "error": "CHANNEL_EXISTS",
    "json_status": 400,
    "http_status": 400
}

CHANNEL_NOT_FOUND = {
    "message": "No channel found for this user",
    "error": "CHANNEL_NOT_FOUND",
    "json_status": 404,
    "http_status": 404
}


def create_channel(request):
    """ POST handler for creating new channel

    POST Parameters:
        - user_email: Account address to create channel for
        - channel_name: Name of channel to create
    """
    bad_secret, response, args = standup.utils.check_request_secret(request)
    if bad_secret:
        return response

    user_email = args.get("user_email", "")
    channel_name = args.get("channel_name", "")

    if not channel_name:
        # Assert that channel name is given
        return standup.utils.json_response(**ARGS_NO_CHANNEL_NAME)

    try:
        user = User.objects.get(email__iexact=user_email)
    except User.DoesNotExist:
        return standup.utils.json_response(**USER_DOES_NOT_EXIST)

    if models.Channel.objects.filter(owner=user, name__iexact=channel_name).count():
        return standup.utils.json_response(**CHANNEL_ALREADY_EXISTS)

    channel = models.Channel(owner=user, name=channel_name)
    channel.save()
    return standup.utils.json_response(
        payload={"channel_name": channel_name},
        message="Channel created",
    )


def list_channels(request):
    """ GET handler to fetch channels for given user

    GET Headers:
        - X-USER-EMAIL
    """
    bad_secret, response, args = standup.utils.check_request_secret(request)
    if bad_secret:
        return response

    user_email = request.headers.get("X-USER-EMAIL")

    try:
        user = User.objects.get(email__iexact=user_email)
    except User.DoesNotExist:
        return standup.utils.json_response(**USER_DOES_NOT_EXIST)

    channels = [
        {"channel_name": channel.name, "owner": channel.owner.email}
        for channel in user.channel_set.all()
    ]
    return standup.utils.json_response(payload=channels)


def get_channel_users(request):
    """ GET handler to fetch members of a channel

    GET HEADERS:
        - X-USER-EMAIL

    PARAMETERS:
        - owner: Address of owner
        - channel_name: Name of channel
    """
    bad_secret, response, args = standup.utils.check_request_secret(request)
    if bad_secret:
        return response

    user_email = request.headers.get("X-USER-EMAIL")
    owner = request.GET.get("owner", "")
    channel_name = request.GET.get("channel_name", "")

    try:
        channel = models.Channel.objects.filter(owner=owner, name=channel_name)
    except models.Channel.DoesNotExist:
        return standup.utils.json_response(CHANNEL_NOT_FOUND)

    members = utils.get_channel_members(channel)
    member_emails = [member.email.lower() for member in members]

    if user_email in member_emails:
        # Successfully found channel
        return standup.utils.json_response(payload=member_emails)

    return standup.utils.json_response(CHANNEL_NOT_FOUND)
