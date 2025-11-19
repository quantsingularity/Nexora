#!/bin/bash
# deploy_fhir.sh - Script to deploy FHIR resources to a FHIR server
#
# This script automates the deployment of FHIR resources (patients, observations,
# conditions, etc.) to a FHIR server. It supports various authentication methods
# and can handle bulk uploads with error handling and reporting.
#
# Usage: ./deploy_fhir.sh --server <fhir_server_url> --resources <resources_dir> [options]

set -e

# Default values
FHIR_SERVER=""
RESOURCES_DIR=""
AUTH_TYPE="none"
AUTH_TOKEN=""
CLIENT_ID=""
CLIENT_SECRET=""
BATCH_SIZE=100
VALIDATE=false
VERBOSE=false
DRY_RUN=false
TIMEOUT=30
LOG_FILE="fhir_deploy_$(date +%Y%m%d_%H%M%S).log"

# Function to display usage information
usage() {
    echo "Usage: $0 [options]"
    echo ""
    echo "Options:"
    echo "  --server URL         FHIR server URL (required)"
    echo "  --resources DIR      Directory containing FHIR resources (required)"
    echo "  --auth-type TYPE     Authentication type: none, token, oauth (default: none)"
    echo "  --token TOKEN        Authentication token for token auth"
    echo "  --client-id ID       OAuth client ID"
    echo "  --client-secret SEC  OAuth client secret"
    echo "  --batch-size N       Number of resources to upload in each batch (default: 100)"
    echo "  --validate           Validate resources before uploading"
    echo "  --verbose            Enable verbose output"
    echo "  --dry-run            Simulate upload without actually sending data"
    echo "  --timeout SEC        Request timeout in seconds (default: 30)"
    echo "  --log-file FILE      Log file path (default: fhir_deploy_YYYYMMDD_HHMMSS.log)"
    echo "  --help               Display this help message"
    echo ""
    echo "Example:"
    echo "  $0 --server https://fhir.example.org/R4 --resources ./fhir_data --auth-type token --token abc123"
    exit 1
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case "$1" in
        --server)
            FHIR_SERVER="$2"
            shift 2
            ;;
        --resources)
            RESOURCES_DIR="$2"
            shift 2
            ;;
        --auth-type)
            AUTH_TYPE="$2"
            shift 2
            ;;
        --token)
            AUTH_TOKEN="$2"
            shift 2
            ;;
        --client-id)
            CLIENT_ID="$2"
            shift 2
            ;;
        --client-secret)
            CLIENT_SECRET="$2"
            shift 2
            ;;
        --batch-size)
            BATCH_SIZE="$2"
            shift 2
            ;;
        --validate)
            VALIDATE=true
            shift
            ;;
        --verbose)
            VERBOSE=true
            shift
            ;;
        --dry-run)
            DRY_RUN=true
            shift
            ;;
        --timeout)
            TIMEOUT="$2"
            shift 2
            ;;
        --log-file)
            LOG_FILE="$2"
            shift 2
            ;;
        --help)
            usage
            ;;
        *)
            echo "Unknown option: $1"
            usage
            ;;
    esac
done

# Validate required parameters
if [[ -z "$FHIR_SERVER" ]]; then
    echo "Error: FHIR server URL is required"
    usage
fi

if [[ -z "$RESOURCES_DIR" ]]; then
    echo "Error: Resources directory is required"
    usage
fi

if [[ ! -d "$RESOURCES_DIR" ]]; then
    echo "Error: Resources directory does not exist: $RESOURCES_DIR"
    exit 1
fi

# Setup logging
log() {
    local level="$1"
    local message="$2"
    local timestamp=$(date +"%Y-%m-%d %H:%M:%S")
    echo "[$timestamp] [$level] $message" | tee -a "$LOG_FILE"

    if [[ "$VERBOSE" == "true" || "$level" != "DEBUG" ]]; then
        echo "[$level] $message"
    fi
}

log "INFO" "Starting FHIR deployment to $FHIR_SERVER"
log "INFO" "Resources directory: $RESOURCES_DIR"
log "INFO" "Authentication type: $AUTH_TYPE"
log "INFO" "Batch size: $BATCH_SIZE"
log "INFO" "Validate resources: $VALIDATE"
log "INFO" "Dry run: $DRY_RUN"

