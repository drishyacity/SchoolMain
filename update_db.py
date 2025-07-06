from app import app, db
import sqlalchemy as sa
from sqlalchemy import text

# Run this script to update the database schema
with app.app_context():
    # Add the position_type column to the teachers table if it doesn't exist
    try:
        with db.engine.connect() as conn:
            conn.execute(text("ALTER TABLE teachers ADD COLUMN position_type VARCHAR(50) DEFAULT 'teaching'"))
            conn.commit()
        print("Added position_type column to teachers table")
    except Exception as e:
        print(f"Note: {e}")
        print("Column may already exist or there was an error")

    # Update existing teachers based on their position
    try:
        with db.engine.connect() as conn:
            # Get all teachers
            result = conn.execute(text("SELECT id, position FROM teachers"))
            teachers = result.fetchall()

            # Update position_type based on position
            leadership_positions = ['Principal', 'Director', 'Chairman', 'Vice Principal', 'Head of School']

            for teacher in teachers:
                teacher_id = teacher[0]
                position = teacher[1]

                if position in leadership_positions:
                    conn.execute(text(f"UPDATE teachers SET position_type = 'leadership' WHERE id = {teacher_id}"))
                else:
                    conn.execute(text(f"UPDATE teachers SET position_type = 'teaching' WHERE id = {teacher_id}"))

            conn.commit()
            print(f"Updated position_type for {len(teachers)} teachers")
    except Exception as e:
        print(f"Error updating teachers: {e}")

print("Database update complete")
