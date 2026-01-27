#!/bin/bash
# =============================================================================
# Azure CLI Commands for Resource Group Management
# Resource Group: rg-kyle-cs
# =============================================================================

set -e

# Configuration
RESOURCE_GROUP="rg-kyle-cs"
LOCATION="eastus2"
ENVIRONMENT="dev"
PROJECT_NAME="customer-support"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo_info() { echo -e "${GREEN}[INFO]${NC} $1"; }
echo_warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
echo_error() { echo -e "${RED}[ERROR]${NC} $1"; }

# =============================================================================
# DISCOVERY COMMANDS - Run these first to see what exists
# =============================================================================

discovery() {
    echo_info "Discovering resources in $RESOURCE_GROUP..."
    
    # List all resources
    echo_info "All resources:"
    az resource list --resource-group $RESOURCE_GROUP --output table
    
    # Export to JSON for backup
    echo_info "Exporting resource list to resources-backup.json..."
    az resource list --resource-group $RESOURCE_GROUP --output json > resources-backup.json
    
    # Get resource types summary
    echo_info "Resource types summary:"
    az resource list --resource-group $RESOURCE_GROUP \
        --query "[].type" --output tsv | sort | uniq -c | sort -rn
}

# =============================================================================
# CLEANUP COMMANDS - Delete resources (USE WITH CAUTION!)
# =============================================================================

# Delete specific resource by name and type
delete_resource() {
    local RESOURCE_NAME=$1
    local RESOURCE_TYPE=$2
    
    echo_warn "Deleting $RESOURCE_TYPE: $RESOURCE_NAME"
    az resource delete \
        --resource-group $RESOURCE_GROUP \
        --name $RESOURCE_NAME \
        --resource-type $RESOURCE_TYPE \
        --verbose
}

# Delete by resource ID (safer, more precise)
delete_by_id() {
    local RESOURCE_ID=$1
    echo_warn "Deleting resource: $RESOURCE_ID"
    az resource delete --ids $RESOURCE_ID --verbose
}

# Delete Container Apps
cleanup_container_apps() {
    echo_info "Deleting Container Apps..."
    az containerapp list --resource-group $RESOURCE_GROUP \
        --query "[].id" --output tsv | while read id; do
        delete_by_id "$id"
    done
}

# Delete Container App Environment
cleanup_container_environment() {
    echo_info "Deleting Container App Environments..."
    az containerapp env list --resource-group $RESOURCE_GROUP \
        --query "[].id" --output tsv | while read id; do
        delete_by_id "$id"
    done
}

# Delete Container Registry
cleanup_container_registry() {
    echo_info "Deleting Container Registries..."
    az acr list --resource-group $RESOURCE_GROUP \
        --query "[].id" --output tsv | while read id; do
        delete_by_id "$id"
    done
}

# Delete OpenAI/Cognitive Services
cleanup_openai() {
    echo_info "Deleting Cognitive Services (OpenAI)..."
    az cognitiveservices account list --resource-group $RESOURCE_GROUP \
        --query "[].id" --output tsv | while read id; do
        delete_by_id "$id"
    done
}

# Delete Communication Services
cleanup_acs() {
    echo_info "Deleting Communication Services..."
    az communication list --resource-group $RESOURCE_GROUP \
        --query "[].id" --output tsv | while read id; do
        delete_by_id "$id"
    done
}

# Delete Search Services
cleanup_search() {
    echo_info "Deleting Search Services..."
    az search service list --resource-group $RESOURCE_GROUP \
        --query "[].id" --output tsv | while read id; do
        delete_by_id "$id"
    done
}

# Delete Storage Accounts
cleanup_storage() {
    echo_info "Deleting Storage Accounts..."
    az storage account list --resource-group $RESOURCE_GROUP \
        --query "[].id" --output tsv | while read id; do
        delete_by_id "$id"
    done
}

# Delete Log Analytics Workspaces
cleanup_log_analytics() {
    echo_info "Deleting Log Analytics Workspaces..."
    az monitor log-analytics workspace list --resource-group $RESOURCE_GROUP \
        --query "[].id" --output tsv | while read id; do
        delete_by_id "$id"
    done
}

# Delete Application Insights
cleanup_app_insights() {
    echo_info "Deleting Application Insights..."
    az monitor app-insights component list --resource-group $RESOURCE_GROUP \
        --query "[].id" --output tsv | while read id; do
        delete_by_id "$id"
    done
}

