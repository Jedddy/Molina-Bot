from typing import Any
import json
"""CONFIG FILE"""


async def update_config(server_id, key, value, inner=False, inner_key=None) -> None:
    """Updates config"""

    with open("bot/config/config.json", "r") as config:
        server: dict = json.load(config)
        # Get server from config
        if not server.get(str(server_id)):
            server[str(server_id)] = {}
        server_cfg = server[str(server_id)]
        if not inner:
            server_cfg.update({key: value})
        else:
            if not server_cfg.get(key, None):
                server_cfg[key] = {}
            inner_cfg = server_cfg[key]
            inner_cfg.update({inner_key: value})
        server.update({str(server_id): server_cfg})
        with open("bot/config/config.json", "w") as config_:
            json.dump(server, config_)
            return


async def get_config(server_id, key) -> Any:
    with open("bot/config/config.json", "r") as config:
        dict_: dict = json.load(config)
    server = dict_.get(str(server_id), None)
    if server:
        return server.get(key, None)


async def delete_config(server_id, key, inner_key=None) -> None:
    with open("bot/config/config.json", "r") as config:
        server: dict = json.load(config)
        temp = server.get(str(server_id), None)
        if temp:
            if not inner_key:
                temp.pop(key)
                server.update({str(server_id): temp})
            else:
                inner = temp.get(key, None)
                if not inner:
                    return
                inner.pop(inner_key)
                server.update({str(server_id): temp})
        with open("bot/config/config.json", "w") as config_:
            json.dump(server, config_)
            return
