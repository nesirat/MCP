from passlib.context import CryptContext

# Configure password hashing with explicit bcrypt version
pwd_context = CryptContext(
    schemes=['bcrypt'],
    deprecated='auto',
    bcrypt__rounds=12
)

# Current hash from database
current_hash = '$2b$12$dRwnCx4OPg7HH6/jozRMV.pzedWWEJvxne1Sa72TnieA9dmz/SBjS'

print(f"\n=== HASH COMPARISON START ===")
print(f"Current hash from database: {current_hash}")
print(f"Current hash length: {len(current_hash)}")

# Generate new hash for comparison
test_password = 'admin'
new_hash = pwd_context.hash(test_password)
print(f"\nGenerated new hash for '{test_password}': {new_hash}")
print(f"New hash length: {len(new_hash)}")

# Test verification both ways
print(f"\nTesting verification:")
print(f"1. Verify '{test_password}' against database hash:")
result1 = pwd_context.verify(test_password, current_hash)
print(f"   Result: {'Match' if result1 else 'No match'}")

print(f"\n2. Verify '{test_password}' against new hash:")
result2 = pwd_context.verify(test_password, new_hash)
print(f"   Result: {'Match' if result2 else 'No match'}")

print("\n=== HASH COMPARISON COMPLETE ===") 