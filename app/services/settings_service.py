import json

from sqlalchemy.orm import Session

from .. import models

DEFAULT_HOUSEHOLD_MEMBERS = ["Person 1", "Person 2", "Person 3", "Person 4"]


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


def get_household_members(db: Session):
    raw = get_setting(db, "household_members")
    if not raw:
        return list(DEFAULT_HOUSEHOLD_MEMBERS)
    try:
        names = json.loads(raw)
    except (TypeError, ValueError):
        return list(DEFAULT_HOUSEHOLD_MEMBERS)
    names = [n.strip() for n in names if n and n.strip()]
    while len(names) < 4:
        names.append(DEFAULT_HOUSEHOLD_MEMBERS[len(names)])
    return names[:4]


def set_household_members(db: Session, names: list[str]) -> None:
    cleaned = []
    for i, n in enumerate(names[:4]):
        n = (n or "").strip()
        cleaned.append(n or DEFAULT_HOUSEHOLD_MEMBERS[i])
    set_setting(db, "household_members", json.dumps(cleaned))
