from app import app, init_db
from waitress import serve

if __name__ == '__main__':
    # Initialize the database
    init_db()

    # Run the application with waitress (production server)
    print("Starting server with waitress on http://127.0.0.1:5000")
    serve(app, host='127.0.0.1', port=5000)
