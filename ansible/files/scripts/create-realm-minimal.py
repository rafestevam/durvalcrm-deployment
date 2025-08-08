#!/usr/bin/env python3
"""
Script to create minimal Keycloak realm and client via REST API
This script creates a basic realm and client instead of importing a large JSON
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

def create_minimal_realm(keycloak_url, token, realm_name):
    """Create minimal realm via API"""
    realms_url = f"{keycloak_url}/admin/realms"
    
    # Minimal realm definition
    realm_data = {
        "realm": realm_name,
        "enabled": True,
        "sslRequired": "external",
        "registrationAllowed": False,
        "loginWithEmailAllowed": True,
        "duplicateEmailsAllowed": False,
        "resetPasswordAllowed": True,
        "editUsernameAllowed": False,
        "bruteForceProtected": False,
        "accessTokenLifespan": 1800,
        "ssoSessionIdleTimeout": 1800,
        "ssoSessionMaxLifespan": 36000,
        "roles": {
            "realm": [
                {
                    "name": "user",
                    "description": "Standard user role",
                    "composite": False
                },
                {
                    "name": "admin", 
                    "description": "Administrative role",
                    "composite": False
                }
            ]
        }
    }
    
    # Prepare JSON data
    json_data = json.dumps(realm_data, separators=(',', ':')).encode('utf-8')
    
    # Create request
    req = urllib.request.Request(realms_url, data=json_data)
    req.add_header('Authorization', f'Bearer {token}')
    req.add_header('Content-Type', 'application/json; charset=utf-8')
    req.add_header('Content-Length', str(len(json_data)))
    req.add_header('Accept', 'application/json')
    
    try:
        with urllib.request.urlopen(req, context=ssl_context) as response:
            print(f"✓ Realm '{realm_name}' created successfully")
            return True
    except urllib.error.HTTPError as e:
        if e.code == 409:
            print(f"ℹ Realm '{realm_name}' already exists")
            return True
        else:
            print(f"✗ Failed to create realm: {e.code} - {e.read().decode()}")
            return False

def create_client(keycloak_url, token, realm_name, client_id):
    """Create client in realm"""
    clients_url = f"{keycloak_url}/admin/realms/{realm_name}/clients"
    
    client_data = {
        "clientId": client_id,
        "name": "DurvalCRM Application Client",
        "description": "Client for DurvalCRM J2EE application",
        "enabled": True,
        "clientAuthenticatorType": "client-secret",
        "redirectUris": [
            "https://20.127.155.169:8443/*",
            "https://localhost:8443/*",
            "http://localhost:8080/*"
        ],
        "webOrigins": [
            "https://20.127.155.169:8443",
            "https://localhost:8443", 
            "http://localhost:8080"
        ],
        "publicClient": False,
        "bearerOnly": False,
        "standardFlowEnabled": True,
        "implicitFlowEnabled": False,
        "directAccessGrantsEnabled": True,
        "serviceAccountsEnabled": True,
        "consentRequired": False,
        "frontchannelLogout": True,
        "protocol": "openid-connect",
        "attributes": {
            "saml.assertion.signature": "false",
            "saml.force.post.binding": "false", 
            "saml.multivalued.roles": "false",
            "saml.encrypt": "false",
            "saml.server.signature": "false",
            "saml.server.signature.keyinfo.ext": "false",
            "exclude.session.state.from.auth.response": "false",
            "saml_force_name_id_format": "false",
            "saml.client.signature": "false",
            "tls.client.certificate.bound.access.tokens": "false",
            "saml.authnstatement": "false",
            "display.on.consent.screen": "false",
            "saml.onetimeuse.condition": "false"
        }
    }
    
    # Prepare JSON data
    json_data = json.dumps(client_data, separators=(',', ':')).encode('utf-8')
    
    # Create request
    req = urllib.request.Request(clients_url, data=json_data)
    req.add_header('Authorization', f'Bearer {token}')
    req.add_header('Content-Type', 'application/json; charset=utf-8')
    req.add_header('Content-Length', str(len(json_data)))
    req.add_header('Accept', 'application/json')
    
    try:
        with urllib.request.urlopen(req, context=ssl_context) as response:
            print(f"✓ Client '{client_id}' created successfully")
            return True
    except urllib.error.HTTPError as e:
        if e.code == 409:
            print(f"ℹ Client '{client_id}' already exists")
            return True
        else:
            print(f"✗ Failed to create client: {e.code} - {e.read().decode()}")
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
    json_data = json.dumps(user_data, separators=(',', ':')).encode('utf-8')
    
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
        # Get user ID and set password (same as original script)
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
                    
                    json_data = json.dumps(password_data, separators=(',', ':')).encode('utf-8')
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
    if len(sys.argv) != 8:
        print("Usage: python3 create-realm-minimal.py <keycloak_url> <admin_user> <admin_pass> <realm_name> <client_id> <test_user> <test_pass>")
        sys.exit(1)
    
    keycloak_url, admin_user, admin_pass, realm_name, client_id, test_user, test_pass = sys.argv[1:8]
    
    try:
        print("🚀 Starting minimal Keycloak realm creation...")
        
        # Get admin token
        print("🔐 Obtaining admin token...")
        token = get_admin_token(keycloak_url, admin_user, admin_pass)
        
        # Create minimal realm
        print(f"📦 Creating minimal realm '{realm_name}'...")
        if create_minimal_realm(keycloak_url, token, realm_name):
            
            # Create client
            print(f"🔧 Creating client '{client_id}'...")
            create_client(keycloak_url, token, realm_name, client_id)
            
            # Create test user
            print(f"👤 Creating test user '{test_user}'...")
            create_user(keycloak_url, token, realm_name, test_user, test_pass,
                       f"{test_user}@durvalcrm.org", "Tesouraria", "DurvalCRM")
            
            print("✅ Minimal Keycloak realm creation completed successfully!")
            sys.exit(0)
        else:
            print("❌ Realm creation failed!")
            sys.exit(1)
            
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        sys.exit(1)

if __name__ == '__main__':
    main()