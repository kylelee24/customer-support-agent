#!/bin/bash
set -eo pipefail

SUBSCRIPTION_ID="aff3f8cf-511e-4af8-a2ae-ba765091e13a"
RESOURCE_GROUP="rg-cs-agent"
CONTAINER_APP="callcenterapp"

# Defaults
MODE="stream"
HOURS=24
OUTPUT=""

usage() {
    echo "Usage: bash scripts/logs.sh [OPTIONS]"
    echo ""
    echo "Gather logs from the Azure Container App."
    echo ""
    echo "Modes:"
    echo "  -s, --stream          Stream live logs (default)"
    echo "  -r, --recent [HOURS]  Fetch recent logs (default: 24 hours)"
    echo "  -q, --query QUERY     Run a custom Log Analytics (KQL) query"
    echo ""
    echo "Options:"
    echo "  -o, --output FILE     Save output to a file"
    echo "  -h, --help            Show this help message"
    echo ""
    echo "Examples:"
    echo "  bash scripts/logs.sh                     # Stream live logs"
    echo "  bash scripts/logs.sh -r                  # Last 24 hours of logs"
    echo "  bash scripts/logs.sh -r 4                # Last 4 hours of logs"
    echo "  bash scripts/logs.sh -r 48 -o logs.txt   # Last 48h, save to file"
    echo "  bash scripts/logs.sh -q 'ContainerAppConsoleLogs_CL | where Log_s contains \"property_search\" | top 50 by TimeGenerated'"
}

# Parse arguments
while [[ $# -gt 0 ]]; do
    case "$1" in
        -s|--stream)
            MODE="stream"
            shift
            ;;
        -r|--recent)
            MODE="recent"
            shift
            if [[ $# -gt 0 && "$1" =~ ^[0-9]+$ ]]; then
                HOURS="$1"
                shift
            fi
            ;;
        -q|--query)
            MODE="query"
            shift
            if [[ $# -gt 0 ]]; then
                CUSTOM_QUERY="$1"
                shift
            else
                echo "Error: --query requires a KQL query string"
                exit 1
            fi
            ;;
        -o|--output)
            shift
            if [[ $# -gt 0 ]]; then
                OUTPUT="$1"
                shift
            else
                echo "Error: --output requires a filename"
                exit 1
            fi
            ;;
        -h|--help)
            usage
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            usage
            exit 1
            ;;
    esac
done

run_query() {
    local query="$1"
    local workspace_id
    workspace_id="$(get_workspace_id)"
    if [[ -z "$workspace_id" ]]; then
        echo "Error: Could not resolve Log Analytics workspace ID." >&2
        echo "Check that container app '${CONTAINER_APP}' exists in resource group '${RESOURCE_GROUP}'." >&2
        exit 1
    fi
    local cmd=(
        az monitor log-analytics query
        --workspace "$workspace_id"
        --analytics-query "$query"
        --timespan "PT${HOURS}H"
        --output json
    )

    local raw
    raw="$("${cmd[@]}" 2>&1)" || true

    if [[ -z "$raw" || "$raw" == "[]" ]]; then
        echo "No logs found in the last ${HOURS}h."
        return
    fi

    local formatted
    formatted="$(echo "$raw" | jq -r '.[] | "[" + .TimeGenerated + "] " + .Log_s' 2>/dev/null)" || formatted="$raw"

    if [[ -n "$OUTPUT" ]]; then
        echo "Saving logs to: $OUTPUT"
        echo "$formatted" | tee "$OUTPUT"
    else
        echo "$formatted"
    fi
}

get_workspace_id() {
    az containerapp show \
        --name "${CONTAINER_APP}" \
        --resource-group "${RESOURCE_GROUP}" \
        --subscription "${SUBSCRIPTION_ID}" \
        --query "properties.managedEnvironmentId" -o tsv \
    | xargs -I{} az containerapp env show \
        --ids {} \
        --subscription "${SUBSCRIPTION_ID}" \
        --query "properties.appLogsConfiguration.logAnalyticsConfiguration.customerId" -o tsv
}

case "$MODE" in
    stream)
        echo "Streaming live logs from ${CONTAINER_APP}..."
        echo "(Ctrl+C to stop)"
        echo ""
        if [[ -n "$OUTPUT" ]]; then
            az containerapp logs show \
                --name "${CONTAINER_APP}" \
                --resource-group "${RESOURCE_GROUP}" \
                --subscription "${SUBSCRIPTION_ID}" \
                --type console \
                --follow \
            | tee "$OUTPUT"
        else
            az containerapp logs show \
                --name "${CONTAINER_APP}" \
                --resource-group "${RESOURCE_GROUP}" \
                --subscription "${SUBSCRIPTION_ID}" \
                --type console \
                --follow
        fi
        ;;
    recent)
        echo "Fetching last ${HOURS}h of logs from ${CONTAINER_APP}..."
        echo ""
        run_query "ContainerAppConsoleLogs_CL | where ContainerAppName_s == '${CONTAINER_APP}' | project TimeGenerated, Log_s | order by TimeGenerated asc"
        ;;
    query)
        echo "Running custom query (timespan: ${HOURS}h)..."
        echo ""
        run_query "$CUSTOM_QUERY"
        ;;
esac
