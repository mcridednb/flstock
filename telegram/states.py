from aiogram.fsm.state import StatesGroup, State


class Registration(StatesGroup):
    category = State()
    subcategory = State()


class Profile(StatesGroup):
    category = State()
    subcategory = State()
    name = State()
    skills = State()
    summary = State()
    experience = State()
    hourly_rate = State()
    stop_words = State()
