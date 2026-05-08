from jose import jwt
from datetime import datetime, timedelta

SECRET_KEY = "super-secret"
ALGORITHM = "HS256"

payload = {
    "sub": "9",
    "exp": datetime.utcnow() + timedelta(hours=12),
}

token = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

print(token)