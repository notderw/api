from fastapi import APIRouter

router = APIRouter(
        prefix="/ts",
    )

from . import v1

router.include_router(v1.router)


def setup(app):
    app.include_router(router)

    v1.setup(app)
