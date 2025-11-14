#!/usr/bin/env python3
"""
Generate secure secrets for production deployment
"""

import secrets
import string

def generate_password(length=32):
    """Generate a secure random password"""
    alphabet = string.ascii_letters + string.digits + string.punctuation
    password = ''.join(secrets.choice(alphabet) for _ in range(length))
    return password

def generate_jwt_secret():
    """Generate a secure JWT secret"""
    return secrets.token_urlsafe(32)

def generate_api_key():
    """Generate a secure API key"""
    return secrets.token_urlsafe(24)

def main():
    print("=" * 60)
    print("Secure Secrets Generator")
    print("=" * 60)
    print()
    
    print("JWT Secret Key:")
    print(f"  {generate_jwt_secret()}")
    print()
    
    print("PostgreSQL Password:")
    print(f"  {generate_password(32)}")
    print()
    
    print("Redis Password:")
    print(f"  {generate_password(32)}")
    print()
    
    print("API Key (if needed):")
    print(f"  {generate_api_key()}")
    print()
    
    print("=" * 60)
    print("IMPORTANT: Store these secrets securely!")
    print("- Add them to your deployment platform (Railway, Vercel)")
    print("- Never commit them to version control")
    print("- Use different secrets for each environment")
    print("=" * 60)

if __name__ == "__main__":
    main()
