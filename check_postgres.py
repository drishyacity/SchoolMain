import psycopg2
import os

# Database URL
DATABASE_URL = "postgresql://postgres.lugpddujngbtrfouxeld:viraj1316mp@aws-0-ap-southeast-1.pooler.supabase.com:5432/postgres"

try:
    # Connect to the database
    print(f"Connecting to PostgreSQL database...")
    conn = psycopg2.connect(DATABASE_URL)
    cursor = conn.cursor()
    
    # Check if the gallery_images table exists
    cursor.execute("SELECT EXISTS(SELECT 1 FROM information_schema.tables WHERE table_name = 'gallery_images')")
    if cursor.fetchone()[0]:
        print("gallery_images table exists")
        
        # Check the structure of the gallery_images table
        cursor.execute("""
            SELECT column_name, data_type 
            FROM information_schema.columns 
            WHERE table_name = 'gallery_images'
        """)
        columns = cursor.fetchall()
        print("\nTable structure:")
        for col in columns:
            print(f"Column: {col[0]}, Type: {col[1]}")
        
        # Check the content of the gallery_images table
        cursor.execute("SELECT id, title, caption, image_filename, upload_date FROM gallery_images")
        rows = cursor.fetchall()
        print(f"\nFound {len(rows)} images in the database:")
        for row in rows:
            print(f"ID: {row[0]}, Title: {row[1]}, Filename: {row[3]}, Date: {row[4]}")
            
            # Check if image_data exists and has content
            cursor.execute("SELECT octet_length(image_data) FROM gallery_images WHERE id = %s", (row[0],))
            data_length = cursor.fetchone()[0]
            print(f"  Image data size: {data_length} bytes")
    else:
        print("gallery_images table does not exist")
        
        # List all tables in the database
        cursor.execute("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'")
        tables = cursor.fetchall()
        print("\nAvailable tables:")
        for table in tables:
            print(f"- {table[0]}")
    
    # Close the connection
    cursor.close()
    conn.close()
    
except Exception as e:
    print(f"Error: {str(e)}")
