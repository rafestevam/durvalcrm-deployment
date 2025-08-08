#!/bin/bash

# =============================================================================
# DurvalCRM Keycloak Integration Test Script
# =============================================================================
# Description: Tests the Keycloak integration with WildFly application
# Usage: ./test-keycloak-integration.sh
# =============================================================================

set -e

# Configuration
KEYCLOAK_BASE_URL="https://20.127.155.169:9443"
WILDFLY_BASE_URL="https://20.127.155.169:8443"
REALM="durval-crm"
CLIENT_ID="durvalcrm-app"
TEST_USER="tesouraria"
TEST_PASSWORD="cairbar@2025"
APPLICATION_NAME="durvalcrm-j2ee"

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

# Test functions
test_keycloak_availability() {
    log_info "Testing Keycloak availability..."
    
    if curl -k -s -o /dev/null -w "%{http_code}" "${KEYCLOAK_BASE_URL}/" | grep -q "200\|302\|404"; then
        log_success "Keycloak is accessible at ${KEYCLOAK_BASE_URL}"
        return 0
    else
        log_error "Keycloak is not accessible at ${KEYCLOAK_BASE_URL}"
        return 1
    fi
}

test_realm_configuration() {
    log_info "Testing realm configuration..."
    
    local oidc_config_url="${KEYCLOAK_BASE_URL}/realms/${REALM}/.well-known/openid-configuration"
    
    if curl -k -s "${oidc_config_url}" | jq -r '.issuer' | grep -q "${REALM}"; then
        log_success "Realm '${REALM}' is properly configured"
        return 0
    else
        log_error "Realm '${REALM}' configuration test failed"
        return 1
    fi
}

test_user_authentication() {
    log_info "Testing user authentication..."
    
    local token_url="${KEYCLOAK_BASE_URL}/realms/${REALM}/protocol/openid-connect/token"
    
    local response=$(curl -k -s -X POST "${token_url}" \
        -H "Content-Type: application/x-www-form-urlencoded" \
        -d "grant_type=password" \
        -d "client_id=${CLIENT_ID}" \
        -d "username=${TEST_USER}" \
        -d "password=${TEST_PASSWORD}")
    
    if echo "${response}" | jq -r '.access_token' | grep -q "^eyJ"; then
        log_success "User authentication successful for ${TEST_USER}"
        
        # Extract token for further tests
        ACCESS_TOKEN=$(echo "${response}" | jq -r '.access_token')
        export ACCESS_TOKEN
        return 0
    else
        log_error "User authentication failed for ${TEST_USER}"
        log_error "Response: ${response}"
        return 1
    fi
}

test_wildfly_availability() {
    log_info "Testing WildFly availability..."
    
    if curl -k -s -o /dev/null -w "%{http_code}" "${WILDFLY_BASE_URL}" | grep -q "200\|302\|404"; then
        log_success "WildFly is accessible at ${WILDFLY_BASE_URL}"
        return 0
    else
        log_error "WildFly is not accessible at ${WILDFLY_BASE_URL}"
        return 1
    fi
}

test_application_deployment() {
    log_info "Testing application deployment..."
    
    local app_url="${WILDFLY_BASE_URL}/${APPLICATION_NAME}/api/health"
    
    if curl -k -s "${app_url}" | grep -q "UP\|OK\|SUCCESS"; then
        log_success "Application is deployed and responding"
        return 0
    else
        log_warning "Application may not be deployed yet or health endpoint not available"
        return 1
    fi
}

test_protected_endpoint_without_token() {
    log_info "Testing protected endpoint without token (should fail)..."
    
    local protected_url="${WILDFLY_BASE_URL}/${APPLICATION_NAME}/api/associados"
    local status_code=$(curl -k -s -o /dev/null -w "%{http_code}" "${protected_url}")
    
    if [ "${status_code}" = "401" ] || [ "${status_code}" = "403" ] || [ "${status_code}" = "302" ]; then
        log_success "Protected endpoint correctly rejects unauthenticated requests (HTTP ${status_code})"
        return 0
    else
        log_warning "Protected endpoint returned unexpected status: ${status_code}"
        return 1
    fi
}

test_protected_endpoint_with_token() {
    log_info "Testing protected endpoint with valid token..."
    
    if [ -z "${ACCESS_TOKEN}" ]; then
        log_error "No access token available for testing"
        return 1
    fi
    
    local protected_url="${WILDFLY_BASE_URL}/${APPLICATION_NAME}/api/associados"
    local response=$(curl -k -s -H "Authorization: Bearer ${ACCESS_TOKEN}" "${protected_url}")
    local status_code=$(curl -k -s -o /dev/null -w "%{http_code}" -H "Authorization: Bearer ${ACCESS_TOKEN}" "${protected_url}")
    
    if [ "${status_code}" = "200" ]; then
        log_success "Protected endpoint accepts authenticated requests (HTTP ${status_code})"
        return 0
    elif [ "${status_code}" = "404" ]; then
        log_warning "Protected endpoint not found - application may not be fully deployed"
        return 1
    else
        log_error "Protected endpoint test failed (HTTP ${status_code})"
        log_error "Response: ${response}"
        return 1
    fi
}

