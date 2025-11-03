<<<<<<< HEAD
import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.environ.get("DATABASE_URL")
=======
import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.environ.get("DATABASE_URL")
>>>>>>> bcd457ea32467cf8181e23873afa32c1735331de
DEBUG = os.environ.get("DEBUG") == "True"