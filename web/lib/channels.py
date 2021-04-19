from asgiref.sync import async_to_sync, sync_to_async
from channels.layers import get_channel_layer
from channels.db import database_sync_to_async
import json
import time
from django.dispatch import receiver

from . import cache

CHANNEL_CONSIDERED_ALIVE_IF_TOUCHED_IN_SECS = 1200


def octo_group_name(printer_id):
    return 'p_octo.{}'.format(printer_id)


def web_group_name(printer_id):
    return 'p_web.{}'.format(printer_id)


def janus_web_group_name(printer_id):
    return 'janus_web.{}'.format(printer_id)


def octoprinttunnel_group_name(printer_id):
    return 'octoprinttunnel.{}'.format(printer_id)


async def async_send_msg_to_printer(printer_id, msg_dict, to_channel=None):
    msg_dict.update({
        'type': 'printer.message',  # mapped to -> printer_message in consumer
    })
    layer = get_channel_layer()

    if to_channel is not None:
        await layer.send(
            to_channel,
            msg_dict,
        )
    else:
        await layer.group_send(
            octo_group_name(printer_id),
            msg_dict,
        )


send_msg_to_printer = async_to_sync(async_send_msg_to_printer)


async def async_send_message_to_web(printer_id, msg_dict):
    msg_dict.update({'type': 'web.message'})    # mapped to -> web_message in consumer
    layer = get_channel_layer()
    await layer.group_send(
        web_group_name(printer_id),
        msg_dict,
    )


send_msg_to_web = async_to_sync(async_send_message_to_web)


async def async_send_status_to_web(printer_id):
    layer = get_channel_layer()
    await layer.group_send(
        web_group_name(printer_id),
        {
            'type': 'printer.status',         # mapped to -> printer_status in consumer
        }
    )


send_status_to_web = async_to_sync(async_send_status_to_web)


async def async_send_janus_to_web(printer_id, msg):
    layer = get_channel_layer()
    await layer.group_send(
        janus_web_group_name(printer_id),
        {
            'type': 'janus.message',         # mapped to -> janus_message in consumer
            'msg': msg,
        }
    )

send_janus_to_web = async_to_sync(async_send_janus_to_web)


async def async_send_message_to_octoprinttunnel(group_name, data):
    msg_dict = {
        # mapped to -> octoprinttunnel_message in consumer
        'type': 'octoprinttunnel.message',
        'data': data
    }
    layer = get_channel_layer()
    await layer.group_send(
        group_name,
        msg_dict,
    )


send_message_to_octoprinttunnel = async_to_sync(async_send_message_to_octoprinttunnel)


async def async_broadcast_ws_connection_change(group_name):
    (group, printer_id) = group_name.split('.')
    if group == 'p_web':
        await async_send_viewing_status(
            printer_id,
            await async_get_num_ws_connections(group_name))
    if group == 'p_octo':
        if await async_get_num_ws_connections(group_name) <= 0:
            await sync_to_async(cache.printer_status_delete)(printer_id)
        await async_send_status_to_web(printer_id)


broadcast_ws_connection_change = async_to_sync(async_broadcast_ws_connection_change)


async def async_send_viewing_status(printer_id, viewing_count=None, to_channel=None):
    if viewing_count is None:
        viewing_count = await async_get_num_ws_connections(web_group_name(printer_id))

    await async_send_msg_to_printer(
        printer_id,
        {'remote_status': {'viewing': viewing_count > 0}},
        to_channel=to_channel,
    )

send_viewing_status = async_to_sync(async_send_viewing_status)


async def async_send_should_watch_status(printer, to_channel=None):
    await async_send_msg_to_printer(
        printer.id,
        {'remote_status': {'should_watch': await database_sync_to_async(printer.should_watch)()}},
        to_channel=to_channel,
    )


send_should_watch_status = async_to_sync(async_send_should_watch_status)


async def async_get_num_ws_connections(group_name, threshold=None, current_time=None):
    threshold = threshold if threshold is not None else CHANNEL_CONSIDERED_ALIVE_IF_TOUCHED_IN_SECS
    current_time = time.time() if current_time is None else current_time
    chlayer = get_channel_layer()
    async with chlayer.connection(chlayer.consistent_hash(group_name)) as conn:
        return await conn.zcount(
            chlayer._group_key(group_name),
            min=current_time - threshold)

get_num_ws_connections = async_to_sync(async_get_num_ws_connections)


async def async_touch_channel(group_name, channel_name):
    chlayer = get_channel_layer()
    # group_add adds or updates existing channel in a redis sorted set,
    # and sets current time as score.. just what we need
    await chlayer.group_add(group_name, channel_name)

touch_channel = async_to_sync(async_touch_channel)
