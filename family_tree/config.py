import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.getenv('SECRET_KEY')
    __database_path = os.path.join(os.path.dirname(__file__), 'databases', 'site.db')
    SQLALCHEMY_DATABASE_URI = f'sqlite:///{__database_path}'
    SQLALCHEMY_TRACK_MODIFICATIONS = False


