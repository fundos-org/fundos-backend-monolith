# @router.post("/user/details")
# async def store_user_details(
#     data: UserDetailsRequest, 
#     session: Annotated[AsyncSession, Depends(get_session)]
# ) -> UserDetailsResponse:

#     result = await dummy_service.set_user_details(
#         user_id = data.user_id,
#         first_name= data.first_name,
#         last_name=data.last_name,
#         session=session
#     )

#     return UserDetailsResponse(**result) 