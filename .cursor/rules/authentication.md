# Authentication Rules

## Dashboard Access
1. All dashboard routes must implement proper authentication checks
2. The following pattern must be used for protected routes:
   ```python
   @app.get("/protected-route")
   async def protected_route(
       request: Request,
       db: Session = Depends(get_db)
   ):
       try:
           current_user = await get_current_user(request, db)
       except HTTPException:
           return RedirectResponse(url="/login-page", status_code=status.HTTP_302_FOUND)
       
       # Route logic here
       context = {
           "request": request,
           "user": current_user,
           # ... other context data
       }
       return templates.TemplateResponse("template.html", context)
   ```

## User Authentication
1. All user-related routes must use the `get_current_user` dependency
2. The `get_current_user` function must:
   - Check for the presence of a valid access token in cookies
   - Validate the token using the application's secret key
   - Return the user object if authentication is successful
   - Raise an HTTPException if authentication fails

## Token Management
1. Access tokens must be:
   - Set as HTTP-only cookies
   - Include the "Bearer" prefix
   - Have a secure flag set
   - Use the "lax" SameSite policy
2. Token expiration must be handled appropriately
3. Remember-me functionality should extend token validity when requested

## Error Handling
1. Authentication failures must:
   - Redirect to the login page for web routes
   - Return appropriate HTTP status codes for API routes
   - Include clear error messages
2. All authentication-related exceptions must be caught and handled gracefully

## Security Requirements
1. Passwords must meet the following criteria:
   - Minimum 8 characters
   - At least one uppercase letter
   - At least one lowercase letter
   - At least one number
   - At least one special character
2. All authentication endpoints must use HTTPS
3. Session management must be secure and follow best practices 