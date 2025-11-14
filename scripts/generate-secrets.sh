#!/bin/bash
# Generate secure secrets for production deployment

echo "============================================================"
echo "Secure Secrets Generator"
echo "============================================================"
echo ""

echo "JWT Secret Key:"
echo "  $(python3 -c 'import secrets; print(secrets.token_urlsafe(32))')"
echo ""

echo "PostgreSQL Password:"
echo "  $(python3 -c 'import secrets, string; print("".join(secrets.choice(string.ascii_letters + string.digits) for _ in range(32)))')"
echo ""

echo "Redis Password:"
echo "  $(python3 -c 'import secrets, string; print("".join(secrets.choice(string.ascii_letters + string.digits) for _ in range(32)))')"
echo ""

echo "API Key (if needed):"
echo "  $(python3 -c 'import secrets; print(secrets.token_urlsafe(24))')"
echo ""

echo "============================================================"
echo "IMPORTANT: Store these secrets securely!"
echo "- Add them to your deployment platform (Railway, Vercel)"
echo "- Never commit them to version control"
echo "- Use different secrets for each environment"
echo "============================================================"
