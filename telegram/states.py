from aiogram.fsm.state import StatesGroup, State


class Profile(StatesGroup):
    category = State()
    name = State()
    skills = State()
    summary = State()
    experience = State()
    hourly_rate = State()
