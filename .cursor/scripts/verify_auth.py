import os
import re
from typing import List, Dict
import ast

def normalize_whitespace(text: str) -> str:
    """Normalize whitespace in text for comparison."""
    return ' '.join(text.split())

def check_function_signature(content: str, signature: str) -> bool:
    """Check if a function signature exists in the content, ignoring whitespace and parameter order."""
    content_parts = normalize_whitespace(content).split()
    signature_parts = normalize_whitespace(signature).split()
    
    # Check for async def and function name
    if signature_parts[0] not in content or signature_parts[1] not in content:
        return False
    
    # Check for parameters, ignoring order
    params = set()
    for part in signature_parts[2:]:
        if ':' in part:
            params.add(normalize_whitespace(part))
    
    content_params = set()
    for part in content_parts:
        if ':' in part:
            content_params.add(normalize_whitespace(part))
    
    return params.issubset(content_params)

def check_dashboard_route(file_content: str) -> List[str]:
    """Check if the dashboard route follows the required pattern."""
    issues = []
    
    # Check for proper route decorator
    if "@app.get(\"/dashboard\")" not in normalize_whitespace(file_content):
        issues.append("Missing or incorrect dashboard route decorator")
    
    # Check for proper function signature
    if not check_function_signature(file_content, "async def dashboard_page(request: Request, db: Session = Depends(get_db))"):
        issues.append("Incorrect function signature for dashboard route")
    
    # Check for authentication check
    auth_check = normalize_whitespace("""
        try:
            current_user = await get_current_user(request, db)
        except HTTPException:
            return RedirectResponse(url="/login-page", status_code=status.HTTP_302_FOUND)
    """)
    if auth_check not in normalize_whitespace(file_content):
        issues.append("Missing or incorrect authentication check in dashboard route")
    
    # Check for proper context preparation
    if '"user": current_user' not in file_content:
        issues.append("Missing user object in template context")
    
    return issues

def check_get_current_user(file_content: str) -> List[str]:
    """Check if the get_current_user function follows the required pattern."""
    issues = []
    
    # Check for proper function signature
    if not check_function_signature(file_content, "async def get_current_user(request: Request, db: Session = Depends(get_db))"):
        issues.append("Incorrect function signature for get_current_user")
    
    # Check for token validation
    if normalize_whitespace("token = await get_token_from_cookie(request)") not in normalize_whitespace(file_content):
        issues.append("Missing token retrieval from cookie")
    
    # Check for JWT validation
    if normalize_whitespace("jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])") not in normalize_whitespace(file_content):
        issues.append("Missing or incorrect JWT validation")
    
    # Check for user lookup
    if normalize_whitespace("db.query(models.User).filter(models.User.email == email).first()") not in normalize_whitespace(file_content):
        issues.append("Missing or incorrect user lookup")
    
    return issues

def check_token_management(file_content: str) -> List[str]:
    """Check if token management follows the required pattern."""
    issues = []
    
    # Check for proper cookie settings
    required_cookie_settings = [
        "httponly=True",
        "secure=True",
        "samesite=\"lax\""
    ]
    
    for setting in required_cookie_settings:
        if setting not in file_content:
            issues.append(f"Missing required cookie setting: {setting}")
    
    # Check for Bearer prefix
    if "Bearer " not in file_content:
        issues.append("Missing Bearer prefix in token")
    
    return issues

def verify_auth_rules(file_path: str) -> Dict[str, List[str]]:
    """Verify authentication rules in the given file."""
    with open(file_path, 'r') as f:
        content = f.read()
    
    return {
        "dashboard_route": check_dashboard_route(content),
        "get_current_user": check_get_current_user(content),
        "token_management": check_token_management(content)
    }

if __name__ == "__main__":
    main_file = "app/main.py"
    if not os.path.exists(main_file):
        print(f"Error: {main_file} not found")
        exit(1)
    
    issues = verify_auth_rules(main_file)
    
    # Print results
    print("\nAuthentication Rules Verification Results:")
    print("========================================")
    
    for category, category_issues in issues.items():
        print(f"\n{category.replace('_', ' ').title()}:")
        if category_issues:
            for issue in category_issues:
                print(f"  - {issue}")
        else:
            print("  ✓ All checks passed")
    
    # Exit with error if any issues found
    if any(issues.values()):
        exit(1)
    else:
        print("\nAll authentication rules verified successfully!") 