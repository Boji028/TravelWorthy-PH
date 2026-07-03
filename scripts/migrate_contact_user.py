import sqlalchemy as sa
from app import create_app, db

app = create_app()

with app.app_context():
    inspector = sa.inspect(db.engine)
    existing_cols = [c["name"] for c in inspector.get_columns("contact_messages")]

    if "user_id" not in existing_cols:
        with db.engine.connect() as conn:
            conn.execute(sa.text("ALTER TABLE contact_messages ADD COLUMN user_id INTEGER REFERENCES users(id)"))
            conn.commit()
        print("✅ Migration complete: user_id column added.")
    else:
        print("ℹ️ Column already exists — nothing to do.")
