DEBUG = False

GEOWATCH_STOPWORDS = [
    "nobot",
    "no bot",
    "stopbot",
    "stop bot",
    "ignorebot",
    "ignore bot",
    "skipbot",
    "skip bot",
    "!bot",
    "-bot"
]

MONGODB_HOST = 'localhost'
MONGODB_PORT = 27017
MONGODB_DB = 'geowatch'

MONGODB_COLLECTION_WATCHLIST = 'geowatch-watchlist'

try:
    from local_settings import *  # noqa
except ImportError:
    pass
