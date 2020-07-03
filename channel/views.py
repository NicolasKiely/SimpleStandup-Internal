from django.contrib.auth.models import User
from django.db import IntegrityError

from channel import models
from channel import utils
import notification.models
import standup.utils


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
        return standup.utils.json_response(**utils.ARGS_NO_CHANNEL_NAME)

    try:
        user = User.objects.get(email__iexact=user_email)
    except User.DoesNotExist:
        return standup.utils.json_response(**standup.utils.USER_DOES_NOT_EXIST)

    prexisting = models.Channel.objects.filter(
        owner=user, name__iexact=channel_name
    ).first()
    if prexisting:
        # Channel already exists
        if prexisting.archived:
            # Channel is archived, so restore it
            prexisting.archived = False
            prexisting.save()
            return standup.utils.json_response(
                payload={"channel_name": channel_name},
                message="Channel created"
            )
        # Duplicate channel error
        return standup.utils.json_response(**utils.CHANNEL_ALREADY_EXISTS)

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
        return standup.utils.json_response(**standup.utils.USER_DOES_NOT_EXIST)

    user_channels = user.channel_set.all()
    member_channels = [
        member.channel
        for member in user.channelmember_set.exclude(channel__in=user_channels)
    ]
    channels = [
        {
            "channel_name": channel.name,
            "owner": channel.owner.email,
            "channel_id": channel.id,
            "archived": channel.archived,
        }
        for channel in list(user_channels) + member_channels
    ]
    return standup.utils.json_response(payload=channels)


def archive_channel(request):
    """ POST handler to archive a channel for a given user

    POST Headers:
        - X-USER-EMAIL
    """
    bad_secret, response, args = standup.utils.check_request_secret(request)
    if bad_secret:
        return response

    user_email = request.headers.get("X-USER-EMAIL")
    channel_id = args.get("channel_id")
    err_response, channel, _ = utils.get_channel_by_member(user_email, channel_id)
    if err_response:
        return err_response

    if user_email == channel.owner.email:
        # Archive as owner
        channel.archived = True
        channel.save()
        msg = "Archived channel"
    else:
        # Leave channel for user
        try:
            models.ChannelMember.objects.get(
                channel=channel, user__email=user_email
            ).delete()
        except models.ChannelMember.DoesNotExist:
            return standup.utils.json_response(
                **utils.CHANNEL_NOT_FOUND
            )
        msg = "Left channel"

    return standup.utils.json_response(
        payload={"channel_id": channel_id}, message=msg
    )


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
        return standup.utils.json_response(**utils.CHANNEL_NOT_FOUND)

    members = utils.get_channel_members(channel)
    member_emails = [member.email.lower() for member in members]

    if user_email in member_emails:
        # Successfully found channel
        return standup.utils.json_response(payload=member_emails)

    return standup.utils.json_response(**utils.CHANNEL_NOT_FOUND)


def invite_user_to_channel(request):
    """ POST handler to handle request to invite user to channel

    POST Headers:
        - X-USER-EMAIL

    POST Parameters:
        - channel_id: ID of channel to invite user to
        - invite_email: Account address to create channel for
    """
    bad_secret, response, args = standup.utils.check_request_secret(request)
    if bad_secret:
        return response

    invite_email = args.get("invite_email").lower()
    user_email = request.headers.get("X-USER-EMAIL").lower()
    channel_id = args.get("channel_id")
    err_response, channel, members = utils.get_channel_by_member(
        user_email, channel_id
    )
    if err_response:
        return err_response

    try:
        user = User.objects.get(email__iexact=user_email)
    except User.DoesNotExist:
        return standup.utils.json_response(**standup.utils.USER_DOES_NOT_EXIST)

    # Verification checks
    if user_email != channel.owner.email.lower():
        return standup.utils.json_response(**utils.CHANNEL_OWNER_PERMISSION)

    if user_email == invite_email:
        return standup.utils.json_response(**utils.CANT_INVITE_SELF)

    if invite_email in [member.email.lower() for member in members]:
        return standup.utils.json_response(**utils.USER_ALREADY_INVITED)

    try:
        invite_user = User.objects.get(email__iexact=invite_email)
    except User.DoesNotExist:
        return standup.utils.json_response(**standup.utils.USER_DOES_NOT_EXIST)

    invites = models.ChannelInvite.objects.filter(
        user=invite_user, channel=channel
    ).count()
    if invites:
        return standup.utils.json_response(**utils.USER_ALREADY_INVITED)

    # Add user
    try:
        # membership = models.ChannelMember(user=invite_user, channel=channel)
        # membership.save()

        note = notification.models.Notification(
            user=invite_user,
            title="Channel Invite: %s" % channel.name[:16],
            role="INVITE",
            message="You have been invited to channel %s by user %s %s (%s)" % (
                channel.name, user.first_name, user.last_name, user.email
            )
        )
        note.save()
        invite = models.ChannelInvite(
            note=note, user=invite_user, channel=channel
        )
        invite.save()

    except IntegrityError:
        return standup.utils.json_response(
            payload={},
            message="Failed to invite user",
            error="INTERNAL_DB_ERR",
            json_status=500,
            http_status=500
        )

    return standup.utils.json_response(
        payload={"invite_email": invite_user.email},
        message="Invite sent to user"
    )
