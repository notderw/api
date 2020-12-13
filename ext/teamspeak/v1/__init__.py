import os
from typing import Tuple
from functools import wraps
from datetime import datetime, timedelta

from ipaddress import ip_address

from fastapi import APIRouter
from fastapi.responses import PlainTextResponse

from ratelimit import RateLimitMiddleware, Rule
from ratelimit.auths import EmptyInformation
from ratelimit.backends.redis import RedisBackend
from ratelimit.auths.ip import client_ip

import ts3

from .models import Server, Channel, Client


TS3_URI = os.environ.get('TS3_URI')


def cache(expires_after=60):
    def decorator(func):
        class InternalCache():
            val = None
            expires_at = datetime.utcfromtimestamp(0)

        _ = InternalCache()

        @wraps(func)
        def wrapper(*args, **kwargs):
            if datetime.utcnow() > _.expires_at:
                _.val = func(*args, **kwargs)
                _.expires_at = datetime.utcnow() + timedelta(seconds=expires_after)

            return _.val

        return wrapper
    return decorator


@cache()
def build() -> Server:
    with ts3.query.TS3ServerConnection(TS3_URI) as ts:
        ts.exec_("use", sid=1, virtual=True)

        serverinfo = ts.query("serverinfo").first()
        channellist = ts.query("channellist").all()
        clientlist = ts.query("clientlist").options("away", "voice", "times", "info").all()

        return Server(
            **serverinfo,
            channels = [Channel(
                **channel,
                clients = [Client(
                        **client
                    ) for client in clientlist if client["cid"] == channel['cid'] and not client['client_type'] == '1']
                ) for channel in  channellist]
            )


router = APIRouter(prefix="/v1")

@router.get('/list')
def list():
    return build().dict(by_alias=False)

@router.get('/rainmeter', response_class=PlainTextResponse)
def rainmeter():
    server = build()

    text = f'<head>{server.name}</head>\n'
    text += '<list>\n'

    for channel in server.channels:
        for client in channel.clients:
            text += f'{client.nickname} '

            if client.away:
                if client.away_message:
                    text += f'[Away {client.away_message}]'
                else:
                    text += '[Away]'

            if client.output_muted:
                text += '[Muted]'
            elif client.input_muted:
                text += '[Mic Muted]'

            text += '\n'

    text += '</list>'

    return text


async def ratelimit(scope) -> Tuple[str, str]:
    try:
        return await client_ip(scope)

    except EmptyInformation:
        ip, port = tuple(scope["client"])
        if not ip_address(ip).is_global:
            return ip, 'default'

async def handle_429(scope, receive, send) -> None:
    await send({"type": "http.response.start", "status": 429})
    await send({"type": "http.response.body", "body": b"You are being rate limited", "more_body": False})


def setup(app):
    app.add_middleware(
        RateLimitMiddleware,
        authenticate=ratelimit,
        backend=RedisBackend(host="redis"),
        config={
            r'^/ts/v1/rainmeter': [Rule(minute=2, block_time=60)]
        },
        on_blocked=handle_429
    )
