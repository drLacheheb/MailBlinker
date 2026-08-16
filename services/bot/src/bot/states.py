from aiogram.fsm.state import State, StatesGroup


class FormatEmailStates(StatesGroup):
    waiting_for_title = State()
    waiting_for_email = State()
    waiting_for_body = State()
