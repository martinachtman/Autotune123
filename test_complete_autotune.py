#!/usr/bin/env python3
"""
Complete Autotune Test - Simulates web interface flow with real configuration

SETUP INSTRUCTIONS:
1. Create .env file in project root (copy from env.example)
2. Set your real Nightscout URL and API secret:
   NS_SITE=https://your-nightscout-site.herokuapp.com
   API_SECRET=your-api-secret-here
3. Run test: docker exec -it <container> python3 test_complete_autotune.py

This test uses your actual .env configuration for realistic testing.
"""

import os
import sys
import json
from datetime import datetime, timedelta

print("🚀 COMPLETE AUTOTUNE PIPELINE TEST")
print("=" * 60)

# Add the app directory to path
sys.path.insert(0, '/app/Autotune123')

try:
    # Import environment loader and autotune
    from dotenv import load_dotenv
    from autotune import Autotune
    
    # Load environment variables from .env file  
    load_dotenv('/app/Autotune123/.env')  # Explicit path for container
    load_dotenv()  # Fallback for local development
    
    # Initialize autotune instance
    autotune_instance = Autotune()
    
    # Get configuration from environment variables (.env file)
    nightscout_url = os.getenv('NS_SITE')
    api_token = os.getenv('API_SECRET')
    
    # Validation and user guidance
    print("🔧 CONFIGURATION CHECK")
    print("-" * 40)
    
    if not nightscout_url:
        print("❌ NS_SITE not found in environment")
        print("📋 SETUP REQUIRED:")
        print("   1. Create .env file from env.example")
        print("   2. Set NS_SITE=https://your-nightscout-site.herokuapp.com")
        print("   3. Set API_SECRET=your-api-secret-here")
        print("   4. Restart container and run test again")
        print("\n💡 Example .env content:")
        print("   NS_SITE=https://yourname.herokuapp.com")
        print("   API_SECRET=your-token-without-token-prefix")
        sys.exit(1)
    
    if not api_token:
        print("❌ API_SECRET not found in environment")
        print("📋 Add API_SECRET to your .env file")
        sys.exit(1)
    
    if api_token == "your-api-secret-here":
        print("⚠️  API_SECRET is still placeholder value")
        print("📋 Update .env with your real Nightscout API secret")
        sys.exit(1)
    
    print(f"✅ Nightscout URL: {nightscout_url}")
    print(f"✅ API Secret: {'*' * (len(api_token) - 4) + api_token[-4:] if len(api_token) > 4 else '****'}")
    print("✅ Configuration loaded from .env")
    
    # Date range for testing (recent dates)
    end_date = datetime.now()
    start_date = end_date - timedelta(days=3)
    
    start_date_str = start_date.strftime("%Y-%m-%d")
    end_date_str = end_date.strftime("%Y-%m-%d")
    
    print(f"\n📅 TEST PARAMETERS")
    print("-" * 40)
    print(f"📅 Date range: {start_date_str} to {end_date_str}")
    print(f"🔗 Nightscout: {nightscout_url}")
    print(f"⏱️  Testing {(end_date - start_date).days} days of data")
    
    # Step 1: Test profile loading
    print("\n1️⃣ TESTING PROFILE LOADING")
    print("-" * 40)
    try:
        df_basals, df_non_basals, profile = autotune_instance.get(nightscout_url, api_token)
        print("✅ Profile loaded successfully")
        print(f"📊 Basals: {len(df_basals)} entries")
        print(f"📊 Non-basals: {len(df_non_basals)} entries") 
        print(f"🔧 Profile keys: {list(profile.keys())}")
    except Exception as e:
        print(f"❌ Profile loading failed: {e}")
        print("Note: This may be expected if API token is not real")
        
        # Create test profile for continuation
        profile = {
            "timezone": "Europe/Zurich",
            "dia": 8.0,
            "carb_ratio": 9.0,
            "carb_ratios": {"schedule": [{"ratio": 9.0}]},
            "isfProfile": {"sensitivities": [{"sensitivity": 41.4}]},
            "basalprofile": [
                {"start": "00:00:00", "minutes": 0, "rate": 0.42},
                {"start": "01:00:00", "minutes": 60, "rate": 0.54}
            ]
        }
        print("✅ Using test profile for continuation")
    
    # Step 2: Test autotune execution
    print("\n2️⃣ TESTING AUTOTUNE EXECUTION")
    print("-" * 40)
    
    # Set up environment
    os.environ['API_SECRET'] = api_token
    os.environ['NIGHTSCOUT_HOST'] = nightscout_url
    
    try:
        # This will test the complete autotune pipeline
        result = autotune_instance.run(
            nightscout=nightscout_url,
            start_date=start_date_str,
            end_date=end_date_str,
            uam=False,
            token=api_token
        )
        
        if result is not None:
            print("✅ Autotune execution completed")
            print(f"📊 Results type: {type(result)}")
            if hasattr(result, 'shape'):
                print(f"📊 Results shape: {result.shape}")
            print(f"📋 Sample results: {result}")
        else:
            print("❌ Autotune execution returned None")
            
    except Exception as e:
        print(f"❌ Autotune execution failed: {e}")
        import traceback
        traceback.print_exc()
    
    # Step 3: Check file outputs
    print("\n3️⃣ CHECKING FILE OUTPUTS")
    print("-" * 40)
    
    autotune_dir = "/root/myopenaps"
    settings_dir = "/root/myopenaps/settings"
    
    files_to_check = [
        f"{settings_dir}/pumpprofile.json",
        f"{settings_dir}/profile.json", 
        f"{settings_dir}/autotune.json",
        f"{autotune_dir}/autotune.{end_date_str}.json",
        f"{autotune_dir}/autotune_recommendations.log"
    ]
    
    for file_path in files_to_check:
        if os.path.exists(file_path):
            size = os.path.getsize(file_path)
            print(f"✅ {file_path} ({size} bytes)")
            
            # Show first few lines for log files
            if file_path.endswith('.log') or file_path.endswith('.json'):
                try:
                    with open(file_path, 'r') as f:
                        content = f.read(200)  # First 200 chars
                        print(f"    Preview: {content[:100]}...")
                except:
                    pass
        else:
            print(f"❌ {file_path} (missing)")
    
    print("\n" + "=" * 60)
    print("🏁 AUTOTUNE PIPELINE TEST COMPLETE")
    print("=" * 60)
    
except Exception as e:
    print(f"❌ Critical error: {e}")
    import traceback
    traceback.print_exc()
    
    # Provide guidance on common issues
    print("\n🔧 TROUBLESHOOTING TIPS:")
    print("-" * 40)
    print("• Check .env file exists and has correct values")
    print("• Verify Nightscout URL is accessible")  
    print("• Ensure API secret has correct permissions")
    print("• Try with a longer date range if no data found")
    print("• Check container logs: docker-compose logs")