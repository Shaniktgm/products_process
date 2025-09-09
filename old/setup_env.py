#!/usr/bin/env python3
"""
Setup script to help configure environment variables for Amazon API
"""

import os
import sys

def create_env_file():
    """Create .env file with user input"""
    print("🔐 Amazon API Environment Setup")
    print("=" * 40)
    print("Please provide your Amazon Product Advertising API credentials:")
    print()
    
    # Get credentials from user
    access_key = input("Enter your PAAPI Access Key ID: ").strip()
    secret_key = input("Enter your PAAPI Secret Access Key: ").strip()
    partner_tag = input("Enter your Partner Tag (Associate ID): ").strip()
    
    # Optional settings
    print("\nOptional settings (press Enter to use defaults):")
    region = input("AWS Region [us-east-1]: ").strip() or "us-east-1"
    marketplace = input("Marketplace [www.amazon.com]: ").strip() or "www.amazon.com"
    host = input("API Host [webservices.amazon.com]: ").strip() or "webservices.amazon.com"
    
    # Create .env content
    env_content = f"""# Amazon Product Advertising API Credentials
PAAPI_ACCESS_KEY={access_key}
PAAPI_SECRET_ACCESS_KEY={secret_key}
PAAPI_PARTNER_TAG={partner_tag}

# Optional: Override defaults
PAAPI_REGION={region}
PAAPI_MARKETPLACE={marketplace}
PAAPI_HOST={host}

# Database Configuration
DATABASE_PATH=amazon_products.db
"""
    
    # Write .env file
    try:
        with open('.env', 'w') as f:
            f.write(env_content)
        
        print(f"\n✅ .env file created successfully!")
        print(f"📁 File location: {os.path.abspath('.env')}")
        print("\n⚠️  Important:")
        print("   - Keep this file secure and never commit it to version control")
        print("   - Add .env to your .gitignore file")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Error creating .env file: {str(e)}")
        return False

def test_credentials():
    """Test if the credentials work"""
    print("\n🧪 Testing credentials...")
    
    try:
        from simple_amazon_api import SimpleAmazonAPI
        api = SimpleAmazonAPI()
        print("✅ Credentials loaded successfully!")
        return True
    except Exception as e:
        print(f"❌ Error loading credentials: {str(e)}")
        return False

def main():
    """Main setup function"""
    print("🚀 Amazon API Environment Setup")
    print("=" * 40)
    
    # Check if .env already exists
    if os.path.exists('.env'):
        print("⚠️  .env file already exists!")
        overwrite = input("Do you want to overwrite it? (y/N): ").strip().lower()
        if overwrite != 'y':
            print("Setup cancelled.")
            return
    
    # Create .env file
    if create_env_file():
        # Test credentials
        test_credentials()
        
        print("\n🎉 Setup completed!")
        print("\n📖 Next steps:")
        print("   1. Test the API: python3 simple_amazon_api.py")
        print("   2. Collect products: python3 main.py")
        print("   3. Check the database and exports")
    else:
        print("\n❌ Setup failed. Please check the error messages above.")
        sys.exit(1)

if __name__ == "__main__":
    main()
