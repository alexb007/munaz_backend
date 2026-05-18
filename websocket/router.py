from channels.layers import get_channel_layer

async def route_db_event(payload: dict):
    channel_layer = get_channel_layer()

    await channel_layer.group_send(
        f"realtime_{payload['table']}",
        {
            "type": "db.event",
            "payload": payload,
        }
    )
