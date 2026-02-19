import logging
import os
import sys
from kiteconnect import KiteConnect
from dotenv import load_dotenv, set_key

# Load existing .env
load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def generate_access_token():
    api_key = os.getenv("KITE_API_KEY")
    api_secret = os.getenv("KITE_API_SECRET")

    if not api_key:
        logger.error("API Key missing in .env")
        return

    kite = KiteConnect(api_key=api_key)

    print("\n=== Kite Connect Login Flow ===")
    print(f"Login URL: {kite.login_url()}")
    
    # Check if request token is passed as argument
    if len(sys.argv) > 1:
        request_token = sys.argv[1]
    else:
        print("1. Open the URL above.")
        print("2. Login and copy the 'request_token' from the redirect URL.")
        request_token = input("Enter Request Token: ").strip()

    try:
        data = kite.generate_session(request_token, api_secret=api_secret)
        access_token = data["access_token"]
        
        print(f"\nSUCCESS! Access Token Generated: {access_token}")
        
        # Save to .env
        env_file = ".env"
        # set_key requires python-dotenv to be installed
        try:
            set_key(env_file, "KITE_ACCESS_TOKEN", access_token)
            print(f"Updated {env_file} with new KITE_ACCESS_TOKEN.")
        except Exception as e:
            print(f"Could not update .env Automatically: {e}")
            print("Please manually update KITE_ACCESS_TOKEN in .env")
        
    except Exception as e:
        logger.error(f"Failed to generate session: {e}")

if __name__ == "__main__":
    generate_access_token()
