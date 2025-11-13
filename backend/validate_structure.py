"""Validate the backend project structure."""
import os
import sys

def check_structure():
    """Check if all required directories and files exist."""
    
    # Change to backend directory if running from root
    script_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(script_dir)
    
    required_structure = {
        "directories": [
            "app",
            "app/api",
            "app/api/routes",
            "app/core",
            "app/models",
            "app/schemas",
            "app/services",
            "app/ml",
        ],
        "files": [
            "requirements.txt",
            "Dockerfile",
            ".env.example",
            ".gitignore",
            "README.md",
            "app/__init__.py",
            "app/main.py",
            "app/core/__init__.py",
            "app/core/config.py",
            "app/core/exceptions.py",
            "app/api/__init__.py",
            "app/api/routes/__init__.py",
            "app/models/__init__.py",
            "app/schemas/__init__.py",
            "app/services/__init__.py",
            "app/ml/__init__.py",
        ]
    }
    
    missing = []
    
    # Check directories
    for directory in required_structure["directories"]:
        if not os.path.isdir(directory):
            missing.append(f"Directory: {directory}")
    
    # Check files
    for file in required_structure["files"]:
        if not os.path.isfile(file):
            missing.append(f"File: {file}")
    
    if missing:
        print("❌ Missing items:")
        for item in missing:
            print(f"  - {item}")
        return False
    else:
        print("✅ All required directories and files are present!")
        print("\n📁 Project structure:")
        print("backend/")
        print("├── app/")
        print("│   ├── api/")
        print("│   │   └── routes/")
        print("│   ├── core/")
        print("│   │   ├── config.py")
        print("│   │   └── exceptions.py")
        print("│   ├── models/")
        print("│   ├── schemas/")
        print("│   ├── services/")
        print("│   ├── ml/")
        print("│   └── main.py")
        print("├── requirements.txt")
        print("├── Dockerfile")
        print("├── .env.example")
        print("└── README.md")
        return True

if __name__ == "__main__":
    success = check_structure()
    sys.exit(0 if success else 1)
