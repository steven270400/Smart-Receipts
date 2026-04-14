from datetime import datetime

DATETIME_FMT = "%Y-%m-%d %H:%M:%S"
DATE_FMT = "%Y-%m-%d"


def parse_datetime(value: str | datetime) -> datetime:
    if isinstance(value, datetime):
        return value

    text = str(value).strip()
    for fmt in (DATETIME_FMT, DATE_FMT):
        try:
            parsed = datetime.strptime(text, fmt)
            if fmt == DATE_FMT:
                return datetime(parsed.year, parsed.month, parsed.day, 0, 0, 0)
            return parsed
        except ValueError:
            continue
    raise ValueError("??????,?? YYYY-MM-DD ? YYYY-MM-DD HH:mm:ss")


def format_datetime(value: datetime | None) -> str | None:
    if value is None:
        return None
    if isinstance(value, datetime):
        return value.strftime(DATETIME_FMT)
    return None
