from sqlalchemy.orm import Session

from .. import models


def get_setting(db: Session, key: str):
    row = db.get(models.AppSetting, key)
    return row.value if row else None


def set_setting(db: Session, key: str, value: str) -> None:
    row = db.get(models.AppSetting, key)
    if row:
        row.value = value
    else:
        db.add(models.AppSetting(key=key, value=value))
    db.commit()
