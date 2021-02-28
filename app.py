import sys
import importlib
import traceback

from fastapi import FastAPI
from fastapi.responses import PlainTextResponse
from fastapi.middleware.cors import CORSMiddleware

extensions = (
    'teamspeak',
)


class App(FastAPI):
    def load_extension(self, key):
        key = f'ext.{key}'
        spec = importlib.util.find_spec(key)
        lib = importlib.util.module_from_spec(spec)
        sys.modules[key] = lib
        try:
            spec.loader.exec_module(lib)
        except Exception as e:
            del sys.modules[key]
            raise e

        try:
            setup = getattr(lib, 'setup')
        except AttributeError as e:
            del sys.modules[key]
            raise e

        try:
            setup(self)
        except Exception as e:
            del sys.modules[key]
            raise e


app = App()


app.add_middleware(
    CORSMiddleware,
    allow_origins=["apps.derw.xyz"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get('/robots.txt')
def robots_txt():
    return PlainTextResponse('User-agent: *\nDisallow: /')


for ext in extensions:
    try:
        app.load_extension(ext)
    except Exception as e:
        print(f'Failed to load extension {ext}. {e}')
        traceback.print_exc()
