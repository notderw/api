# This is basically just a repeater for the twitch webhooks

from fastapi import APIRouter

router = APIRouter(
        prefix="/twitch-archive",
    )

from . import v1

router.include_router(v1.router)


def setup(app):
    app.include_router(router)

    v1.setup(app)
