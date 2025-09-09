#!/usr/bin/env python3
"""
Easy script to change scoring method and update all products
"""

import json
import sys
from configurable_scoring_system import ConfigurableScoringSystem

def show_current_method():
    """Show current scoring method"""
    try:
        with open("scoring_config.json", 'r') as f:
            config = json.load(f)
        
        current_method = config.get("overall_score", {}).get("method", "price_based")
        method_info = config.get("overall_score", {}).get("options", {}).get(current_method, {})
        
        print(f"📊 Current Scoring Method: {current_method}")
        print(f"   Description: {method_info.get('description', 'No description')}")
        print(f"   Formula: {method_info.get('formula', 'No formula')}")
        return current_method
        
    except Exception as e:
        print(f"❌ Error reading configuration: {e}")
        return None

def list_available_methods():
    """List all available scoring methods"""
    try:
        with open("scoring_config.json", 'r') as f:
            config = json.load(f)
        
        print("\n📋 Available Scoring Methods:")
        print("=" * 50)
        
        methods = config.get("overall_score", {}).get("options", {})
        for i, (method_name, method_info) in enumerate(methods.items(), 1):
            print(f"   {i}. {method_name}")
            print(f"      {method_info.get('description', 'No description')}")
            print(f"      Formula: {method_info.get('formula', 'No formula')}")
            print()
        
        return list(methods.keys())
        
    except Exception as e:
        print(f"❌ Error reading configuration: {e}")
        return []

def change_scoring_method(new_method: str):
    """Change the scoring method in configuration"""
    try:
        with open("scoring_config.json", 'r') as f:
            config = json.load(f)
        
        # Validate method exists
        available_methods = list(config.get("overall_score", {}).get("options", {}).keys())
        if new_method not in available_methods:
            print(f"❌ Method '{new_method}' not found. Available methods: {', '.join(available_methods)}")
            return False
        
        # Update method
        config["overall_score"]["method"] = new_method
        
        # Save configuration
        with open("scoring_config.json", 'w') as f:
            json.dump(config, f, indent=2)
        
        print(f"✅ Successfully changed scoring method to: {new_method}")
        return True
        
    except Exception as e:
        print(f"❌ Error changing scoring method: {e}")
        return False

def update_products_with_new_method():
    """Update all products with the new scoring method"""
    print("\n🔄 Updating all products with new scoring method...")
    scoring_system = ConfigurableScoringSystem()
    scoring_system.update_all_product_scores()
    scoring_system.show_scoring_summary()

def interactive_mode():
    """Interactive mode to select scoring method"""
    print("🎯 Interactive Scoring Method Changer")
    print("=" * 40)
    
    # Show current method
    current_method = show_current_method()
    
    # List available methods
    available_methods = list_available_methods()
    
    if not available_methods:
        print("❌ No methods available")
        return
    
    print(f"\nCurrent method: {current_method}")
    print("\nSelect new scoring method:")
    
    for i, method in enumerate(available_methods, 1):
        print(f"   {i}. {method}")
    
    try:
        choice = input(f"\nEnter choice (1-{len(available_methods)}) or 'q' to quit: ").strip()
        
        if choice.lower() == 'q':
            print("👋 Goodbye!")
            return
        
        choice_num = int(choice)
        if 1 <= choice_num <= len(available_methods):
            new_method = available_methods[choice_num - 1]
            
            if new_method == current_method:
                print(f"⚠️  Method '{new_method}' is already selected")
                return
            
            # Change method
            if change_scoring_method(new_method):
                # Update products
                update_products_with_new_method()
                print(f"\n🎉 Successfully switched to '{new_method}' scoring method!")
            else:
                print("❌ Failed to change scoring method")
        else:
            print(f"❌ Invalid choice. Please enter 1-{len(available_methods)}")
            
    except ValueError:
        print("❌ Invalid input. Please enter a number or 'q'")
    except KeyboardInterrupt:
        print("\n👋 Goodbye!")

def main():
    """Main function"""
    if len(sys.argv) > 1:
        # Command line mode
        new_method = sys.argv[1]
        print(f"🎯 Changing scoring method to: {new_method}")
        
        if change_scoring_method(new_method):
            update_products_with_new_method()
            print(f"\n🎉 Successfully switched to '{new_method}' scoring method!")
        else:
            print("❌ Failed to change scoring method")
    else:
        # Interactive mode
        interactive_mode()

if __name__ == "__main__":
    main()
