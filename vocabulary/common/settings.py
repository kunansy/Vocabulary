from environs import Env


env = Env()

API_VERSION = env('VERSION', '0.1.0')

with env.prefixed('LOGGER_'):
    LOGGER_NAME = env('NAME', 'Vocabulary')
    LOGGER_LEVEL = env.log_level('LEVEL', 'debug')

with env.prefixed('DB_'):
    DB_DSN_TEMPLATE = "postgresq+asyncpg://{username}:{password}@" \
                      "{host}:{port}/{name}"

    DB_HOST = env('HOST', '127.0.0.1')
    DB_PORT = env.int('PORT', 5432)
    DB_USERNAME = env('USERNAME', 'docker')
    DB_PASSWORD = env('PASSWORD', 'docker')
    DB_NAME = env('NAME', 'vocabulary')
    DB_ISOLATION_LEVEL = env('ISOLATION_LEVEL', 'REPEATABLE READ')


