from aiogram.fsm.state import StatesGroup, State


class Registration(StatesGroup):
    source = State()
    category = State()
    subcategory = State()


class Profile(StatesGroup):
    name = State()
    skills = State()
    summary = State()
    experience = State()
    hourly_rate = State()


class Notifications(StatesGroup):
    source = State()
    category = State()
    subcategory = State()
    keywords = State()
    stop_words = State()


class GPT(StatesGroup):
    start_response = State()
    start_analyze = State()
