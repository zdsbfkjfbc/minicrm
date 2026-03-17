from datetime import datetime, timezone


def sanitize_for_spreadsheet(value):
    if not isinstance(value, str):
        return value
    stripped = value.lstrip()
    if stripped.startswith(('=', '+', '-', '@')):
        return f"'{value}"
    return value


def sanitize_html(text):
    if not text:
        return text
    import re

    clean = re.compile('<.*?>')
    return re.sub(clean, '', text)


def format_datetime_brt(dt: datetime, fmt: str = '%d/%m/%Y %H:%M'):
    if not dt:
        return ''
    from datetime import timezone as dt_timezone, timedelta

    BRT = dt_timezone(timedelta(hours=-3))
    dt_brt = dt.replace(tzinfo=timezone.utc).astimezone(BRT)
    return dt_brt.strftime(fmt)
