from sqlalchemy.orm import Session
from app.models import SaveTable


# Получение всех записей истории для конкретного пользователя
def get_all_history(user_id: str, db: Session):
    if not user_id:
        return {"success": True, "items": []}
    records = db.query(SaveTable).filter(SaveTable.UUID == user_id).order_by(SaveTable.CreateData.desc()).all()
    items = [r.to_dict() for r in records]
    return {"success": True, "items": items}

# Удаление всей истории по идентификатору пользователя
def delete_all_history(user_id: str, db: Session):
    db.query(SaveTable).filter(SaveTable.UUID == user_id).delete()
    db.commit()
    return {"success": True}

# Удаление одной записи истории по номеру записи и идентификатору пользователя
def delete_one_history(record_id: int, user_id: str, db: Session):
    if not user_id:
        return {"success": False}

    record = (
        db.query(SaveTable)
        .filter(
            SaveTable.id == record_id,
            SaveTable.UUID == user_id 
        )
        .first()
    )

    if not record:
        return {"success": False}

    db.delete(record)
    db.commit()
    return {"success": True}

# Добавление новой записи истории 
def add_history_record(UUID: str, TextBefore: str, TextAfter: str, Compression: str, db: Session):
    record = SaveTable(
        UUID=UUID,
        TextBefore=TextBefore,
        TextAfter=TextAfter,
        Compression=Compression
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return record