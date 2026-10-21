import logging
from datetime import timedelta
from urllib.parse import parse_qs

import jwt
from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import User
from app.schemas.auth import (
    UserRegister,
    UserResponse,
    TokenResponse,
)
from app.services.security import (
    hash_password,
    verify_password,
    create_access_token,
    decode_access_token,
    ACCESS_TOKEN_EXPIRE_MINUTES,
)


# ============================================================
# LOGGING
# ============================================================

logger = logging.getLogger(__name__)


# ============================================================
# AUTHENTICATION ROUTER
# ============================================================

router = APIRouter(
    prefix="/auth",
    tags=["Authentication"],
)


# ============================================================
# OAUTH2 CONFIGURATION
# ============================================================

oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="/auth/login"
)


# ============================================================
# 1. REGISTER NEW USER
# ============================================================

@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
)
def register_user(
    user_data: UserRegister,
    db: Session = Depends(get_db),
):
    """
    Register a new user.

    Passwords are hashed before being stored.
    Passwords are NEVER written to logs.
    """

    # --------------------------------------------------------
    # Check if email already exists
    # --------------------------------------------------------

    existing_user = (
        db.query(User)
        .filter(User.email == user_data.email)
        .first()
    )

    if existing_user:
        logger.warning(
            "Registration failed: email already registered"
        )

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email is already registered",
        )

    # --------------------------------------------------------
    # Create user
    # --------------------------------------------------------

    new_user = User(
        full_name=user_data.full_name,
        email=user_data.email,
        hashed_password=hash_password(
            user_data.password
        ),
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    # --------------------------------------------------------
    # Log successful registration
    # --------------------------------------------------------

    logger.info(
        "User registered successfully: user_id=%s",
        new_user.id,
    )

    return new_user


# ============================================================
# 2. LOGIN
#
# Supports BOTH:
#
# A. JSON from React frontend
#
# {
#     "email": "example@gmail.com",
#     "password": "password"
# }
#
# B. OAuth2 form data from Swagger
#
# username=example@gmail.com
# password=password
#
# ============================================================

@router.post(
    "/login",
    response_model=TokenResponse,
)
async def login_user(
    request: Request,
    db: Session = Depends(get_db),
):

    # --------------------------------------------------------
    # Read request body
    # --------------------------------------------------------

    body = await request.body()

    if not body:

        logger.warning(
            "Login failed: empty request body"
        )

        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Login data is required",
        )

    # --------------------------------------------------------
    # Detect request content type
    # --------------------------------------------------------

    content_type = request.headers.get(
        "content-type",
        ""
    ).lower()

    email = None
    password = None

    # ========================================================
    # JSON REQUEST
    #
    # Used by React frontend
    # ========================================================

    if "application/json" in content_type:

        try:

            data = await request.json()

        except Exception:

            logger.warning(
                "Login failed: invalid JSON request"
            )

            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Invalid JSON request",
            )

        email = data.get("email")
        password = data.get("password")

    # ========================================================
    # FORM REQUEST
    #
    # Used by Swagger OAuth2
    # ========================================================

    elif (
        "application/x-www-form-urlencoded"
        in content_type
    ):

        try:

            form_data = parse_qs(
                body.decode("utf-8")
            )

        except Exception:

            logger.warning(
                "Login failed: invalid form request"
            )

            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Invalid form request",
            )

        # ----------------------------------------------------
        # OAuth2 uses "username"
        # We use email as username
        # ----------------------------------------------------

        email_values = form_data.get(
            "username"
        )

        password_values = form_data.get(
            "password"
        )

        if email_values:

            email = email_values[0]

        if password_values:

            password = password_values[0]

    # ========================================================
    # UNSUPPORTED REQUEST FORMAT
    # ========================================================

    else:

        logger.warning(
            "Login failed: unsupported request format"
        )

        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail="Unsupported login request format",
        )

    # ========================================================
    # VALIDATE LOGIN DATA
    # ========================================================

    if not email or not password:

        logger.warning(
            "Login failed: missing credentials"
        )

        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Email/username and password are required",
        )

    email = email.strip().lower()

    # ========================================================
    # FIND USER
    # ========================================================

    user = (
        db.query(User)
        .filter(User.email == email)
        .first()
    )

    # ========================================================
    # VERIFY CREDENTIALS
    # ========================================================

    if not user:

        logger.warning(
            "Login failed: user not found"
        )

        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={
                "WWW-Authenticate": "Bearer"
            },
        )

    if not verify_password(
        password,
        user.hashed_password,
    ):

        logger.warning(
            "Login failed: invalid password"
        )

        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={
                "WWW-Authenticate": "Bearer"
            },
        )

    # ========================================================
    # CHECK ACCOUNT STATUS
    # ========================================================

    if not user.is_active:

        logger.warning(
            "Login failed: inactive account user_id=%s",
            user.id,
        )

        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This account is inactive",
        )

    # ========================================================
    # CREATE JWT ACCESS TOKEN
    # ========================================================

    access_token = create_access_token(
        data={
            "sub": str(user.id)
        },
        expires_delta=timedelta(
            minutes=ACCESS_TOKEN_EXPIRE_MINUTES
        ),
    )

    # ========================================================
    # LOG SUCCESSFUL LOGIN
    # ========================================================

    logger.info(
        "User logged in successfully: user_id=%s",
        user.id,
    )

    # ========================================================
    # RETURN TOKEN + USER
    # ========================================================

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": user,
    }


# ============================================================
# 3. GET CURRENT AUTHENTICATED USER
# ============================================================

def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
):

    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={
            "WWW-Authenticate": "Bearer"
        },
    )

    # ========================================================
    # DECODE JWT
    # ========================================================

    try:

        payload = decode_access_token(token)

        user_id = payload.get("sub")

        if user_id is None:

            logger.warning(
                "Authentication failed: missing user ID in token"
            )

            raise credentials_exception

    except (
        jwt.InvalidTokenError,
        ValueError,
        TypeError,
    ):

        logger.warning(
            "Authentication failed: invalid token"
        )

        raise credentials_exception

    # ========================================================
    # CONVERT USER ID
    # ========================================================

    try:

        user_id = int(user_id)

    except (ValueError, TypeError):

        logger.warning(
            "Authentication failed: invalid user ID in token"
        )

        raise credentials_exception

    # ========================================================
    # FIND USER
    # ========================================================

    user = (
        db.query(User)
        .filter(User.id == user_id)
        .first()
    )

    # ========================================================
    # VALIDATE USER
    # ========================================================

    if user is None:

        logger.warning(
            "Authentication failed: user not found"
        )

        raise credentials_exception

    if not user.is_active:

        logger.warning(
            "Authentication failed: inactive user_id=%s",
            user.id,
        )

        raise credentials_exception

    return user


# ============================================================
# 4. GET CURRENT USER PROFILE
# ============================================================

@router.get(
    "/me",
    response_model=UserResponse,
)
def get_my_profile(
    current_user: User = Depends(
        get_current_user
    ),
):

    logger.info(
        "User profile requested: user_id=%s",
        current_user.id,
    )

    return current_user