# Delete Event Grid
cleanup_eventgrid() {
    echo_info "Deleting Event Grid System Topics..."
    az eventgrid system-topic list --resource-group $RESOURCE_GROUP \
        --query "[].id" --output tsv 2>/dev/null | while read id; do
        delete_by_id "$id"
    done
}

# Clean up half of the resources (containers and apps, keep core services)
cleanup_half() {
    echo_warn "Cleaning up application layer (keeping core services)..."
    echo_warn "This will delete: Container Apps, Container Environment, Container Registry"
    echo_warn "This will keep: OpenAI, Communication Services, Search, Storage, Monitoring"
    
    read -p "Are you sure? (y/N) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        cleanup_container_apps
        cleanup_container_environment
        cleanup_container_registry
        echo_info "Application layer cleanup complete!"
    else
        echo_info "Cleanup cancelled."
    fi
}

# Clean up everything except resource group
cleanup_all() {
    echo_error "WARNING: This will delete ALL resources in $RESOURCE_GROUP!"
    read -p "Are you sure? (y/N) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        cleanup_container_apps
        cleanup_container_environment
        cleanup_container_registry
        cleanup_eventgrid
        cleanup_app_insights
        cleanup_log_analytics
        cleanup_search
        cleanup_storage
        cleanup_acs
        cleanup_openai
        echo_info "All resources deleted!"
    else
        echo_info "Cleanup cancelled."
    fi
}

# Delete entire resource group
delete_resource_group() {
    echo_error "WARNING: This will delete the ENTIRE resource group $RESOURCE_GROUP!"
    read -p "Are you sure? (y/N) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        az group delete --name $RESOURCE_GROUP --yes --no-wait
        echo_info "Resource group deletion initiated (running in background)."
    else
        echo_info "Deletion cancelled."
    fi
}

# =============================================================================
# RECOVERY COMMANDS - Recreate resources
# =============================================================================

create_resource_group() {
    echo_info "Creating resource group $RESOURCE_GROUP..."
    az group create \
        --name $RESOURCE_GROUP \
        --location $LOCATION \
        --tags Environment=$ENVIRONMENT Project=$PROJECT_NAME ManagedBy=AzureCLI
}

create_openai() {
    local NAME="oai-${PROJECT_NAME}-${ENVIRONMENT}"
    echo_info "Creating Azure OpenAI service: $NAME..."
    
    az cognitiveservices account create \
        --name $NAME \
        --resource-group $RESOURCE_GROUP \
        --kind OpenAI \
        --sku S0 \
        --location $LOCATION \
        --custom-domain $NAME \
        --tags Environment=$ENVIRONMENT Project=$PROJECT_NAME
    
    # Deploy GPT-4o realtime model
    echo_info "Deploying GPT-4o realtime model..."
    az cognitiveservices account deployment create \
        --name $NAME \
        --resource-group $RESOURCE_GROUP \
        --deployment-name "gpt-4o-realtime-preview" \
        --model-name "gpt-4o-realtime-preview" \
        --model-version "2024-10-01" \
        --model-format OpenAI \
        --sku-capacity 1 \
        --sku-name Standard
}

create_communication_service() {
    local NAME="acs-${PROJECT_NAME}-${ENVIRONMENT}"
    echo_info "Creating Communication Service: $NAME..."
    
    az communication create \
        --name $NAME \
        --resource-group $RESOURCE_GROUP \
        --location global \
        --data-location "United States" \
        --tags Environment=$ENVIRONMENT Project=$PROJECT_NAME
}

create_log_analytics() {
    local NAME="log-${PROJECT_NAME}-${ENVIRONMENT}"
    echo_info "Creating Log Analytics Workspace: $NAME..."
    
    az monitor log-analytics workspace create \
        --resource-group $RESOURCE_GROUP \
        --workspace-name $NAME \
        --location $LOCATION \
        --retention-time 30 \
        --tags Environment=$ENVIRONMENT Project=$PROJECT_NAME
}

