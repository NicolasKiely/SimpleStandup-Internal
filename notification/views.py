import base64
from django.contrib.auth.models import User
import hashlib

import channel.models
import standup.utils
from notification import models


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
            "id": note.pk,
            "timestamp": note.dt_created,
            "message": note.message,
            "role": note.role,
            "title": note.title
        }
        for note in user.notification_set.filter(dismissed=False)[:25]
    ]
    pks = sorted([note["id"] for note in notifications])
    pk_hash = base64.b64encode(
        hashlib.md5(",".join(str(pk) for pk in pks).encode("utf8")).digest()
    ).decode()

    return standup.utils.json_response(
        payload={"notifications": notifications, "hash": pk_hash}
    )


def handle_notification_response(request):
    """ POST hander for user's response to a notification """
    bad_secret, response, args = standup.utils.check_request_secret(request)
    if bad_secret:
        return response

    note_id = args.get("notification_id", "")
    try:
        user_email = request.headers.get("X-USER-EMAIL")
        user = User.objects.get(email__iexact=user_email)
    except User.DoesNotExist:
        return standup.utils.json_response(**standup.utils.USER_DOES_NOT_EXIST)

    # Fetch notification
    try:
        note: models.Notification = models.Notification.objects.filter(
            user=user, pk=note_id
        ).get()
    except models.Notification.DoesNotExist:
        return standup.utils.json_response(
            **standup.utils.NOTIFICATION_DOES_NOT_EXIST
        )

    if "dismissed" in args:
        # Handle argument to dismiss notification
        try:
            note.dismissed = standup.utils.parse_bool(args["dismissed"])
        except ValueError:
            return standup.utils.json_response(
                error="INVALID_ARG",
                message="Bad value for dismissed",
                json_status=400,
                http_status=400
            )

    if "invite" in args:
        # Handle argument to accept invitation
        linvite = args["invite"].lower()
        try:
            channel_invite = note.channelinvite
            if linvite == "accept":
                membership = channel.models.ChannelMember(
                    user=user, channel=channel_invite.channel
                )
                membership.save()
                channel_invite.delete()
            elif linvite != "decline":
                return standup.utils.json_response(
                    error="INVALID_ARG",
                    message="Bad value for invite",
                    json_status=400,
                    http_status=400
                )

        except channel.models.ChannelInvite.DoesNotExist:
            pass

    print("Notification: %s" % note_id)
    note.save()
    return standup.utils.json_response(payload={})
