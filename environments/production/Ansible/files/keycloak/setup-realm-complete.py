#!/usr/bin/env python3
"""
Complete Keycloak Realm Setup Script
Creates durval-crm realm with proper configuration for production
"""

import json
import requests
import time
import sys
from requests.packages.urllib3.exceptions import InsecureRequestWarning

# Disable SSL warnings for localhost testing
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

class KeycloakAdmin:
    def __init__(self, base_url="http://localhost:8090", admin_user="admin", admin_password="admin"):
        self.base_url = base_url
        self.admin_user = admin_user
        self.admin_password = admin_password
        self.access_token = None
        
    def get_admin_token(self):
        """Get admin access token"""
        token_url = f"{self.base_url}/realms/master/protocol/openid-connect/token"
        data = {
            'client_id': 'admin-cli',
            'username': self.admin_user,
            'password': self.admin_password,
            'grant_type': 'password'
        }
        
        response = requests.post(token_url, data=data, verify=False)
        if response.status_code == 200:
            self.access_token = response.json()['access_token']
            return True
        else:
            print(f"Failed to get admin token: {response.status_code} - {response.text}")
            return False
    
    def headers(self):
        """Get authorization headers"""
        return {
            'Authorization': f'Bearer {self.access_token}',
            'Content-Type': 'application/json'
        }
    
    def delete_realm(self, realm_name):
        """Delete existing realm if it exists"""
        url = f"{self.base_url}/admin/realms/{realm_name}"
        response = requests.delete(url, headers=self.headers(), verify=False)
        if response.status_code in [204, 404]:
            print(f"✅ Realm {realm_name} deleted or didn't exist")
            return True
        else:
            print(f"❌ Failed to delete realm: {response.status_code} - {response.text}")
            return False
    
    def create_realm(self, realm_name):
        """Create new realm with proper configuration"""
        realm_config = {
            "realm": realm_name,
            "enabled": True,
            "displayName": "Durval CRM",
            "displayNameHtml": "<strong>Durval CRM</strong>",
            "loginWithEmailAllowed": True,
            "duplicateEmailsAllowed": False,
            "resetPasswordAllowed": True,
            "editUsernameAllowed": False,
            "bruteForceProtected": True,
            "permanentLockout": False,
            "maxFailureWaitSeconds": 900,
            "minimumQuickLoginWaitSeconds": 60,
            "waitIncrementSeconds": 60,
            "quickLoginCheckMilliSeconds": 1000,
            "maxDeltaTimeSeconds": 43200,
            "failureFactor": 30,
            "roles": {
                "realm": [
                    {
                        "name": "user",
                        "description": "User role",
                        "composite": False,
                        "clientRole": False,
                        "containerId": realm_name
                    },
                    {
                        "name": "admin",
                        "description": "Admin role",
                        "composite": False,
                        "clientRole": False,
                        "containerId": realm_name
                    }
                ]
            },
            "defaultRoles": ["user"],
            "requiredCredentials": ["password"],
            "passwordPolicy": "length(8)",
            "otpPolicyType": "totp",
            "otpPolicyAlgorithm": "HmacSHA1",
            "otpPolicyInitialCounter": 0,
            "otpPolicyDigits": 6,
            "otpPolicyLookAheadWindow": 1,
            "otpPolicyPeriod": 30,
            "browserFlow": "browser",
            "registrationFlow": "registration",
            "directGrantFlow": "direct grant",
            "resetCredentialsFlow": "reset credentials",
            "clientAuthenticationFlow": "clients",
            "attributes": {
                "frontendUrl": "https://admin.durvalcrm.org",
                "hostname": "admin.durvalcrm.org",
                "hostnameStrict": "false",
                "hostnameStrictHttps": "false"
            }
        }
        
        url = f"{self.base_url}/admin/realms"
        response = requests.post(url, headers=self.headers(), json=realm_config, verify=False)
        if response.status_code == 201:
            print(f"✅ Realm {realm_name} created successfully")
            return True
        else:
            print(f"❌ Failed to create realm: {response.status_code} - {response.text}")
            return False
    
    def create_client(self, realm_name, client_config):
        """Create client in realm"""
        url = f"{self.base_url}/admin/realms/{realm_name}/clients"
        response = requests.post(url, headers=self.headers(), json=client_config, verify=False)
        if response.status_code == 201:
            print(f"✅ Client {client_config['clientId']} created successfully")
            return True
        else:
            print(f"❌ Failed to create client: {response.status_code} - {response.text}")
            return False
    
    def create_user(self, realm_name, user_config):
        """Create user in realm"""
        url = f"{self.base_url}/admin/realms/{realm_name}/users"
        response = requests.post(url, headers=self.headers(), json=user_config, verify=False)
        if response.status_code == 201:
            print(f"✅ User {user_config['username']} created successfully")
            
            # Get user ID from Location header
            user_location = response.headers.get('Location')
            user_id = user_location.split('/')[-1]
            
            return user_id
        else:
            print(f"❌ Failed to create user: {response.status_code} - {response.text}")
            return None
    
    def set_user_password(self, realm_name, user_id, password):
        """Set user password"""
        url = f"{self.base_url}/admin/realms/{realm_name}/users/{user_id}/reset-password"
        password_config = {
            "type": "password",
            "value": password,
            "temporary": False
        }
        response = requests.put(url, headers=self.headers(), json=password_config, verify=False)
        if response.status_code == 204:
            print("✅ User password set successfully")
            return True
        else:
            print(f"❌ Failed to set password: {response.status_code} - {response.text}")
            return False