# Get OAuth token if needed
get_oauth_token() {
    if [[ "$AUTH_TYPE" != "oauth" ]]; then
        return
    fi

    if [[ -z "$CLIENT_ID" || -z "$CLIENT_SECRET" ]]; then
        log "ERROR" "OAuth client ID and secret are required for OAuth authentication"
        exit 1
    fi

    log "INFO" "Obtaining OAuth token..."

    # Extract token endpoint from FHIR server metadata
    local token_endpoint
    token_endpoint=$(curl -s "$FHIR_SERVER/metadata" | jq -r '.rest[0].security.extension[] | select(.url=="http://fhir-registry.smarthealthit.org/StructureDefinition/oauth-uris") | .extension[] | select(.url=="token") | .valueUri')

    if [[ -z "$token_endpoint" ]]; then
        log "ERROR" "Could not determine OAuth token endpoint from server metadata"
        exit 1
    fi

    # Request token
    local response
    response=$(curl -s -X POST "$token_endpoint" \
        -d "grant_type=client_credentials" \
        -d "client_id=$CLIENT_ID" \
        -d "client_secret=$CLIENT_SECRET")

    AUTH_TOKEN=$(echo "$response" | jq -r '.access_token')

    if [[ -z "$AUTH_TOKEN" || "$AUTH_TOKEN" == "null" ]]; then
        log "ERROR" "Failed to obtain OAuth token: $response"
        exit 1
    fi

    log "INFO" "OAuth token obtained successfully"
}

# Validate a FHIR resource
validate_resource() {
    local file="$1"
    local resource_type=$(jq -r '.resourceType' "$file")

    if [[ -z "$resource_type" || "$resource_type" == "null" ]]; then
        log "ERROR" "Invalid FHIR resource in $file: Missing resourceType"
        return 1
    fi

    # Additional validation could be added here

    return 0
}

# Upload a single FHIR resource
upload_resource() {
    local file="$1"
    local resource_type=$(jq -r '.resourceType' "$file")
    local id=$(jq -r '.id' "$file")

    # Prepare curl command with appropriate authentication
    local curl_cmd="curl -s -X PUT"

    if [[ "$AUTH_TYPE" == "token" || "$AUTH_TYPE" == "oauth" ]]; then
        curl_cmd="$curl_cmd -H 'Authorization: Bearer $AUTH_TOKEN'"
    fi

    curl_cmd="$curl_cmd -H 'Content-Type: application/fhir+json'"
    curl_cmd="$curl_cmd --connect-timeout $TIMEOUT"
    curl_cmd="$curl_cmd -d @$file"
    curl_cmd="$curl_cmd '$FHIR_SERVER/$resource_type/$id'"

    if [[ "$DRY_RUN" == "true" ]]; then
        log "DEBUG" "Would execute: $curl_cmd"
        return 0
    fi

    # Execute the curl command
    local response
    response=$(eval "$curl_cmd")
    local status=$?

    if [[ $status -ne 0 ]]; then
        log "ERROR" "Failed to upload resource $file: curl error $status"
        return 1
    fi

    # Check for HTTP errors in response
    if echo "$response" | jq -e '.issue[0].severity == "error"' &>/dev/null; then
        local error_msg=$(echo "$response" | jq -r '.issue[0].diagnostics')
        log "ERROR" "Failed to upload resource $file: $error_msg"
        return 1
    fi

    log "DEBUG" "Successfully uploaded $resource_type/$id"
    return 0
}

