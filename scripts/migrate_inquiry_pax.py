import sqlalchemy as sa
from app import create_app, db

app = create_app()

with app.app_context():
    inspector = sa.inspect(db.engine)
    existing_cols = [c['name'] for c in inspector.get_columns('inquiries')]

    with db.engine.connect() as conn:
        if 'num_adults' not in existing_cols:
            conn.execute(sa.text('ALTER TABLE inquiries ADD COLUMN num_adults INTEGER NOT NULL DEFAULT 1'))
            print("✅ num_adults added.")
        if 'num_children' not in existing_cols:
            conn.execute(sa.text('ALTER TABLE inquiries ADD COLUMN num_children INTEGER NOT NULL DEFAULT 0'))
            print("✅ num_children added.")
        if 'num_infants' not in existing_cols:
            conn.execute(sa.text('ALTER TABLE inquiries ADD COLUMN num_infants INTEGER NOT NULL DEFAULT 0'))
            print("✅ num_infants added.")
        conn.commit()
    print("✅ Migration complete.")