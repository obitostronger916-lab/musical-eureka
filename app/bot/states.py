from aiogram.fsm.state import State, StatesGroup


class MusicSearch(StatesGroup):
    waiting_for_query = State()
    waiting_for_lyrics = State()
