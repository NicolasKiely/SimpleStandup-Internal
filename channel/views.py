from django.contrib.auth.models import User
from django.db import IntegrityError
import datetime as dtt

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


def message_channel(request):
    """ POST handler for posting messages to a channel

    POST Parameters:
        - dt_posted: Target date of message
        - channel_id: ID of channel to post to
        - message: Message text
    """
    bad_secret, response, args = standup.utils.check_request_secret(request)
    if bad_secret:
        return response

    # Fetch arguments
    user_email = request.headers.get("X-USER-EMAIL").lower()
    err = standup.utils.assert_required_args(
        args, "dt_posted", "channel_id", "message"
    )
    if err:
        return err
    posted = args.get("dt_posted")
    channel_id = args.get("channel_id")
    message = args.get("message")

    try:
        dt_posted = dtt.date.fromisoformat(posted)
    except ValueError:
        return standup.utils.json_response(
            error="INVALID_ARG",
            message="Bad value for dt_posted, must be ISO",
            json_status=400,
            http_status=400
        )

    try:
        user = User.objects.get(email__iexact=user_email)
    except User.DoesNotExist:
        return standup.utils.json_response(**standup.utils.USER_DOES_NOT_EXIST)

    err_response, channel, members = utils.get_channel_by_member(
        user_email, channel_id
    )
    if err_response:
        return err_response

    # Check to see if message already exists
    channel_message = models.ChannelMessage.objects.filter(
        user=user, dt_posted=dt_posted, channel_id=channel_id
    ).first()
    if channel_message is None:
        channel_message = models.ChannelMessage(
            user=user, dt_posted=dt_posted, channel_id=channel_id
        )
    channel_message.message = message

    try:
        channel_message.save()
    except IntegrityError:
        return standup.utils.json_response(
            payload={},
            message="Failed to post message",
            error="INTERNAL_DB_ERR",
            json_status=500,
            http_status=500
        )

    return standup.utils.json_response(
        payload={"message_id": channel_message.pk},
        message="Saved message"
    )


def list_logs(request):
    """ Endpoint to handle request to list logs """
    bad_secret, response, args = standup.utils.check_request_secret(request)
    if bad_secret:
        return response

    user_email = request.headers.get("X-USER-EMAIL").lower()
    err = standup.utils.assert_required_args(
        args, "dt_start", "dt_end", "channel_id",
    )
    if err:
        return err

    channel_id = args["channel_id"]

    # Get channel
    err_response, channel, members = utils.get_channel_by_member(
        user_email, channel_id
    )
    if err_response:
        return err_response

    # Get date range
    try:
        dt_start = dtt.date.fromisoformat(args["dt_start"])
    except ValueError:
        return standup.utils.json_response(
            error="INVALID ARG",
            message="Invalid ISO date for start date, must be YYYY-MM-DD",
            json_status=400,
            http_status=400
        )

    try:
        dt_end = dtt.date.fromisoformat(args["dt_end"])
    except ValueError:
        return standup.utils.json_response(
            error="INVALID ARG",
            message="Invalid ISO date for end date, must be YYYY-MM-DD",
            json_status=400,
            http_status=400
        )

    if dt_start > dt_end:
        # Swap date range if reversed
        dt_start, dt_end = dt_end, dt_end

    dt_delta = (dt_end - dt_start).days
    if dt_delta > 31:
        return standup.utils.json_response(
            error="INVALID RANGE",
            message="Date range too large",
            json_status=400,
            http_status=400
        )

    # Get sorted list of dates
    dt_range = [
        {"date": dt_start + dtt.timedelta(i), "messages": []}
        for i in range(dt_delta+1)
    ]

    return standup.utils.json_response(
        payload={"logs": dt_range}
    )
