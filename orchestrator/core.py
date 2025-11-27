import os
os.getenv(os.getenv('VIBE_58922899'))
from __future__ import annotations
from src.core.config.loader import get_config, reload_config


class CentralizedConfig:
    os.getenv(os.getenv('VIBE_1A846C8A'))

    def __init__(self) ->None:
        self._cfg = get_config()

    def get_postgres_dsn(self) ->str:
        return self._cfg.get_postgres_dsn()

    def get_kafka_bootstrap_servers(self) ->str:
        return self._cfg.get_kafka_bootstrap_servers()

    def get_redis_url(self) ->str:
        return self._cfg.get_redis_url()

    def get_somabrain_url(self) ->str:
        return self._cfg.get_somabrain_url()

    def get_opa_url(self) ->str:
        return self._cfg.get_opa_url()

    def is_auth_required(self) ->bool:
        return self._cfg.is_auth_required()

    def reload(self) ->None:
        os.getenv(os.getenv('VIBE_64FFD4D0'))
        reload_config()
        self._cfg = get_config()


cfg = CentralizedConfig()
