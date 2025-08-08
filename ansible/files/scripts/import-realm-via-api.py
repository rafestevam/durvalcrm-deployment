#!/usr/bin/env python3
"""
Script to import Keycloak realm via REST API
This script handles the import of a realm JSON file using Keycloak's admin REST API
Uses only Python standard library to avoid external dependencies
"""

import json
import sys
import urllib.request
import urllib.parse
import ssl
import urllib.error

# Create SSL context that ignores certificate verification
ssl_context = ssl.create_default_context()
ssl_context.check_hostname = False
ssl_context.verify_mode = ssl.CERT_NONE

def get_admin_token(keycloak_url, username, password):
    """Get admin access token from Keycloak"""
    token_url = f"{keycloak_url}/realms/master/protocol/openid-connect/token"
    
    data = {
        'grant_type': 'password',
        'client_id': 'admin-cli',
        'username': username,
        'password': password
    }
    
    # Encode form data
    post_data = urllib.parse.urlencode(data).encode('utf-8')
    
    # Create request
    req = urllib.request.Request(token_url, data=post_data)
    req.add_header('Content-Type', 'application/x-www-form-urlencoded')
    
    try:
        with urllib.request.urlopen(req, context=ssl_context) as response:
            response_data = json.loads(response.read().decode())
            return response_data['access_token']
    except urllib.error.HTTPError as e:
        print(f"Error getting token: {e.code} - {e.read().decode()}")
        raise

def import_realm(keycloak_url, token, realm_file):
    """Import realm using REST API"""
    import_url = f"{keycloak_url}/admin/realms"
    
    # Read realm file
    with open(realm_file, 'r') as f:
        realm_data = json.load(f)
    
    # Prepare JSON data with explicit encoding
    json_data = json.dumps(realm_data, separators=(',', ':'), ensure_ascii=False).encode('utf-8')
    
    # Create request with explicit content-length
    req = urllib.request.Request(import_url, data=json_data)
    req.add_header('Authorization', f'Bearer {token}')
    req.add_header('Content-Type', 'application/json; charset=utf-8')
    req.add_header('Content-Length', str(len(json_data)))
    req.add_header('Accept', 'application/json')
    
    try:
        with urllib.request.urlopen(req, context=ssl_context) as response:
            print(f"✓ Realm '{realm_data.get('realm', 'unknown')}' imported successfully")
            return True
    except urllib.error.HTTPError as e:
        if e.code == 409:
            print(f"ℹ Realm '{realm_data.get('realm', 'unknown')}' already exists")
            return True
        else:
            print(f"✗ Failed to import realm: {e.code} - {e.read().decode()}")
            return False

def create_user(keycloak_url, token, realm_name, username, password, email=None, first_name=None, last_name=None):
    """Create user in realm"""
    users_url = f"{keycloak_url}/admin/realms/{realm_name}/users"
    
    user_data = {
        'username': username,
        'enabled': True,
        'emailVerified': True
    }
    
    if email:
        user_data['email'] = email
    if first_name:
        user_data['firstName'] = first_name
    if last_name:
        user_data['lastName'] = last_name
    
    # Prepare JSON data
    json_data = json.dumps(user_data, separators=(',', ':'), ensure_ascii=False).encode('utf-8')
    
    # Create user
    req = urllib.request.Request(users_url, data=json_data)
    req.add_header('Authorization', f'Bearer {token}')
    req.add_header('Content-Type', 'application/json; charset=utf-8')
    req.add_header('Content-Length', str(len(json_data)))
    req.add_header('Accept', 'application/json')
    
    try:
        with urllib.request.urlopen(req, context=ssl_context) as response:
            print(f"✓ User '{username}' created successfully")
            user_created = True
    except urllib.error.HTTPError as e:
        if e.code == 409:
            print(f"ℹ User '{username}' already exists")
            user_created = True
        else:
            print(f"✗ Failed to create user: {e.code} - {e.read().decode()}")
            return False
    
    if user_created:
        # Get user ID
        search_url = f"{keycloak_url}/admin/realms/{realm_name}/users?username={username}"
        req = urllib.request.Request(search_url)
        req.add_header('Authorization', f'Bearer {token}')
        
        try:
            with urllib.request.urlopen(req, context=ssl_context) as response:
                users = json.loads(response.read().decode())
                if users:
                    user_id = users[0]['id']
                    
                    # Set password
                    password_url = f"{keycloak_url}/admin/realms/{realm_name}/users/{user_id}/reset-password"
                    password_data = {
                        'type': 'password',
                        'value': password,
                        'temporary': False
                    }
                    
                    json_data = json.dumps(password_data, separators=(',', ':'), ensure_ascii=False).encode('utf-8')
                    req = urllib.request.Request(password_url, data=json_data)
                    req.add_header('Authorization', f'Bearer {token}')
                    req.add_header('Content-Type', 'application/json; charset=utf-8')
                    req.add_header('Content-Length', str(len(json_data)))
                    req.add_header('Accept', 'application/json')
                    req.get_method = lambda: 'PUT'
                    
                    try:
                        with urllib.request.urlopen(req, context=ssl_context) as response:
                            print(f"✓ Password set for user '{username}'")
                            return True
                    except urllib.error.HTTPError as e:
                        print(f"⚠ User created but failed to set password: {e.code}")
                        return False
                else:
                    print(f"⚠ User created but could not retrieve user ID")
                    return False
        except urllib.error.HTTPError as e:
            print(f"⚠ User created but failed to retrieve user details: {e.code}")
            return False
    
    return False

def main():
    if len(sys.argv) != 7:
        print("Usage: python3 import-realm-via-api.py <keycloak_url> <admin_user> <admin_pass> <realm_file> <test_user> <test_pass>")
        sys.exit(1)
    
    keycloak_url, admin_user, admin_pass, realm_file, test_user, test_pass = sys.argv[1:7]
    
    try:
        print("🚀 Starting Keycloak realm import...")
        
        # Get admin token
        print("🔐 Obtaining admin token...")
        token = get_admin_token(keycloak_url, admin_user, admin_pass)
        
        # Import realm
        print("📥 Importing realm...")
        if import_realm(keycloak_url, token, realm_file):
            
            # Read realm data to get realm name
            with open(realm_file, 'r') as f:
                realm_data = json.load(f)
            realm_name = realm_data.get('realm', 'unknown')
            
            # Create test user
            print(f"👤 Creating test user in realm '{realm_name}'...")
            create_user(keycloak_url, token, realm_name, test_user, test_pass, 
                       f"{test_user}@durvalcrm.org", "Tesouraria", "DurvalCRM")
            
            print("✅ Keycloak realm import completed successfully!")
            sys.exit(0)
        else:
            print("❌ Realm import failed!")
            sys.exit(1)
            
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        sys.exit(1)

if __name__ == '__main__':
    main()