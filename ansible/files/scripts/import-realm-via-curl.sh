#!/bin/bash

# =============================================================================
# Keycloak Realm Import Script using only curl
# =============================================================================
# Description: Imports Keycloak realm and creates user using pure bash/curl
# Usage: ./import-realm-via-curl.sh <keycloak_url> <admin_user> <admin_pass> <realm_file> <test_user> <test_pass>
# =============================================================================

set -e

# Configuration from arguments
KEYCLOAK_URL="${1}"
ADMIN_USER="${2}"
ADMIN_PASS="${3}"
REALM_FILE="${4}"
TEST_USER="${5}"
TEST_PASS="${6}"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Validate arguments
if [ $# -ne 6 ]; then
    log_error "Usage: $0 <keycloak_url> <admin_user> <admin_pass> <realm_file> <test_user> <test_pass>"
    exit 1
fi

# Check if realm file exists
if [ ! -f "$REALM_FILE" ]; then
    log_error "Realm file not found: $REALM_FILE"
    exit 1
fi

log_info "🚀 Starting Keycloak realm import via curl..."

# Step 1: Get admin token
log_info "🔐 Obtaining admin token..."
TOKEN_RESPONSE=$(curl -k -s -X POST \
    "${KEYCLOAK_URL}/realms/master/protocol/openid-connect/token" \
    -H "Content-Type: application/x-www-form-urlencoded" \
    -d "grant_type=password" \
    -d "client_id=admin-cli" \
    -d "username=${ADMIN_USER}" \
    -d "password=${ADMIN_PASS}")

if [ $? -ne 0 ]; then
    log_error "Failed to get admin token"
    exit 1
fi

# Extract access token
ACCESS_TOKEN=$(echo "$TOKEN_RESPONSE" | grep -o '"access_token":"[^"]*' | cut -d'"' -f4)

if [ -z "$ACCESS_TOKEN" ]; then
    log_error "Could not extract access token from response"
    log_error "Response: $TOKEN_RESPONSE"
    exit 1
fi

log_success "Access token obtained successfully"

# Step 2: Import realm
log_info "📥 Importing realm..."

# Import realm using curl with explicit headers
IMPORT_RESPONSE=$(curl -k -s -X POST \
    "${KEYCLOAK_URL}/admin/realms" \
    -H "Authorization: Bearer ${ACCESS_TOKEN}" \
    -H "Content-Type: application/json; charset=utf-8" \
    -H "Accept: application/json" \
    -H "User-Agent: Keycloak-Import-Script/1.0" \
    --data-binary @"${REALM_FILE}" \
    -w "HTTPSTATUS:%{http_code}")

# Extract HTTP status code
HTTP_STATUS=$(echo "$IMPORT_RESPONSE" | grep -o "HTTPSTATUS:[0-9]*" | cut -d: -f2)
RESPONSE_BODY=$(echo "$IMPORT_RESPONSE" | sed -E 's/HTTPSTATUS:[0-9]*$//')

if [ "$HTTP_STATUS" = "201" ]; then
    log_success "Realm imported successfully"
elif [ "$HTTP_STATUS" = "409" ]; then
    log_success "Realm already exists - continuing..."
else
    log_error "Failed to import realm (HTTP $HTTP_STATUS)"
    log_error "Response: $RESPONSE_BODY"
    exit 1
fi

# Step 3: Get realm name from file
REALM_NAME=$(grep -o '"realm"\s*:\s*"[^"]*' "$REALM_FILE" | cut -d'"' -f4)

if [ -z "$REALM_NAME" ]; then
    log_error "Could not extract realm name from file"
    exit 1
fi

log_info "Working with realm: $REALM_NAME"

# Step 4: Check if user already exists
log_info "👤 Checking if user exists..."

USER_SEARCH_RESPONSE=$(curl -k -s -X GET \
    "${KEYCLOAK_URL}/admin/realms/${REALM_NAME}/users?username=${TEST_USER}" \
    -H "Authorization: Bearer ${ACCESS_TOKEN}" \
    -w "HTTPSTATUS:%{http_code}")

USER_HTTP_STATUS=$(echo "$USER_SEARCH_RESPONSE" | grep -o "HTTPSTATUS:[0-9]*" | cut -d: -f2)
USER_SEARCH_BODY=$(echo "$USER_SEARCH_RESPONSE" | sed -E 's/HTTPSTATUS:[0-9]*$//')

if [ "$USER_HTTP_STATUS" = "200" ]; then
    # Check if user array is empty (no users found)
    if [ "$USER_SEARCH_BODY" = "[]" ]; then
        USER_EXISTS=false
        log_info "User does not exist - will create"
    else
        USER_EXISTS=true
        # Extract user ID for password update
        USER_ID=$(echo "$USER_SEARCH_BODY" | grep -o '"id":"[^"]*' | head -1 | cut -d'"' -f4)
        log_info "User already exists - will update password"
    fi
else
    log_error "Failed to search for user (HTTP $USER_HTTP_STATUS)"
    exit 1
fi

# Step 5: Create user if doesn't exist
if [ "$USER_EXISTS" = false ]; then
    log_info "Creating user: $TEST_USER"
    
    USER_DATA=$(cat <<EOF
{
    "username": "${TEST_USER}",
    "firstName": "Tesouraria",
    "lastName": "DurvalCRM",
    "email": "${TEST_USER}@durvalcrm.org",
    "enabled": true,
    "emailVerified": true
}
EOF
)

    CREATE_RESPONSE=$(curl -k -s -X POST \
        "${KEYCLOAK_URL}/admin/realms/${REALM_NAME}/users" \
        -H "Authorization: Bearer ${ACCESS_TOKEN}" \
        -H "Content-Type: application/json; charset=utf-8" \
        -H "Accept: application/json" \
        --data-raw "$USER_DATA" \
        -w "HTTPSTATUS:%{http_code}")

    CREATE_HTTP_STATUS=$(echo "$CREATE_RESPONSE" | grep -o "HTTPSTATUS:[0-9]*" | cut -d: -f2)

    if [ "$CREATE_HTTP_STATUS" = "201" ]; then
        log_success "User created successfully"
        
        # Get the created user ID
        USER_SEARCH_RESPONSE=$(curl -k -s -X GET \
            "${KEYCLOAK_URL}/admin/realms/${REALM_NAME}/users?username=${TEST_USER}" \
            -H "Authorization: Bearer ${ACCESS_TOKEN}")
        
        USER_ID=$(echo "$USER_SEARCH_RESPONSE" | grep -o '"id":"[^"]*' | head -1 | cut -d'"' -f4)
    else
        log_error "Failed to create user (HTTP $CREATE_HTTP_STATUS)"
        exit 1
    fi
fi

# Step 6: Set password
if [ -n "$USER_ID" ]; then
    log_info "Setting password for user: $TEST_USER"
    
    PASSWORD_DATA=$(cat <<EOF
{
    "type": "password",
    "value": "${TEST_PASS}",
    "temporary": false
}
EOF
)

    PASSWORD_RESPONSE=$(curl -k -s -X PUT \
        "${KEYCLOAK_URL}/admin/realms/${REALM_NAME}/users/${USER_ID}/reset-password" \
        -H "Authorization: Bearer ${ACCESS_TOKEN}" \
        -H "Content-Type: application/json; charset=utf-8" \
        -H "Accept: application/json" \
        --data-raw "$PASSWORD_DATA" \
        -w "HTTPSTATUS:%{http_code}")

    PASSWORD_HTTP_STATUS=$(echo "$PASSWORD_RESPONSE" | grep -o "HTTPSTATUS:[0-9]*" | cut -d: -f2)

    if [ "$PASSWORD_HTTP_STATUS" = "204" ]; then
        log_success "Password set successfully"
    else
        log_warning "Failed to set password (HTTP $PASSWORD_HTTP_STATUS)"
    fi
else
    log_error "Could not get user ID"
    exit 1
fi

# Step 7: Test authentication
log_info "🧪 Testing user authentication..."

AUTH_TEST_RESPONSE=$(curl -k -s -X POST \
    "${KEYCLOAK_URL}/realms/${REALM_NAME}/protocol/openid-connect/token" \
    -H "Content-Type: application/x-www-form-urlencoded" \
    -d "grant_type=password" \
    -d "client_id=account" \
    -d "username=${TEST_USER}" \
    -d "password=${TEST_PASS}" \
    -w "HTTPSTATUS:%{http_code}")

AUTH_HTTP_STATUS=$(echo "$AUTH_TEST_RESPONSE" | grep -o "HTTPSTATUS:[0-9]*" | cut -d: -f2)

if [ "$AUTH_HTTP_STATUS" = "200" ]; then
    log_success "User authentication test PASSED"
else
    log_warning "User authentication test failed (HTTP $AUTH_HTTP_STATUS) - but user was created"
fi

log_success "✅ Keycloak realm import completed successfully!"

echo ""
echo "=========================================="
echo "Import Summary:"
echo "=========================================="
echo "✅ Realm: $REALM_NAME"
echo "✅ User: $TEST_USER"  
echo "✅ Password: $TEST_PASS"
echo "🌐 Admin Console: ${KEYCLOAK_URL}/admin/"
echo "🌐 Realm URL: ${KEYCLOAK_URL}/realms/${REALM_NAME}"
echo "=========================================="

exit 0