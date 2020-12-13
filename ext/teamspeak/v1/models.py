from typing import List
from datetime import datetime, timedelta

from pydantic import BaseModel

class Client(BaseModel):
    id: int
    nickname: str
    input_hardware: bool
    output_hardware: bool
    input_muted: bool
    output_muted: bool
    lastconnected: datetime
    idle_time: timedelta
    away: bool
    away_message: str

    class Config:
        allow_population_by_field_name = True
        @classmethod
        def alias_generator(cls, string: str) -> str:
            if string == 'id': return 'clid'
            return f'client_{string}'

class Channel(BaseModel):
    id: int
    name: str
    order: int
    clients: List[Client]

    class Config:
        allow_population_by_field_name = True
        @classmethod
        def alias_generator(cls, string: str) -> str:
            if string == 'id': return 'cid'
            return f'channel_{string}'

class Server(BaseModel):
    name: str
    channels: List[Channel]

    class Config:
        allow_population_by_field_name = True
        alias_generator = lambda string: f'virtualserver_{string}'
