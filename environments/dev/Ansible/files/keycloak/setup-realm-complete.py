#!/usr/bin/env python3
"""
Complete Keycloak Realm Setup Script for Development
Creates durval-crm realm with proper configuration for local development
"""

import json
import requests
import time
import sys
import os
from requests.packages.urllib3.exceptions import InsecureRequestWarning

# Disable SSL warnings for localhost testing
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

# Get configuration from environment variables or use defaults
KEYCLOAK_URL = os.environ.get('KEYCLOAK_URL', 'http://localhost:8090')
APP_BASE_URL_LOCALHOST = os.environ.get('APP_BASE_URL_LOCALHOST', 'http://localhost:9080')
APP_BASE_URL_127 = os.environ.get('APP_BASE_URL_127', 'http://127.0.0.1:9080')
APP_CONTEXT_PATH = os.environ.get('APP_CONTEXT_PATH', '/crm')

class KeycloakAdmin:
    def __init__(self, base_url=KEYCLOAK_URL, admin_user="admin", admin_password="admin"):
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
        """Create new realm with proper configuration for development"""
        realm_config = {
            "realm": realm_name,
            "enabled": True,
            "displayName": "Durval CRM - Development",
            "displayNameHtml": "<strong>Durval CRM</strong> <span style='color: #f59e0b;'>[DEV]</span>",
            "loginWithEmailAllowed": True,
            "duplicateEmailsAllowed": False,
            "resetPasswordAllowed": True,
            "editUsernameAllowed": False,
            "bruteForceProtected": False,  # Disabled for dev
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
                "frontendUrl": "",
                "hostname": "",
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
    print("🚀 Starting Keycloak Realm Setup for Development...")
    print(f"📍 Keycloak URL: {KEYCLOAK_URL}")
    print(f"📍 App Base URL (localhost): {APP_BASE_URL_LOCALHOST}")
    print(f"📍 App Base URL (127.0.0.1): {APP_BASE_URL_127}")
    print(f"📍 App Context Path: {APP_CONTEXT_PATH}")

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
        except Exception as e:
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

    # Create client with development redirect URIs
    print("📱 Creating durvalcrm-app client...")
    redirect_uris = [
        f"{APP_BASE_URL_LOCALHOST}{APP_CONTEXT_PATH}/auth/callback",
        f"{APP_BASE_URL_127}{APP_CONTEXT_PATH}/auth/callback",
        f"{APP_BASE_URL_LOCALHOST}{APP_CONTEXT_PATH}/*",
        f"{APP_BASE_URL_127}{APP_CONTEXT_PATH}/*",
        # Add root context as well
        f"{APP_BASE_URL_LOCALHOST}/auth/callback",
        f"{APP_BASE_URL_127}/auth/callback",
    ]

    web_origins = [
        APP_BASE_URL_LOCALHOST,
        APP_BASE_URL_127,
        "http://localhost:5173",  # Vite dev server
        "http://127.0.0.1:5173",
    ]

    client_config = {
        "clientId": "durvalcrm-app",
        "name": "DurvalCRM Application - Development",
        "description": "DurvalCRM Vue.js Frontend Application - Development Environment",
        "enabled": True,
        "publicClient": True,
        "standardFlowEnabled": True,
        "implicitFlowEnabled": False,
        "directAccessGrantsEnabled": True,  # Enabled for dev testing
        "serviceAccountsEnabled": False,
        "protocol": "openid-connect",
        "fullScopeAllowed": True,
        "nodeReRegistrationTimeout": 0,
        "protocolMappers": [],
        "defaultClientScopes": ["web-origins", "role_list", "profile", "roles", "email"],
        "optionalClientScopes": ["address", "phone", "offline_access", "microprofile-jwt"],
        "redirectUris": redirect_uris,
        "webOrigins": web_origins,
        "attributes": {
            "pkce.code.challenge.method": "S256",
            "post.logout.redirect.uris": "+",  # Allow all configured redirect URIs
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
        "email": "tesouraria@localhost",
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

    print("\n" + "="*60)
    print("🎉 Keycloak setup completed successfully!")
    print("="*60)
    print("\n📋 Summary:")
    print(f"   • Environment: Development")
    print(f"   • Keycloak URL: {KEYCLOAK_URL}")
    print(f"   • Realm: durval-crm")
    print(f"   • Client: durvalcrm-app (PKCE enabled)")
    print(f"   • User: tesouraria / cairbar@2025")
    print(f"\n🔗 Redirect URIs:")
    for uri in redirect_uris:
        print(f"     ✓ {uri}")
    print(f"\n🌐 Web Origins:")
    for origin in web_origins:
        print(f"     ✓ {origin}")
    print(f"\n🔐 Access:")
    print(f"   • Admin Console: {KEYCLOAK_URL}/admin")
    print(f"   • User Account: {KEYCLOAK_URL}/realms/durval-crm/account")
    print(f"   • Frontend App: {APP_BASE_URL_LOCALHOST}{APP_CONTEXT_PATH}/")
    print("\n🧪 Ready for development testing!")
    print("="*60)

if __name__ == "__main__":
    main()
