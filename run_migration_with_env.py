import os
from migrate_db_files_to_storage import migrate

os.environ['SUPABASE_URL'] = 'https://fdwvijvptodpojjkfret.supabase.co'
os.environ['SUPABASE_SERVICE_ROLE_KEY'] = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImZkd3ZpanZwdG9kcG9qamtmcmV0Iiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc2MDk4ODg5MCwiZXhwIjoyMDc2NTY0ODkwfQ.2Der318KqgaBVGdRI-spJasIvXze4w9rDT00BhLqRcI'
os.environ['SUPABASE_BUCKET'] = 'school'

if __name__ == '__main__':
    migrate()
