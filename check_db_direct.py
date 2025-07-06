import sqlite3

# Connect to the database
conn = sqlite3.connect('school_portal.db')
cursor = conn.cursor()

# Check if the gallery_images table exists
cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='gallery_images'")
if cursor.fetchone():
    print("gallery_images table exists")
    
    # Check the structure of the gallery_images table
    cursor.execute("PRAGMA table_info(gallery_images)")
    columns = cursor.fetchall()
    print("\nTable structure:")
    for col in columns:
        print(f"Column: {col[1]}, Type: {col[2]}")
    
    # Check the content of the gallery_images table
    cursor.execute("SELECT id, title, caption, image_filename, upload_date FROM gallery_images")
    rows = cursor.fetchall()
    print(f"\nFound {len(rows)} images in the database:")
    for row in rows:
        print(f"ID: {row[0]}, Title: {row[1]}, Filename: {row[3]}, Date: {row[4]}")
        
        # Check if image_data exists and has content
        cursor.execute("SELECT length(image_data) FROM gallery_images WHERE id = ?", (row[0],))
        data_length = cursor.fetchone()[0]
        print(f"  Image data size: {data_length} bytes")
else:
    print("gallery_images table does not exist")

# Close the connection
conn.close()