# Upload resources in batches
upload_batch() {
    local files=("$@")
    local batch_file=$(mktemp)

    # Create batch bundle
    echo '{
        "resourceType": "Bundle",
        "type": "batch",
        "entry": [' > "$batch_file"

    local first=true
    for file in "${files[@]}"; do
        if [[ "$first" != "true" ]]; then
            echo "," >> "$batch_file"
        fi
        first=false

        local resource_type=$(jq -r '.resourceType' "$file")
        local id=$(jq -r '.id' "$file")

        echo '{
            "request": {
                "method": "PUT",
                "url": "'"$resource_type/$id"'"
            },
            "resource": ' >> "$batch_file"

        cat "$file" >> "$batch_file"
        echo '}' >> "$batch_file"
    done

    echo ']}' >> "$batch_file"

    # Prepare curl command with appropriate authentication
    local curl_cmd="curl -s -X POST"

    if [[ "$AUTH_TYPE" == "token" || "$AUTH_TYPE" == "oauth" ]]; then
        curl_cmd="$curl_cmd -H 'Authorization: Bearer $AUTH_TOKEN'"
    fi

    curl_cmd="$curl_cmd -H 'Content-Type: application/fhir+json'"
    curl_cmd="$curl_cmd --connect-timeout $TIMEOUT"
    curl_cmd="$curl_cmd -d @$batch_file"
    curl_cmd="$curl_cmd '$FHIR_SERVER'"

    if [[ "$DRY_RUN" == "true" ]]; then
        log "DEBUG" "Would execute batch upload with ${#files[@]} resources"
        rm "$batch_file"
        return 0
    fi

    # Execute the curl command
    local response
    response=$(eval "$curl_cmd")
    local status=$?

    rm "$batch_file"

    if [[ $status -ne 0 ]]; then
        log "ERROR" "Failed to upload batch: curl error $status"
        return 1
    fi

    # Check for errors in response
    local error_count=$(echo "$response" | jq '[.entry[].response | select(.status | startswith("4") or startswith("5"))] | length')

    if [[ "$error_count" -gt 0 ]]; then
        log "WARNING" "Batch upload completed with $error_count errors"
        if [[ "$VERBOSE" == "true" ]]; then
            echo "$response" | jq '.entry[] | select(.response.status | startswith("4") or startswith("5")) | {url: .request.url, status: .response.status, outcome: .response.outcome}'
        fi
        return 1
    fi

    log "INFO" "Successfully uploaded batch with ${#files[@]} resources"
    return 0
}

# Main execution
main() {
    # Get OAuth token if needed
    if [[ "$AUTH_TYPE" == "oauth" ]]; then
        get_oauth_token
    fi

    # Find all JSON files in the resources directory
    local files=()
    while IFS= read -r file; do
        files+=("$file")
    done < <(find "$RESOURCES_DIR" -type f -name "*.json" | sort)

    log "INFO" "Found ${#files[@]} FHIR resource files"

    # Validate resources if requested
    if [[ "$VALIDATE" == "true" ]]; then
        log "INFO" "Validating resources..."
        local invalid_count=0

        for file in "${files[@]}"; do
            if ! validate_resource "$file"; then
                invalid_count=$((invalid_count + 1))
            fi
        done

        if [[ $invalid_count -gt 0 ]]; then
            log "ERROR" "Found $invalid_count invalid resources"
            exit 1
        fi

        log "INFO" "All resources validated successfully"
    fi

    # Upload resources in batches
    log "INFO" "Uploading resources in batches of $BATCH_SIZE..."
    local total_files=${#files[@]}
    local processed=0
    local success=0
    local failed=0

    while [[ $processed -lt $total_files ]]; do
        local batch=()
        local batch_size=0

        while [[ $batch_size -lt $BATCH_SIZE && $processed -lt $total_files ]]; do
            batch+=("${files[$processed]}")
            batch_size=$((batch_size + 1))
            processed=$((processed + 1))
        done

        log "INFO" "Uploading batch $((processed / BATCH_SIZE)) of $((total_files / BATCH_SIZE + (total_files % BATCH_SIZE > 0 ? 1 : 0)))..."

        if upload_batch "${batch[@]}"; then
            success=$((success + batch_size))
        else
            # If batch upload fails, try individual uploads
            log "WARNING" "Batch upload failed, trying individual uploads..."

            for file in "${batch[@]}"; do
                if upload_resource "$file"; then
                    success=$((success + 1))
                else
                    failed=$((failed + 1))
                fi
            done
        fi

        log "INFO" "Progress: $processed/$total_files resources processed"
    done

    # Summary
    log "INFO" "Deployment completed"
    log "INFO" "Total resources: $total_files"
    log "INFO" "Successfully uploaded: $success"
    log "INFO" "Failed to upload: $failed"

    if [[ $failed -gt 0 ]]; then
        log "WARNING" "Some resources failed to upload. See log file for details: $LOG_FILE"
        return 1
    else
        log "INFO" "All resources uploaded successfully"
        return 0
    fi
}

# Run the main function
main
exit $?
