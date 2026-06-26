import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    
    MYSQL_HOST = 'localhost'
    MYSQL_USER = 'root'
    MYSQL_PASSWORD = ''  # Cambiar por tu contraseña
    MYSQL_DB = 'concurso_danzas'
    MYSQL_CURSORCLASS = 'DictCursor'