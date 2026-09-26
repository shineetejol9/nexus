from passlib.context import CryptContext
from jose import jwt
from datetime import datetime, timedelta
import os
from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from backend.database import get_connection, get_all_users
# Password hashing configuration
pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto"
)


def hash_password(password):
    return pwd_context.hash(password)


def verify_password(password, hashed_password):
    return pwd_context.verify(password, hashed_password)

def create_access_token(user_id, username, role):

    secret_key = os.getenv("JWT_SECRET_KEY")
    algorithm = os.getenv("JWT_ALGORITHM", "HS256")
    expire_minutes = int(os.getenv("JWT_EXPIRE_MINUTES", "60"))

    expire_time = datetime.utcnow() + timedelta(
        minutes=expire_minutes
    )

    payload = {
        "user_id": user_id,
        "username": username,
        "role": role,
        "exp": expire_time
    }

    token = jwt.encode(
        payload,
        secret_key,
        algorithm=algorithm
    )

    return token


def register_user(username, email, password, role="Viewer"):
    # Security: Public registration ALWAYS receives Viewer role regardless of client input
    assigned_role = "Viewer"

    connection = get_connection()
    cursor = connection.cursor()

    # Check whether username already exists
    cursor.execute(
        "SELECT id FROM users WHERE username = %s",
        (username,)
    )

    existing_user = cursor.fetchone()

    if existing_user:
        cursor.close()
        connection.close()
        return False, "Username already exists"

    # Hash password
    password_hash = hash_password(password)

    # Insert user
    cursor.execute("""
        INSERT INTO users
        (username, email, password_hash, role)
        VALUES (%s, %s, %s, %s)
        RETURNING id
    """, (
        username,
        email,
        password_hash,
        assigned_role
    ))

    user_id = cursor.fetchone()[0]

    connection.commit()

    cursor.close()
    connection.close()

    return True, user_id
def check_user_active(user_id):
    if user_id is None:
        return True
    try:
        connection = get_connection()
        cursor = connection.cursor()
        cursor.execute("SELECT status FROM users WHERE id = %s", (user_id,))
        row = cursor.fetchone()
        cursor.close()
        connection.close()
        if row and row[0] == "inactive":
            return False
        return True
    except Exception:
        return True


def login_user(username, password):

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT id, username, password_hash, role, status
        FROM users
        WHERE username = %s
    """, (username,))

    user = cursor.fetchone()

    cursor.close()
    connection.close()

    if user is None:
        return False, "Invalid username or password"

    user_id = user[0]
    db_username = user[1]
    password_hash = user[2]
    role = user[3]
    status = user[4] if len(user) > 4 and user[4] is not None else "active"

    if not verify_password(password, password_hash):
        return False, "Invalid username or password"

    if status == "inactive":
        return False, "Account is deactivated. Please contact an administrator."

    token = create_access_token(
        user_id,
        db_username,
        role
    )

    return True, token

security = HTTPBearer()


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
):

    token = credentials.credentials

    secret_key = os.getenv("JWT_SECRET_KEY")
    algorithm = os.getenv("JWT_ALGORITHM", "HS256")

    try:
        payload = jwt.decode(
            token,
            secret_key,
            algorithms=[algorithm]
        )

        if not check_user_active(payload.get("user_id")):
            raise HTTPException(
                status_code=403,
                detail="Account is inactive"
            )

        return payload

    except HTTPException:
        raise
    except Exception:
        raise HTTPException(
            status_code=401,
            detail="Invalid or expired token"
        )
def require_role(*required_roles):

    def role_checker(
        current_user=Depends(get_current_user)
    ):

        if current_user["role"] not in required_roles:
            raise HTTPException(
                status_code=403,
                detail="You do not have permission to access this resource"
            )

        return current_user

    return role_checker