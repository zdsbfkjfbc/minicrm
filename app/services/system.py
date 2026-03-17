from app.models import SystemSettings


def get_setting(key: str, default: str = '') -> str:
    setting = SystemSettings.query.filter_by(key=key).first()
    return setting.value if setting else default
