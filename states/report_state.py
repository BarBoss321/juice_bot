from aiogram.fsm.state import StatesGroup, State


class AddReport(StatesGroup):
    company = State()  # NEW: для admin выбор юр.лица
    fruit = State()
    raw = State()
    juice = State()
    waste = State()