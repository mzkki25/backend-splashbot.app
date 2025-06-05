from typing import Optional, Dict
from firebase_admin import auth, firestore
from fastapi import HTTPException, status

from models.schemas import UserCreate, UserLogin
from core.firebase import db
from core.logging_logger import setup_logger

logger = setup_logger(__name__)


class AuthService:
    @staticmethod
    def create_user(user: UserCreate) -> str:
        try:
            user_record = auth.create_user(
                email=user.email,
                password=user.password,
                display_name=user.username
            )
            logger.info(f"User created: {user_record.uid}")

            db.collection('users').document(user_record.uid).set({
                'email': user.email,
                'username': user.username,
                'password': user.password, 
                'created_at': firestore.SERVER_TIMESTAMP,
            })

            logger.info(f"User data saved to Firestore: {user_record.uid}")
            return user_record.uid
        except Exception as e:
            logger.error(f"Error creating user: {str(e)}")
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    @staticmethod
    def authenticate_user(user: UserLogin) -> Dict[str, str]:
        try:
            query_field = 'email' if '@' in user.email_or_username else 'username'
            users = db.collection('users').where(query_field, '==', user.email_or_username).limit(1).get()

            logger.info(f"User login attempt: {user.email_or_username}")

            if not users:
                logger.warning(f"User not found: {user.email_or_username}")
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

            user_data = users[0].to_dict()
            saved_password = user_data.get('password')
            email = user_data.get('email')

            logger.info(f"User found: {email}")

            if user.password != saved_password:
                raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid password")

            user_record = auth.get_user_by_email(email)
            custom_token = auth.create_custom_token(user_record.uid)

            logger.info(f"Custom token created for user: {user_record.uid}")

            return {
                "user_id": user_record.uid,
                "token": custom_token.decode('utf-8')  
            }

        except Exception as e:
            logger.error(f"Login error: {str(e)}")
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
