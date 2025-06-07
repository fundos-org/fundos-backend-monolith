# @router.post("/user/invitation/validate")
# async def validate_invitation(
#     data: UserOnboardingStartRequest, 
#     session: Annotated[AsyncSession, Depends(get_session)]
# ) -> Dict[str, Any]:
    
#     result: dict = await dummy_service.verify_invitation_code(
#         invitation_code = data.invitation_code,
#         phone_number=data.phone_number, 
#         session=session
#     ) 
#     if not result["success"]:
#         logger.error(f"Error in validate_invitation: {result['message']}")
#         raise HTTPException(status_code=400, detail="Invalid invitation code")
    
#     response: Dict = {
#         "user_id": result["user_id"],
#         "message": "new user added",
#         "success": True
#     }
#     logger.info(f"validate_invitation response: {response}")

#     return response
