TOLERANCE = 5  # допустимая погрешность


def calculate_percent(raw: float, waste: float) -> float:
    if raw == 0:
        return 0.0

    return round((waste / raw) * 100, 2)