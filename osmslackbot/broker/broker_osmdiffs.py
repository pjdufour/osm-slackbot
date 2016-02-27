import json
import re

import defusedxml.ElementTree as et

from geowatchutil.broker.base import GeoWatchBroker
from geowatchutil.codec.geowatch_codec_slack import GeoWatchCodecSlack

from osmslackbot import settings
from osmslackbot.broker.base import OSMSlackBotBroker
from osmslackbot.enumerations import *  # noqa
from osmslackbot.mapping.base import *  # noqa
from osmslackbot.utils import load_patterns


class OSMSlackBotBroker_OSMDiffs(OSMSlackBotBroker):
    """
    Broker for OpenStreetMap Slack bot that processes OSM Diffs
    """
    _user_id = None  # Dervied from consumer authtoken
    _user_name = None  # Dervied from consumer authtoken
    patterns = None
    _ignore_errors = True

    def _pre(self):
        pass

    def _post(self, messages=None):
        for m in messages:
            print m


    def __init__(self, name, description, templates=None, duplex=None, consumers=None, producers=None, stores_out=None, filter_metadata=None, sleep_period=5, count=1, timeout=5, deduplicate=False, ignore_errors=True, verbose=False):  # noqa
        super(OSMSlackBotBroker_OSMDiffs, self).__init__(
            name,
            description,
            duplex=duplex,
            consumers=consumers,
            producers=producers,
            stores_out=stores_out,
            count=count,
            sleep_period=sleep_period,
            timeout=timeout,
            deduplicate=deduplicate,
            filter_metadata=filter_metadata,
            verbose=verbose)

        self.templates = templates  # loaded from templates.yml
        self._ignore_errors = ignore_errors
        self._user_id = self.producers[0]._client._user_id
        self._user_name = self.producers[0]._client._user_name

        self.codec_slack = GeoWatchCodecSlack()

        self.patterns = load_patterns()