def main():
    print("🚀 Starting Keycloak Realm Setup...")
    
    # Initialize Keycloak admin
    kc = KeycloakAdmin()
    
    # Wait for Keycloak to be ready
    print("⏳ Waiting for Keycloak to be ready...")
    for i in range(30):
        try:
            response = requests.get(f"{kc.base_url}/realms/master", verify=False, timeout=5)
            if response.status_code == 200:
                print("✅ Keycloak is ready!")
                break
        except:
            pass
        time.sleep(2)
        print(f"   Attempt {i+1}/30...")
    else:
        print("❌ Keycloak not ready after 60 seconds")
        sys.exit(1)
    
    # Get admin token
    print("🔑 Getting admin access token...")
    if not kc.get_admin_token():
        print("❌ Failed to get admin token")
        sys.exit(1)
    print("✅ Admin token obtained")
    
    # Delete existing realm if it exists
    print("🗑️  Deleting existing realm (if exists)...")
    kc.delete_realm("durval-crm")
    
    # Create new realm
    print("🏗️  Creating durval-crm realm...")
    if not kc.create_realm("durval-crm"):
        sys.exit(1)
    
    # Create client
    print("📱 Creating durvalcrm-app client...")
    client_config = {
        "clientId": "durvalcrm-app",
        "name": "DurvalCRM Application",
        "description": "DurvalCRM Vue.js Frontend Application",
        "enabled": True,
        "publicClient": True,
        "standardFlowEnabled": True,
        "implicitFlowEnabled": False,
        "directAccessGrantsEnabled": False,
        "serviceAccountsEnabled": False,
        "protocol": "openid-connect",
        "fullScopeAllowed": True,
        "nodeReRegistrationTimeout": 0,
        "protocolMappers": [],
        "defaultClientScopes": ["web-origins", "role_list", "profile", "roles", "email"],
        "optionalClientScopes": ["address", "phone", "offline_access", "microprofile-jwt"],
        "redirectUris": [
            "https://crm.durvalcrm.org/auth/callback",
            "https://crm.durvalcrm.org/crm/auth/callback",
            "https://crm.durvalcrm.org/*"
        ],
        "webOrigins": [
            "https://crm.durvalcrm.org"
        ],
        "attributes": {
            "pkce.code.challenge.method": "S256",
            "post.logout.redirect.uris": "https://crm.durvalcrm.org/*",
            "oauth2.device.authorization.grant.enabled": "false",
            "backchannel.logout.session.required": "true",
            "backchannel.logout.revoke.offline.tokens": "false"
        }
    }
    
    if not kc.create_client("durval-crm", client_config):
        sys.exit(1)
    
    # Create test user
    print("👤 Creating tesouraria user...")
    user_config = {
        "username": "tesouraria",
        "enabled": True,
        "emailVerified": True,
        "firstName": "Tesoureiro",
        "lastName": "Sistema",
        "email": "tesouraria@durvalcrm.org",
        "attributes": {},
        "groups": [],
        "realmRoles": ["user"],
        "clientRoles": {}
    }
    
    user_id = kc.create_user("durval-crm", user_config)
    if not user_id:
        sys.exit(1)
    
    # Set user password
    print("🔒 Setting user password...")
    if not kc.set_user_password("durval-crm", user_id, "cairbar@2025"):
        sys.exit(1)
    
    print("\n🎉 Keycloak setup completed successfully!")
    print("📋 Summary:")
    print("   - Realm: durval-crm")
    print("   - Client: durvalcrm-app (PKCE enabled)")
    print("   - User: tesouraria / cairbar@2025")
    print("   - Redirect URIs:")
    print("     * https://crm.durvalcrm.org/auth/callback")
    print("     * https://crm.durvalcrm.org/crm/auth/callback")
    print("\n🧪 Ready for testing!")

if __name__ == "__main__":
    main()