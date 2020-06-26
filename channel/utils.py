from typing import List, Optional, Tuple

from django.contrib.auth.models import User
from django.http import JsonResponse

from channel import models
import standup.utils


ARGS_NO_CHANNEL_NAME = {
    "message": "No channel name given",
    "error": "INVALID_NAME",
    "json_status": 400,
    "http_status": 400
}

ARGS_INVALID_CHANNEL = {
    "message": "Invalid channel id given",
    "error": "INVALID_ID",
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

CHANNEL_OWNER_PERMISSION = {
    "message": "Must be channel owner",
    "error": "NOT_CHANNEL_OWNER",
    "json_status": 400,
    "http_status": 400
}

CHANNEL_NOT_FOUND = {
    "message": "No channel found for this user",
    "error": "CHANNEL_NOT_FOUND",
    "json_status": 404,
    "http_status": 404
}

CANT_INVITE_SELF = {
    "message": "Invite email address is same as user address",
    "error": "SELF_INVITE",
    "json_status": 400,
    "http_status": 400
}

USER_ALREADY_INVITED = {
    "message": "User already has been invited to this channel",
    "error": "ALREADY_INVITED",
    "json_status": 400,
    "http_status": 400
}


def get_channel_members(channel: models.Channel) -> List[User]:
    """ Returns list of members under a channel """
    owner = channel.owner
    return [owner]


def get_channel_by_member(
        user_email: str, channel_id: str
) -> Tuple[Optional[JsonResponse], Optional[models.Channel], List[User]]:
    """ Fetches channel by member email address, and check for common errors

    :param user_email: Email address to fetch channel as member
    :param channel_id: ID of channel to lookup
    :return: error response if request failed, channel, and member emails
    """
    # Try to parse channel id
    try:
        channel_id_int = int(channel_id)
    except ValueError:
        return standup.utils.json_response(**ARGS_INVALID_CHANNEL), None, []

    # Try to fetch channel object by id
    try:
        channel = models.Channel.objects.get(pk=channel_id_int)
    except models.Channel.DoesNotExist:
        return standup.utils.json_response(CHANNEL_NOT_FOUND), None, []

    # Get list of members for channel to check if user can see channel
    members = get_channel_members(channel)
    member_emails = [member.email.lower() for member in members]
    if user_email not in member_emails:
        return standup.utils.json_response(CHANNEL_NOT_FOUND), None, []

    return None, channel, members
