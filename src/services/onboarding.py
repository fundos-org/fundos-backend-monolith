from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from src.models.user import User
from src.utils.dependencies import get_user, get_session 
from src.models.user import investorType

class OnboardingService:

    def __init__(self):
        self.session: AsyncSession = get_session

    async def set_user_details(self, user_id: str,first_name: str,last_name: str) -> dict:
        try:
            user: User = get_user(user_id=user_id)
            user.first_name = first_name
            user.last_name = last_name

            self.session.add(user)
            await self.session.commit()
            await self.session.refresh(user)

            return {
                "message": "User details updated successfully",
                "user_id": user.id,
                "first_name": user.first_name,
                "last_name": user.last_name
            }

        except Exception as e:
            await self.session.rollback()
            raise HTTPException(status_code=500, detail=f"Failed to update user details: {str(e)}")
        
    async def choose_investor_type(self, user_id, investor_type: investorType) -> any :
        
        try:
            user: User = get_user(user_id= user_id)
            user.investor_type = investor_type

            self.session.add(user)
            await self.session.commit()
            await self.session.refresh(user)

            return {
                "message": "User details updated successfully",
                "user_id": user.id,
                "first_name": user.first_name,
                "last_name": user.last_name
            }

        except Exception as e:
            await self.session.rollback()
            raise HTTPException(status_code=500, detail=f"Failed to update user details: {str(e)}")
        
    async def declaration_accepted( self, user_id: str, declaration_accepted: bool) -> any : 

        try: 
            user: User = get_user(user_id=user_id) 

            user.declaration_accepted = declaration_accepted
            self.session.add(user)
            await self.session.commit()
            await self.session.refresh(user) 

            return {
                "message": "User details updated successfully",
                "user_id": user.id,
                "declaration_accepted": f"{declaration_accepted}",
            }

        except Exception as e:
            await self.session.rollback()
            raise HTTPException(status_code=500, detail=f"Failed to update user details: {str(e)}")
        
