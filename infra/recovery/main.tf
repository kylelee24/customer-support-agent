# Azure Recovery Terraform Stack
# Resource Group: rg-kyle-cs
# 
# This Terraform configuration can recreate the resources that were cleaned up.
# Run `terraform init && terraform plan` to see what will be created.

terraform {
  required_version = ">= 1.0"

  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "~> 3.0"
    }
  }
}

provider "azurerm" {
  features {}
  
  # Uncomment and set the subscription ID where rg-kyle-cs exists
  # subscription_id = "aff3f8cf-511e-4af8-a2ae-ba765091e13a"  # Kyle's Sandbox
}

# =============================================================================
# VARIABLES
# =============================================================================

variable "resource_group_name" {
  description = "Name of the resource group"
  type        = string
  default     = "rg-kyle-cs"
}

variable "location" {
  description = "Azure region for resources"
  type        = string
  default     = "eastus2"
}

variable "environment" {
  description = "Environment name"
  type        = string
  default     = "dev"
}

variable "project_name" {
  description = "Project name for resource naming"
  type        = string
  default     = "customer-support"
}

# =============================================================================
# RESOURCE GROUP
# =============================================================================

resource "azurerm_resource_group" "main" {
  name     = var.resource_group_name
  location = var.location

  tags = {
    Environment = var.environment
    Project     = var.project_name
    ManagedBy   = "Terraform"
  }
}

# =============================================================================
# AZURE OPENAI SERVICE
# =============================================================================

resource "azurerm_cognitive_account" "openai" {
  name                  = "oai-${var.project_name}-${var.environment}"
  location              = var.location
  resource_group_name   = azurerm_resource_group.main.name
  kind                  = "OpenAI"
  sku_name              = "S0"
  custom_subdomain_name = "oai-${var.project_name}-${var.environment}"

  tags = azurerm_resource_group.main.tags

  lifecycle {
    ignore_changes = [
      tags["CreatedDate"]
    ]
  }
}

resource "azurerm_cognitive_deployment" "gpt4" {
  name                 = "gpt-4o-realtime-preview"
  cognitive_account_id = azurerm_cognitive_account.openai.id

  model {
    format  = "OpenAI"
    name    = "gpt-4o-realtime-preview"
    version = "2024-10-01"
  }

  scale {
    type = "Standard"
  }
}

# =============================================================================
# AZURE COMMUNICATION SERVICES
# =============================================================================

resource "azurerm_communication_service" "main" {
  name                = "acs-${var.project_name}-${var.environment}"
  resource_group_name = azurerm_resource_group.main.name
  data_location       = "United States"

  tags = azurerm_resource_group.main.tags
}

# =============================================================================
# CONTAINER APPS ENVIRONMENT
# =============================================================================

resource "azurerm_log_analytics_workspace" "main" {
  name                = "log-${var.project_name}-${var.environment}"
  location            = var.location
  resource_group_name = azurerm_resource_group.main.name
  sku                 = "PerGB2018"
  retention_in_days   = 30

  tags = azurerm_resource_group.main.tags
}

resource "azurerm_application_insights" "main" {
  name                = "appi-${var.project_name}-${var.environment}"
  location            = var.location
  resource_group_name = azurerm_resource_group.main.name
  workspace_id        = azurerm_log_analytics_workspace.main.id
  application_type    = "web"

  tags = azurerm_resource_group.main.tags
}

resource "azurerm_container_app_environment" "main" {
  name                       = "cae-${var.project_name}-${var.environment}"
  location                   = var.location
  resource_group_name        = azurerm_resource_group.main.name
  log_analytics_workspace_id = azurerm_log_analytics_workspace.main.id

  tags = azurerm_resource_group.main.tags
}

# =============================================================================
# CONTAINER REGISTRY
# =============================================================================

resource "azurerm_container_registry" "main" {
  name                = "acr${replace(var.project_name, "-", "")}${var.environment}"
  resource_group_name = azurerm_resource_group.main.name
  location            = var.location
  sku                 = "Basic"
  admin_enabled       = true

  tags = azurerm_resource_group.main.tags
}

# =============================================================================
# CONTAINER APP
# =============================================================================

resource "azurerm_container_app" "main" {
  name                         = "ca-${var.project_name}-${var.environment}"
  container_app_environment_id = azurerm_container_app_environment.main.id
  resource_group_name          = azurerm_resource_group.main.name
  revision_mode                = "Single"

  template {
    container {
      name   = "customer-support-agent"
      image  = "${azurerm_container_registry.main.login_server}/customer-support-agent:latest"
      cpu    = 0.5
      memory = "1Gi"

      env {
        name  = "AZURE_OPENAI_ENDPOINT"
        value = azurerm_cognitive_account.openai.endpoint
      }

      env {
        name  = "AZURE_OPENAI_DEPLOYMENT"
        value = azurerm_cognitive_deployment.gpt4.name
      }

      env {
        name  = "APPLICATIONINSIGHTS_CONNECTION_STRING"
        value = azurerm_application_insights.main.connection_string
      }
    }

    min_replicas = 0
    max_replicas = 3
  }

  ingress {
    external_enabled = true
    target_port      = 8080

    traffic_weight {
      percentage      = 100
      latest_revision = true
    }
  }

  tags = azurerm_resource_group.main.tags

  depends_on = [
    azurerm_container_registry.main
  ]
}

# =============================================================================
# AZURE AI SEARCH (for RAG)
# =============================================================================

resource "azurerm_search_service" "main" {
  name                = "srch-${var.project_name}-${var.environment}"
  resource_group_name = azurerm_resource_group.main.name
  location            = var.location
  sku                 = "basic"

  tags = azurerm_resource_group.main.tags
}

# =============================================================================
# STORAGE ACCOUNT (for documents)
# =============================================================================

resource "azurerm_storage_account" "main" {
  name                     = "st${replace(var.project_name, "-", "")}${var.environment}"
  resource_group_name      = azurerm_resource_group.main.name
  location                 = var.location
  account_tier             = "Standard"
  account_replication_type = "LRS"

  tags = azurerm_resource_group.main.tags
}

resource "azurerm_storage_container" "documents" {
  name                  = "documents"
  storage_account_name  = azurerm_storage_account.main.name
  container_access_type = "private"
}

# =============================================================================
# EVENT GRID (for call events)
# =============================================================================

resource "azurerm_eventgrid_system_topic" "acs" {
  name                   = "evgt-${var.project_name}-${var.environment}"
  resource_group_name    = azurerm_resource_group.main.name
  location               = "global"
  source_arm_resource_id = azurerm_communication_service.main.id
  topic_type             = "Microsoft.Communication.CommunicationServices"

  tags = azurerm_resource_group.main.tags
}
