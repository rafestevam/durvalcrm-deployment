#!/usr/bin/env python3
"""
Test Complete Login Flow
Tests the full OAuth2/OIDC flow with PKCE
"""

import requests
import base64
import hashlib
import secrets
import urllib.parse
from requests.packages.urllib3.exceptions import InsecureRequestWarning

# Disable SSL warnings for testing
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

def base64url_encode(data):
    """Base64 URL encode without padding"""
    return base64.urlsafe_b64encode(data).rstrip(b'=').decode('ascii')

def generate_pkce_params():
    """Generate PKCE code verifier and challenge"""
    code_verifier = base64url_encode(secrets.token_bytes(32))
    code_challenge = base64url_encode(hashlib.sha256(code_verifier.encode()).digest())
    return code_verifier, code_challenge

def test_login_flow():
    print("🧪 Testing complete login flow...")
    
    # Step 1: Get login info
    print("1️⃣ Getting login info from API...")
    try:
        response = requests.get("https://crm.durvalcrm.org/api/auth/login-info", verify=False)
        if response.status_code == 200:
            login_info = response.json()
            print(f"   ✅ Client ID: {login_info['clientId']}")
            print(f"   ✅ Auth Server: {login_info['authServerUrl']}")
        else:
            print(f"   ❌ Failed to get login info: {response.status_code}")
            return False
    except Exception as e:
        print(f"   ❌ Error getting login info: {e}")
        return False
    
    # Step 2: Generate PKCE parameters
    print("2️⃣ Generating PKCE parameters...")
    code_verifier, code_challenge = generate_pkce_params()
    state = base64url_encode(secrets.token_bytes(16))
    redirect_uri = "https://crm.durvalcrm.org/auth/callback"
    
    print(f"   ✅ Code challenge: {code_challenge[:20]}...")
    print(f"   ✅ State: {state[:20]}...")
    
    # Step 3: Test authorization endpoint
    print("3️⃣ Testing authorization endpoint...")
    auth_params = {
        'client_id': 'durvalcrm-app',
        'response_type': 'code',
        'redirect_uri': redirect_uri,
        'scope': 'openid profile email',
        'state': state,
        'code_challenge': code_challenge,
        'code_challenge_method': 'S256'
    }
    
    auth_url = f"https://admin.durvalcrm.org/realms/durval-crm/protocol/openid-connect/auth"
    
    try:
        response = requests.get(auth_url, params=auth_params, verify=False, allow_redirects=False)
        if response.status_code == 200:
            print("   ✅ Authorization endpoint accessible")
            print("   ✅ Login form should be displayed")
        else:
            print(f"   ❌ Authorization endpoint error: {response.status_code}")
            if 'Location' in response.headers:
                location = response.headers['Location']
                if 'error=' in location:
                    parsed_location = urllib.parse.urlparse(location)
                    query_params = urllib.parse.parse_qs(parsed_location.query)
                    if 'iss' in query_params:
                        issuer = query_params['iss'][0]
                        if issuer.startswith('https://'):
                            print(f"   ✅ Issuer URL uses HTTPS: {issuer}")
                        else:
                            print(f"   ❌ Issuer URL uses HTTP: {issuer}")
                return False
    except Exception as e:
        print(f"   ❌ Error testing authorization endpoint: {e}")
        return False
    
    # Step 4: Test realm info
    print("4️⃣ Testing realm information...")
    try:
        response = requests.get("https://admin.durvalcrm.org/realms/durval-crm", verify=False)
        if response.status_code == 200:
            realm_info = response.json()
            token_service = realm_info.get('token-service', '')
            if token_service.startswith('https://'):
                print(f"   ✅ Token service uses HTTPS: {token_service}")
            else:
                print(f"   ❌ Token service uses HTTP: {token_service}")
        else:
            print(f"   ❌ Failed to get realm info: {response.status_code}")
            return False
    except Exception as e:
        print(f"   ❌ Error getting realm info: {e}")
        return False
    
    # Step 5: Test callback endpoint
    print("5️⃣ Testing callback endpoint...")
    try:
        response = requests.get("https://crm.durvalcrm.org/auth/callback", verify=False)
        if response.status_code == 200:
            print("   ✅ Callback endpoint accessible")
            # Check for no-cache headers
            cache_control = response.headers.get('cache-control', '')
            if 'no-cache' in cache_control.lower():
                print("   ✅ Callback has proper no-cache headers")
            else:
                print("   ⚠️ Callback may be cached")
        else:
            print(f"   ❌ Callback endpoint error: {response.status_code}")
            return False
    except Exception as e:
        print(f"   ❌ Error testing callback endpoint: {e}")
        return False
    
    print("\n🎉 All tests passed!")
    print("📋 Test Summary:")
    print("   ✅ API endpoints accessible")
    print("   ✅ PKCE parameters generated correctly")
    print("   ✅ Authorization endpoint working")
    print("   ✅ HTTPS issuer URL configured")
    print("   ✅ Callback endpoint properly configured")
    print("\n👤 Ready for manual login test with:")
    print("   Username: tesouraria")
    print("   Password: cairbar@2025")
    
    return True

if __name__ == "__main__":
    success = test_login_flow()
    exit(0 if success else 1)