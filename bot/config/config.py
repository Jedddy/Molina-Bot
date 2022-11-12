import json
"""CONFIG FILE"""


async def update_config(server_id, key, value) -> None:
    """Updates config"""

    with open("bot/config/config.json", "r") as config:
        server: dict = json.load(config)
        if not server.get(str(server_id)):
            server[str(server_id)] = {}
        inner = server[str(server_id)]
        inner.update(**{key: value})
        server.update(**{str(server_id): inner})
        with open("bot/config/config.json", "w") as config_:
            json.dump(server, config_)
            return


async def get_config(server_id, key) -> str | int:
    with open("bot/config/config.json", "r") as config:
        dict_: dict = json.load(config)
    server = dict_.get(str(server_id), None)
    if server:
        return server.get(key, None)


