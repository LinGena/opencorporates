from environs import Env
from dataclasses import dataclass

@dataclass
class Db:
    db_user: str
    db_password: str
    db_database: str
    db_host: str
    db_port: int
    table_companies:str
    table_cookies:str

@dataclass
class Sets:
    driver_version: int
    count_thred: int
    debug: bool

@dataclass
class Logs:
    level: str
    dir: str
    format: str
    separate_log_without_rollover: bool

@dataclass
class Capsolver:
    token: str

@dataclass
class BasePath:
    dir: str

@dataclass
class Settings:
    db: Db
    logs: Logs
    capsolver: Capsolver
    base_path: BasePath
    sets: Sets

def get_settings(path: str):
    env = Env()
    env.read_env(path, override=True)

    return Settings(
        db=Db(
            db_user=env.str('DB_USER'),
            db_password=env.str('DB_PASSWORD'),
            db_database=env.str('DB_DATABASE'),
            db_host=env.str('DB_HOST'),
            db_port=env.int('DB_PORT'),
            table_companies='companies',
            table_cookies='cookies'
        ),
        logs=Logs(
            level=env.str('LOGS_LEVEL'),
            dir=env.str('LOGS_DIR'),
            format=env.str('LOGS_FORMAT'),
            separate_log_without_rollover=env.str('LOGS_ROLLOVER')
        ),
        capsolver=Capsolver(
            token=env.str('CAPSOLVER_TOKEN')
        ),
        base_path=BasePath(
            dir=env.str('PRODUCTION_DIR')
        ),
        sets=Sets(
            driver_version=env.int('DRIVER_VERSION'),
            count_thred=env.int('COUNT_THREADS'),
            debug=env.bool('DEBUG')
        )
    )

settings = get_settings('.env')
