from typing import List

from django.contrib.auth.models import User

from channel import models


def get_channel_members(channel: models.Channel) -> List[User]:
    """ Returns list of members under a channel """
    owner = channel.owner
    return [owner]
