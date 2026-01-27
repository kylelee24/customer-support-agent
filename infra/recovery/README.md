# Azure Recovery Stack for rg-kyle-cs

This directory contains infrastructure-as-code for recovering Azure resources after cleanup.

## Quick Start

### 1. Authenticate to Azure

```bash
# Login to the correct tenant/subscription
az login

# List subscriptions to find the right one
az account list --output table

# Set the correct subscription (e.g., Kyle's Sandbox)
az account set --subscription "aff3f8cf-511e-4af8-a2ae-ba765091e13a"
```

### 2. Discovery - See What Exists

```bash
# Using Azure CLI
source azure-cli-commands.sh
discovery

# Or directly
az resource list --resource-group rg-kyle-cs --output table
```

### 3. Cleanup - Remove Resources

#### Option A: Azure CLI (Interactive)

```bash
# Source the script to load functions
source azure-cli-commands.sh

# Delete application layer only (keeps OpenAI, ACS, Search, Storage)
cleanup_half

# Delete everything except resource group
cleanup_all

# Delete specific resource types
cleanup_container_apps
cleanup_container_registry
cleanup_openai
```

#### Option B: Quick One-Liners

```bash
# Delete all Container Apps
az containerapp list -g rg-kyle-cs --query "[].id" -o tsv | xargs -I {} az resource delete --ids {}

# Delete Container App Environment
az containerapp env list -g rg-kyle-cs --query "[].id" -o tsv | xargs -I {} az resource delete --ids {}

# Delete Container Registry
az acr list -g rg-kyle-cs --query "[].id" -o tsv | xargs -I {} az resource delete --ids {}

# Delete OpenAI
az cognitiveservices account list -g rg-kyle-cs --query "[].id" -o tsv | xargs -I {} az resource delete --ids {}

# Delete Communication Services
az communication list -g rg-kyle-cs --query "[].id" -o tsv | xargs -I {} az resource delete --ids {}

# Delete entire resource group (nuclear option)
az group delete --name rg-kyle-cs --yes --no-wait
```

### 4. Recovery - Recreate Resources

#### Option A: Terraform (Recommended)

```bash
cd infra/recovery

# Initialize Terraform
terraform init

# Preview what will be created
terraform plan

# Apply the configuration
terraform apply

# Show outputs (endpoints, connection strings)
terraform output
```

#### Option B: Azure CLI

```bash
source azure-cli-commands.sh

# Recreate everything
recover_all

# Or recreate specific resources
create_resource_group
create_openai
create_communication_service
create_container_registry
create_container_environment
```

## File Structure

```
recovery/
├── main.tf              # Main Terraform configuration
├── variables.tf         # Input variables with defaults
├── outputs.tf           # Output values (endpoints, IDs)
├── azure-cli-commands.sh # Azure CLI helper script
└── README.md            # This file
```

## Resources Managed

| Resource Type | Name Pattern | Purpose |
|--------------|--------------|---------|
| Resource Group | rg-kyle-cs | Container for all resources |
| Azure OpenAI | oai-customer-support-dev | GPT-4o realtime for voice AI |
| Communication Services | acs-customer-support-dev | Phone calls and SMS |
| Container App Environment | cae-customer-support-dev | Serverless container hosting |
| Container App | ca-customer-support-dev | The voice agent application |
| Container Registry | acrcustomersupportdev | Docker image storage |
| AI Search | srch-customer-support-dev | RAG document search |
| Storage Account | stcustomersupportdev | Document storage |
| Log Analytics | log-customer-support-dev | Logging and monitoring |
| Application Insights | appi-customer-support-dev | Application telemetry |
| Event Grid | evgt-customer-support-dev | ACS event handling |

## Cleanup Strategy: "Half"

When running `cleanup_half`, the following resources are **deleted**:
- Container Apps
- Container App Environment
- Container Registry

These resources are **kept**:
- Azure OpenAI (expensive to recreate, has deployment quotas)
- Communication Services (has phone numbers)
- Azure AI Search (has indexes)
- Storage Account (has documents)
- Log Analytics & App Insights (has historical data)

## Cost Considerations

| Resource | Approximate Cost | Notes |
|----------|-----------------|-------|
| Azure OpenAI | Pay-per-use | Only costs when used |
| Communication Services | Pay-per-use | Phone number ~$2/month |
| Container Apps | Pay-per-use | $0 when scaled to 0 |
| Container Registry | ~$5/month (Basic) | Can delete images |
| AI Search | ~$75/month (Basic) | Consider Free tier |
| Storage | ~$0.02/GB/month | Minimal cost |
| Log Analytics | Pay-per-GB | 5GB free/month |

## Tips

1. **Export before delete**: Always run `discovery` and save `resources-backup.json` before cleanup
2. **Use Terraform state**: If recovering frequently, use remote state (Azure Storage)
3. **Check soft-delete**: Some resources (KeyVault, Storage) have soft-delete enabled
4. **Quota limits**: OpenAI deployments have regional quotas - check before recreating
