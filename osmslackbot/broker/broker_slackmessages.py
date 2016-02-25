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


class OSMSlackBotBroker_SlackMessages(OSMSlackBotBroker):
    """
    Broker for OpenStreetMap Slack bot that processes Slack Messages
    """
    _user_id = None  # Dervied from consumer authtoken
    _user_name = None  # Dervied from consumer authtoken
    patterns = None
    _ignore_errors = True

    def _pre(self):
        pass

    def _post(self, messages=None):
        for m in messages:
            msgtype = m[u'type']
            if msgtype == u'hello':  # slack always open up connection with hello message
                pass
            elif msgtype == u'message':
                msgsubtype = m.get(u'subtype', None)
                if msgsubtype == u'bot_message':
                    # username = m[u'username']
                    # text = m[u'text']
                    pass
                elif msgsubtype == u'message_deleted':
                    pass
                else:
                    # user = m[u'user']
                    text = m[u'text']
                    channel = m[u'channel']

                    stop = False
                    for stopword in settings.GEOWATCH_STOPWORDS:
                        if stopword in text:
                            stop = True
                            break

                    if stop:
                        continue

                    match_question = None
                    match_value = None
                    for question in self.patterns:
                        for pattern in self.patterns[question]:
                            match_value = re.search(pattern, text, re.M | re.I)
                            if match_value:
                                match_question = question
                                break
                        if match_value:
                            break

                    if match_value:
                        outgoing = None
                        print "Match Question: ", match_question
                        print "Match Value: ", match_value
                        try:
                            if match_question == "project":
                                ctx = self._request_project(match_value.group("project"), URL_PROJECT_TASKS)
                                t = self.templates.get('SLACK_MESSAGE_TEMPLATE_PROJECT', None)
                                if t:
                                    outgoing = self.codec_slack.render(ctx, t=t)
                            elif match_question == "changeset":
                                ctx = self._request_changeset(match_value.group("changeset"), URL_CHANGESET_API)
                                t = self.templates.get('SLACK_MESSAGE_TEMPLATE_CHANGESET', None)
                                if t:
                                    outgoing = self.codec_slack.render(ctx, t=t)
                            elif match_question == "node":
                                ctx = self._request_node(match_value.group("node"), URL_NODE_API)
                                t = self.templates.get('SLACK_MESSAGE_TEMPLATE_NODE', None)
                                if t:
                                    outgoing = self.codec_slack.render(ctx, t=t)
                            elif match_question == "way":
                                ctx = self._request_way(match_value.group("way"), URL_WAY_API)
                                t = self.templates.get('SLACK_MESSAGE_TEMPLATE_WAY', None)
                                if t:
                                    outgoing = self.codec_slack.render(ctx, t=t)
                            elif match_question == "relation":
                                ctx = self._request_relation(match_value.group("relation"), URL_RELATION_API)
                                t = self.templates.get('SLACK_MESSAGE_TEMPLATE_RELATION', None)
                                if t:
                                    outgoing = self.codec_slack.render(ctx, t=t)
                        except:
                            print "Error processing match for original text: ", text
                            if not self._ignore_errors:
                                raise

                        if outgoing:
                            print "Sending message ..."
                            print "+ Data = ", outgoing
                            self.duplex[0]._channel.send_message(outgoing, topic=channel)


    def __init__(self, name, description, templates=None, duplex=None, consumers=None, producers=None, stores_out=None, filter_metadata=None, sleep_period=5, count=1, timeout=5, deduplicate=False, ignore_errors=True, verbose=False):  # noqa
        super(OSMSlackBotBroker_SlackMessages, self).__init__(
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
        self._user_id = self.duplex[0]._client._user_id
        self._user_name = self.duplex[0]._client._user_name

        self.codec_slack = GeoWatchCodecSlack()

        self.patterns = load_patterns()