test_keycloak_adapter_installation() {
    log_info "Testing Keycloak adapter installation in WildFly..."
    
    # This test checks if the Keycloak subsystem is available in WildFly
    # We do this by checking if the management interface responds to Keycloak-specific operations
    local mgmt_url="https://20.127.155.169:9990/management"
    
    if curl -k -s --digest -u "admin:wildfly@2025" "${mgmt_url}" \
        -H "Content-Type: application/json" \
        -d '{"operation":"read-children-names","address":[],"child-type":"subsystem"}' \
        | jq -r '.result[]' | grep -q "keycloak"; then
        log_success "Keycloak adapter is installed in WildFly"
        return 0
    else
        log_warning "Keycloak adapter may not be installed or configured in WildFly"
        return 1
    fi
}

generate_test_report() {
    log_info "Generating integration test report..."
    
    cat > "/tmp/keycloak-integration-test-report.txt" << EOF
DurvalCRM Keycloak Integration Test Report
========================================
Date: $(date)
Test Environment: ${KEYCLOAK_BASE_URL}

Test Results:
- Keycloak Availability: ${KEYCLOAK_TEST:-FAILED}
- Realm Configuration: ${REALM_TEST:-FAILED}
- User Authentication: ${AUTH_TEST:-FAILED}
- WildFly Availability: ${WILDFLY_TEST:-FAILED}
- Application Deployment: ${APP_TEST:-FAILED}
- Protected Endpoint (No Auth): ${PROTECTED_NO_AUTH_TEST:-FAILED}
- Protected Endpoint (With Auth): ${PROTECTED_WITH_AUTH_TEST:-FAILED}
- Keycloak Adapter: ${ADAPTER_TEST:-FAILED}

Configuration Details:
- Keycloak URL: ${KEYCLOAK_BASE_URL}
- WildFly URL: ${WILDFLY_BASE_URL}
- Realm: ${REALM}
- Client ID: ${CLIENT_ID}
- Test User: ${TEST_USER}
- Application: ${APPLICATION_NAME}

Next Steps:
1. If tests are failing, check service status and logs
2. Verify network connectivity and firewall rules
3. Ensure all configuration files are properly deployed
4. Check Keycloak realm and client configuration
5. Verify WildFly Keycloak adapter installation

Troubleshooting Commands:
- Check Keycloak logs: journalctl -u keycloak -f
- Check WildFly logs: tail -f /opt/wildfly/standalone/log/server.log
- Test connectivity: curl -k ${KEYCLOAK_BASE_URL}/
- Check services: systemctl status keycloak wildfly
EOF

    log_info "Test report saved to /tmp/keycloak-integration-test-report.txt"
}

# Main test execution
main() {
    echo "=========================================="
    echo "DurvalCRM Keycloak Integration Test Suite"
    echo "=========================================="
    echo ""
    
    # Initialize test results
    KEYCLOAK_TEST="FAILED"
    REALM_TEST="FAILED"
    AUTH_TEST="FAILED"
    WILDFLY_TEST="FAILED"
    APP_TEST="FAILED"
    PROTECTED_NO_AUTH_TEST="FAILED"
    PROTECTED_WITH_AUTH_TEST="FAILED"
    ADAPTER_TEST="FAILED"
    
    # Run tests
    if test_keycloak_availability; then
        KEYCLOAK_TEST="PASSED"
    fi
    
    if test_realm_configuration; then
        REALM_TEST="PASSED"
    fi
    
    if test_user_authentication; then
        AUTH_TEST="PASSED"
    fi
    
    if test_wildfly_availability; then
        WILDFLY_TEST="PASSED"
    fi
    
    if test_application_deployment; then
        APP_TEST="PASSED"
    fi
    
    if test_protected_endpoint_without_token; then
        PROTECTED_NO_AUTH_TEST="PASSED"
    fi
    
    if test_protected_endpoint_with_token; then
        PROTECTED_WITH_AUTH_TEST="PASSED"
    fi
    
    if test_keycloak_adapter_installation; then
        ADAPTER_TEST="PASSED"
    fi
    
    # Generate report
    generate_test_report
    
    # Summary
    echo ""
    echo "=========================================="
    echo "Test Summary:"
    echo "=========================================="
    echo "✓ Keycloak Availability: ${KEYCLOAK_TEST}"
    echo "✓ Realm Configuration: ${REALM_TEST}"
    echo "✓ User Authentication: ${AUTH_TEST}"
    echo "✓ WildFly Availability: ${WILDFLY_TEST}"
    echo "✓ Application Deployment: ${APP_TEST}"
    echo "✓ Protected Endpoint Security: ${PROTECTED_NO_AUTH_TEST}"
    echo "✓ Authenticated Access: ${PROTECTED_WITH_AUTH_TEST}"
    echo "✓ Keycloak Adapter: ${ADAPTER_TEST}"
    echo ""
    
    # Determine overall result
    if [[ "${KEYCLOAK_TEST}" == "PASSED" && "${REALM_TEST}" == "PASSED" && "${AUTH_TEST}" == "PASSED" ]]; then
        log_success "Core Keycloak integration tests PASSED"
        exit 0
    else
        log_error "Some integration tests FAILED"
        exit 1
    fi
}

# Check dependencies
if ! command -v curl &> /dev/null; then
    log_error "curl is required but not installed"
    exit 1
fi

if ! command -v jq &> /dev/null; then
    log_warning "jq is not installed - some tests may not work properly"
fi

# Run main function
main "$@"