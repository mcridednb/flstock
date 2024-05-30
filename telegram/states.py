from aiogram.fsm.state import StatesGroup, State


class Registration(StatesGroup):
    source = State()
    category = State()
    subcategory = State()


class Profile(StatesGroup):
    source = State()
    category = State()
    subcategory = State()
    name = State()
    skills = State()
    summary = State()
    experience = State()
    hourly_rate = State()
    stop_words = State()
    keywords = State()
