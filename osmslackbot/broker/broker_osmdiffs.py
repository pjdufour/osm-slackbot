import json
import re
import yaml

import defusedxml.ElementTree as et

from jinja2 import Environment, PackageLoader
from pymongo import MongoClient

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
    env = None  # Jinja2 Environment
    _user_id = None  # Dervied from consumer authtoken
    _user_name = None  # Dervied from consumer authtoken
    osm_tags = None
    patterns = None
    _ignore_errors = True

    def _pre(self):
        pass

    def _post(self, messages=None):
        osm_tags_set = set(self.osm_tags)

        client = MongoClient(settings.MONGODB_HOST, settings.MONGODB_PORT)
        db = client[settings.MONGODB_DB]
        collection = db[settings.MONGODB_COLLECTION_WATCHLIST]
        watchlist = collection.find()

        outgoing_messages = []

        for m in messages:
            for action in m.findall('action'):
                if action.get('type') == "create":
                    for node in action.findall('node'):
                        nodeID = node.get('id')
                        tags = [(tag.get('k') + "=" + tag.get('v','')) for tag in node.findall('tag')]
                        if len(tags) > 0:
                            print node.get('user'), ': ', tags
                        if len(osm_tags_set & set(tags)) > 0:
                            ctx = self._flatten_node(nodeID, node)
                            t = self.env.get_template("response/node/created.yml")
                            outgoing_messages.append(yaml.load(t.render(** ctx)))
                            #t = self.templates.get('SLACK_MESSAGE_TEMPLATE_NODE', None)
                            #if t:
                            #    outgoing_messages.append(self.codec_slack.render(ctx, t=t))

                    for way in action.findall('way'):
                        wayID = way.get('id')
                        tags = [(tag.get('k') + "=" + tag.get('v','')) for tag in way.findall('tag')]
                        if len(tags) > 0:
                            print way.get('user'), ': ', tags
                        if len(osm_tags_set & set(tags)) > 0:
                            ctx = self._flatten_way(wayID, way)
                            t = self.env.get_template("response/way/created.yml")
                            outgoing_messages.append(yaml.load(t.render(** ctx)))
                            #t = self.templates.get('SLACK_MESSAGE_TEMPLATE_WAY', None)
                            #if t:
                            #    outgoing_messages.append(self.codec_slack.render(ctx, t=t))

                    for relation in action.findall('relation'):
                        relationID = relation.get('id')
                        tags = [(tag.get('k') + "=" + tag.get('v','')) for tag in relation.findall('tag')]
                        if len(tags) > 0:
                            print relation.get('user'), ': ', tags
                        if len(osm_tags_set & set(tags)) > 0:
                            ctx = self._flatten_relation(relationID, relation)
                            t = self.templates.get('SLACK_MESSAGE_TEMPLATE_RELATION', None)
                            if t:
                                outgoing_messages.append(self.codec_slack.render(ctx, t=t))

        if outgoing_messages:
            for outgoing in outgoing_messages:
                print "Sending message ..."
                print "+ Data = ", outgoing
                #self.producers[0]._channel.send_message(outgoing, topic='#test')
                self.producers[0]._channel.send_message(outgoing)

    def __init__(
        self,
        name,
        description,
        osm_tags=None,
        templates=None,
        duplex=None,
        consumers=None,
        producers=None,
        stores_out=None,
        filter_metadata=None,
        sleep_period=5,
        count=1,
        timeout=5,
        deduplicate=False,
        ignore_errors=True,
        verbose=False):  # noqa
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
        self.osm_tags = osm_tags
        self._user_id = self.producers[0]._client._user_id
        self._user_name = self.producers[0]._client._user_name

        self.codec_slack = GeoWatchCodecSlack()

        self.patterns = load_patterns()

        self.env = Environment(loader=PackageLoader('osmslackbot', 'templates'))
