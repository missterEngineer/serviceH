from werkzeug.security import generate_password_hash

password = 'MySecurePassword123'
password_hash = generate_password_hash(password)