create_app_insights() {
    local NAME="appi-${PROJECT_NAME}-${ENVIRONMENT}"
    local WORKSPACE_NAME="log-${PROJECT_NAME}-${ENVIRONMENT}"
    echo_info "Creating Application Insights: $NAME..."
    
    WORKSPACE_ID=$(az monitor log-analytics workspace show \
        --resource-group $RESOURCE_GROUP \
        --workspace-name $WORKSPACE_NAME \
        --query id --output tsv)
    
    az monitor app-insights component create \
        --app $NAME \
        --resource-group $RESOURCE_GROUP \
        --location $LOCATION \
        --workspace $WORKSPACE_ID \
        --application-type web \
        --tags Environment=$ENVIRONMENT Project=$PROJECT_NAME
}

create_container_registry() {
    local NAME="acr${PROJECT_NAME//[-_]/}${ENVIRONMENT}"
    echo_info "Creating Container Registry: $NAME..."
    
    az acr create \
        --resource-group $RESOURCE_GROUP \
        --name $NAME \
        --sku Basic \
        --admin-enabled true \
        --location $LOCATION \
        --tags Environment=$ENVIRONMENT Project=$PROJECT_NAME
}

create_container_environment() {
    local NAME="cae-${PROJECT_NAME}-${ENVIRONMENT}"
    local WORKSPACE_NAME="log-${PROJECT_NAME}-${ENVIRONMENT}"
    echo_info "Creating Container App Environment: $NAME..."
    
    WORKSPACE_ID=$(az monitor log-analytics workspace show \
        --resource-group $RESOURCE_GROUP \
        --workspace-name $WORKSPACE_NAME \
        --query customerId --output tsv)
    
    WORKSPACE_KEY=$(az monitor log-analytics workspace get-shared-keys \
        --resource-group $RESOURCE_GROUP \
        --workspace-name $WORKSPACE_NAME \
        --query primarySharedKey --output tsv)
    
    az containerapp env create \
        --name $NAME \
        --resource-group $RESOURCE_GROUP \
        --location $LOCATION \
        --logs-workspace-id $WORKSPACE_ID \
        --logs-workspace-key $WORKSPACE_KEY \
        --tags Environment=$ENVIRONMENT Project=$PROJECT_NAME
}

create_search() {
    local NAME="srch-${PROJECT_NAME}-${ENVIRONMENT}"
    echo_info "Creating Azure AI Search: $NAME..."
    
    az search service create \
        --name $NAME \
        --resource-group $RESOURCE_GROUP \
        --sku basic \
        --location $LOCATION \
        --tags Environment=$ENVIRONMENT Project=$PROJECT_NAME
}

create_storage() {
    local NAME="st${PROJECT_NAME//[-_]/}${ENVIRONMENT}"
    echo_info "Creating Storage Account: $NAME..."
    
    az storage account create \
        --name $NAME \
        --resource-group $RESOURCE_GROUP \
        --location $LOCATION \
        --sku Standard_LRS \
        --kind StorageV2 \
        --tags Environment=$ENVIRONMENT Project=$PROJECT_NAME
    
    # Create documents container
    az storage container create \
        --name documents \
        --account-name $NAME
}

# Recover all resources
recover_all() {
    echo_info "Recovering all resources in $RESOURCE_GROUP..."
    
    create_resource_group
    create_log_analytics
    create_app_insights
    create_openai
    create_communication_service
    create_search
    create_storage
    create_container_registry
    create_container_environment
    
    echo_info "Recovery complete! Run 'discovery' to verify resources."
}

# =============================================================================
# MENU
# =============================================================================

show_menu() {
    echo ""
    echo "=== Azure Resource Management for $RESOURCE_GROUP ==="
    echo ""
    echo "Discovery:"
    echo "  1) discovery          - List all resources"
    echo ""
    echo "Cleanup:"
    echo "  2) cleanup_half       - Delete app layer (keep core services)"
    echo "  3) cleanup_all        - Delete all resources (keep RG)"
    echo "  4) delete_resource_group - Delete entire resource group"
    echo ""
    echo "Recovery:"
    echo "  5) recover_all        - Recreate all resources"
    echo ""
    echo "Individual Cleanup:"
    echo "  6) cleanup_container_apps"
    echo "  7) cleanup_container_environment"
    echo "  8) cleanup_container_registry"
    echo "  9) cleanup_openai"
    echo "  10) cleanup_acs"
    echo ""
    echo "Usage: source azure-cli-commands.sh && <function_name>"
    echo ""
}

# Show menu if script is run directly
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    show_menu
fi
