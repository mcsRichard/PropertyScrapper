
import sys
import os

# Create a mock env for the check
os.environ['WECHAT_APP_ID'] = 'test'
os.environ['WECHAT_APP_SECRET'] = 'test'

# Add backend to path
sys.path.insert(0, os.path.join(os.getcwd(), 'scf_deploy', 'backend'))

try:
    from config import Config
    print(f"WECHAT_APP_ID: {getattr(Config, 'WECHAT_APP_ID', 'MISSING')}")
    print(f"AUTH_TOKEN_EXPIRES: {getattr(Config, 'AUTH_TOKEN_EXPIRES', 'MISSING')}")
    
    if hasattr(Config, 'AUTH_TOKEN_EXPIRES'):
        print("SUCCESS: AUTH_TOKEN_EXPIRES exists.")
    else:
        print("FAILURE: AUTH_TOKEN_EXPIRES missing.")
except Exception as e:
    print(f"ERROR: {e}")
    import traceback
    traceback.print_exc()
