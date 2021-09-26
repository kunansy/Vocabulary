import os

from environs import Env


env = Env()

SYNONYMS_SEARCH_URL = 'https://rusvectores.org/tayga_upos_skipgram_300_2_2019/' \
                      '{word}/api/json/'
CORPUS_EXAMPLES_MARKER = lambda ex: f"<b>{ex.upper()}</b>"

with env.prefixed('API_'):
    API_VERSION = env('VERSION', '0.1.0')
    API_HOST = env('HOST')
    API_PORT = env.int('PORT')
    API_DEBUG = env.bool('DEBUG', False)

with env.prefixed('LOGGER_'):
    LOGGER_NAME = env('NAME', 'Vocabulary')
    LOGGER_LEVEL = env.log_level('LEVEL', 'debug')

with env.prefixed('DB_'):
    DB_DSN_TEMPLATE = "postgresql+{driver}://{username}:{password}@" \
                      "{host}:{port}/{name}"

    DB_HOST = env('HOST')
    DB_PORT = env.int('PORT')
    DB_USERNAME = env('USERNAME')
    DB_PASSWORD = env('PASSWORD')
    DB_NAME = env('NAME')
    DB_ISOLATION_LEVEL = env('ISOLATION_LEVEL', 'REPEATABLE READ')

os.environ.clear()
