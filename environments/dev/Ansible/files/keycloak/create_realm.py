#!/usr/bin/env python3
"""
Script to create Keycloak realm and user
"""
import json
import sys
import requests
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry

# Configuration
KEYCLOAK_URL = "http://localhost:8090"
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "admin"
REALM_NAME = "durval-crm"
USER_USERNAME = "tesouraria"
USER_PASSWORD = "cairbar@2025"

def create_session_with_retries():
    """Create a requests session with retry logic"""
    session = requests.Session()
    retry = Retry(
        total=3,
        backoff_factor=0.3,
        status_forcelist=[500, 502, 503, 504]
    )
    adapter = HTTPAdapter(max_retries=retry)
    session.mount('http://', adapter)
    session.mount('https://', adapter)
    return session

def get_admin_token(session):
    """Get admin access token from Keycloak"""
    token_url = f"{KEYCLOAK_URL}/realms/master/protocol/openid-connect/token"
    data = {
        'grant_type': 'password',
        'client_id': 'admin-cli',
        'username': ADMIN_USERNAME,
        'password': ADMIN_PASSWORD
    }
    
    try:
        response = session.post(token_url, data=data)
        response.raise_for_status()
        return response.json()['access_token']
    except Exception as e:
        print(f"Error getting admin token: {e}")
        sys.exit(1)

def check_realm_exists(session, token):
    """Check if realm already exists"""
    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json'
    }
    
    try:
        response = session.get(f"{KEYCLOAK_URL}/admin/realms/{REALM_NAME}", headers=headers)
        return response.status_code == 200
    except:
        return False

def create_realm(session, token):
    """Create the durval-crm realm"""
    if check_realm_exists(session, token):
        print(f"Realm '{REALM_NAME}' already exists")
        return True
    
    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json'
    }
    
    realm_data = {
        'realm': REALM_NAME,
        'enabled': True,
        'displayName': 'Durval CRM',
        'displayNameHtml': '<b>Durval CRM</b>',
        'registrationAllowed': False,
        'resetPasswordAllowed': True,
        'rememberMe': True,
        'verifyEmail': False,
        'loginWithEmailAllowed': True,
        'duplicateEmailsAllowed': False,
        'sslRequired': 'external',
        'accessTokenLifespan': 1800,
        'ssoSessionIdleTimeout': 1800,
        'ssoSessionMaxLifespan': 36000,
        'bruteForceProtected': True,
        'permanentLockout': False,
        'maxFailureWaitSeconds': 900,
        'minimumQuickLoginWaitSeconds': 60,
        'waitIncrementSeconds': 60,
        'quickLoginCheckMilliSeconds': 1000,
        'maxDeltaTimeSeconds': 43200,
        'failureFactor': 30
    }
    
    try:
        response = session.post(f"{KEYCLOAK_URL}/admin/realms", 
                               headers=headers, 
                               json=realm_data)
        
        if response.status_code == 201:
            print(f"Realm '{REALM_NAME}' created successfully")
            return True
        elif response.status_code == 409:
            print(f"Realm '{REALM_NAME}' already exists")
            return True
        else:
            print(f"Failed to create realm: {response.status_code} - {response.text}")
            return False
    except Exception as e:
        print(f"Error creating realm: {e}")
        return False

def create_user(session, token):
    """Create user in the realm"""
    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json'
    }
    
    # Check if user already exists
    try:
        response = session.get(
            f"{KEYCLOAK_URL}/admin/realms/{REALM_NAME}/users",
            headers=headers,
            params={'username': USER_USERNAME}
        )
        if response.status_code == 200:
            users = response.json()
            if users and len(users) > 0:
                print(f"User '{USER_USERNAME}' already exists")
                return True
    except:
        pass
    
    # Create user
    user_data = {
        'username': USER_USERNAME,
        'enabled': True,
        'emailVerified': True,
        'firstName': 'Tesouraria',
        'lastName': 'Sistema',
        'email': 'tesouraria@durvalcrm.com',
        'credentials': [{
            'type': 'password',
            'value': USER_PASSWORD,
            'temporary': False
        }]
    }
    
    try:
        response = session.post(
            f"{KEYCLOAK_URL}/admin/realms/{REALM_NAME}/users",
            headers=headers,
            json=user_data
        )
        
        if response.status_code == 201:
            print(f"User '{USER_USERNAME}' created successfully")
            
            # Get user ID from Location header
            location = response.headers.get('Location', '')
            user_id = location.split('/')[-1] if location else None
            
            if user_id:
                # Set password
                password_data = {
                    'type': 'password',
                    'value': USER_PASSWORD,
                    'temporary': False
                }
                
                password_response = session.put(
                    f"{KEYCLOAK_URL}/admin/realms/{REALM_NAME}/users/{user_id}/reset-password",
                    headers=headers,
                    json=password_data
                )
                
                if password_response.status_code == 204:
                    print(f"Password set for user '{USER_USERNAME}'")
                else:
                    print(f"Warning: Could not set password: {password_response.status_code}")
            
            return True
        elif response.status_code == 409:
            print(f"User '{USER_USERNAME}' already exists")
            return True
        else:
            print(f"Failed to create user: {response.status_code} - {response.text}")
            return False
    except Exception as e:
        print(f"Error creating user: {e}")
        return False

def main():
    """Main function"""
    print("Starting Keycloak realm and user creation...")
    
    # Create session with retries
    session = create_session_with_retries()
    
    # Get admin token
    print("Getting admin access token...")
    token = get_admin_token(session)
    
    # Create realm
    print(f"Creating realm '{REALM_NAME}'...")
    if not create_realm(session, token):
        print("Failed to create realm")
        sys.exit(1)
    
    # Create user
    print(f"Creating user '{USER_USERNAME}' in realm '{REALM_NAME}'...")
    if not create_user(session, token):
        print("Failed to create user")
        sys.exit(1)
    
    print("Keycloak configuration completed successfully!")
    
    # Verify realm is accessible
    try:
        response = session.get(f"{KEYCLOAK_URL}/realms/{REALM_NAME}")
        if response.status_code == 200:
            print(f"Realm '{REALM_NAME}' is accessible at: {KEYCLOAK_URL}/realms/{REALM_NAME}")
            print(f"Admin console: {KEYCLOAK_URL}/admin/{REALM_NAME}/console")
        else:
            print(f"Warning: Realm created but not accessible: {response.status_code}")
    except Exception as e:
        print(f"Warning: Could not verify realm accessibility: {e}")

if __name__ == "__main__":
    main()