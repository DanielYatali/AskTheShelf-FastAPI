import bcrypt

from app.core.security import hash_password, check_password

# def hash_password(password):
#     password_bytes = password.encode('utf-8')
#     hashed_password = bcrypt.hashpw(password_bytes, bcrypt.gensalt())
#     return hashed_password
#
#
# def check_password(stored_hash, password_to_check):
#     password_bytes = password_to_check.encode('utf-8')
#     return bcrypt.checkpw(password_bytes, stored_hash)


    # Example usage
my_password = "supersecretpassword"
hashed_password = hash_password(my_password)
print("Hashed password:", hashed_password)

# The hashed password can be stored in a database

# Checking the password
check_result = check_password(hashed_password, "supersecretpassword")  # This should return True
print("Password match:", check_result)

check_result = check_password(hashed_password, "wrongpassword")  # This should return False
print("Password match:", check_result)