"""Регистрирует БД находок (aziral_core) как источник данных Superset.

Запускается внутри контейнера Superset (имеет доступ к его app-контексту).
Идемпотентно: если соединение с таким именем уже есть — ничего не делает.
"""
import os

from superset.app import create_app

DB_NAME = "Aziral Findings"

app = create_app()
with app.app_context():
    from superset import db
    from superset.models.core import Database

    uri = os.environ.get(
        "AZIRAL_FINDINGS_URI",
        f"postgresql+psycopg2://{os.environ['POSTGRES_USER']}:{os.environ['POSTGRES_PASSWORD']}"
        f"@postgres:5432/aziral_core",
    )
    existing = db.session.query(Database).filter_by(database_name=DB_NAME).first()
    if existing:
        print(f"[register_db] '{DB_NAME}' уже зарегистрирована — пропуск")
    else:
        database = Database(database_name=DB_NAME)
        database.set_sqlalchemy_uri(uri)
        db.session.add(database)
        db.session.commit()
        print(f"[register_db] '{DB_NAME}' добавлена")
