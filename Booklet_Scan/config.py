import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'your-secret-key' # It's important to set a strong secret key
    # Ensure the database is created within the 'Booklet_Scan' directory, specifically in an 'instance' folder
    # for better organization, or directly in the project root if preferred.
    # Let's put it in the project root for now, matching 'Booklet_Scan/app.db'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'sqlite:///' + os.path.join(os.path.abspath(os.path.dirname(os.path.dirname(__file__))), 'app.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
