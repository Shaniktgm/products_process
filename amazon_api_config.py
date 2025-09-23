#!/usr/bin/env python3
"""
Amazon API Configuration
Store API credentials securely (not committed to git)
"""

import os
from typing import Dict, Any

def get_amazon_api_config() -> Dict[str, str]:
    """Get Amazon API configuration from environment variables or config file"""
    
    # Try to get from environment variables first (recommended for production)
    config = {
        'access_key': os.getenv('AMAZON_ACCESS_KEY'),
        'secret_key': os.getenv('AMAZON_SECRET_KEY'),
        'associate_tag': os.getenv('AMAZON_ASSOCIATE_TAG'),
    }
    
    # If not in environment, try to load from local config file
    if not all(config.values()):
        try:
            from amazon_api_local_config import AMAZON_API_CONFIG
            config.update(AMAZON_API_CONFIG)
        except ImportError:
            # Fallback to hardcoded values (for development only)
            # WARNING: These should not be committed to git!
            config = {
                'access_key': 'AKPATKWXAM1758523929',
                'secret_key': 'YxW3wUc6a96fsRZYxOhHAI5+lIYvszrmqV3Qawfs',
                'associate_tag': 'homeprinciple-20',
            }
    
    # Validate configuration
    if not all(config.values()):
        raise ValueError("Amazon API credentials not found. Please set environment variables or create amazon_api_local_config.py")
    
    return config

def create_local_config_template():
    """Create a template for local API configuration"""
    template = '''#!/usr/bin/env python3
"""
Amazon API Local Configuration
Copy this file and add your actual credentials
DO NOT commit this file to git!
"""

AMAZON_API_CONFIG = {
    'access_key': 'YOUR_ACCESS_KEY_HERE',
    'secret_key': 'YOUR_SECRET_KEY_HERE', 
    'associate_tag': 'YOUR_ASSOCIATE_TAG_HERE',
}
'''
    
    with open('amazon_api_local_config.py.template', 'w') as f:
        f.write(template)
    
    print("✅ Created amazon_api_local_config.py.template")
    print("📝 Copy this file to amazon_api_local_config.py and add your credentials")
    print("⚠️  DO NOT commit amazon_api_local_config.py to git!")

if __name__ == "__main__":
    create_local_config_template()
