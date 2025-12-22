import os
import secrets
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa

def generate_rsa_key():
    key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048,
    )
    private_key = key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption()
    )
    return private_key.decode('utf-8')

def main():
    print("Generating RSA Key...")
    rsa_key = generate_rsa_key()
    
    # Escape newlines for .env if needed, but docker compose often handles multi-line if quoted
    # However, for simply writing to .env, we can just dump it. 
    # But usually for one-line env vars it's tricky. 
    # Lago docs usually stick it directly in env file or utilize separate file.
    # We'll put it in .env quoted.
    
    # Generate other secrets
    secret_key_base = secrets.token_hex(64)
    encryption_primary = secrets.token_hex(32)
    encryption_deterministic = secrets.token_hex(32)
    key_derivation = secrets.token_hex(32)
    
    env_content = f"""LAGO_RSA_PRIVATE_KEY="{rsa_key}"
LAGO_API_URL=http://localhost:3000
LAGO_FRONT_URL=http://localhost
POSTGRES_USER=lago
POSTGRES_PASSWORD=changeme
POSTGRES_DB=lago
REDIS_HOST=redis
REDIS_PORT=6379
SECRET_KEY_BASE={secret_key_base}
LAGO_ENCRYPTION_PRIMARY_KEY={encryption_primary}
LAGO_ENCRYPTION_DETERMINISTIC_KEY={encryption_deterministic}
LAGO_ENCRYPTION_KEY_DERIVATION_SALT={key_derivation}
"""
    
    with open('.env', 'w') as f:
        f.write(env_content)
    
    print("Created .env with new keys.")

if __name__ == "__main__":
    main()
