# WSGI Entry Point

from app import app

# run in production
if __name__ == '__main__':
    
    # runs the app
    app.run()