# =============================================================================
# VARIABLES - Customize these for your deployment
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

  validation {
    condition = contains([
      "eastus", "eastus2", "westus", "westus2", "westus3",
      "centralus", "northcentralus", "southcentralus",
      "canadacentral", "canadaeast",
      "westeurope", "northeurope", "uksouth", "ukwest",
      "australiaeast", "australiasoutheast",
      "japaneast", "japanwest",
      "southeastasia", "eastasia"
    ], var.location)
    error_message = "Location must be a valid Azure region."
  }
}

variable "environment" {
  description = "Environment name (dev, staging, prod)"
  type        = string
  default     = "dev"

  validation {
    condition     = contains(["dev", "staging", "prod"], var.environment)
    error_message = "Environment must be dev, staging, or prod."
  }
}

variable "project_name" {
  description = "Project name for resource naming"
  type        = string
  default     = "customer-support"
}

# =============================================================================
# OPTIONAL VARIABLES
# =============================================================================

variable "openai_model_version" {
  description = "Azure OpenAI model version"
  type        = string
  default     = "2024-10-01"
}

variable "container_cpu" {
  description = "CPU allocation for container app"
  type        = number
  default     = 0.5
}

variable "container_memory" {
  description = "Memory allocation for container app"
  type        = string
  default     = "1Gi"
}

variable "min_replicas" {
  description = "Minimum number of container replicas"
  type        = number
  default     = 0
}

variable "max_replicas" {
  description = "Maximum number of container replicas"
  type        = number
  default     = 3
}

variable "log_retention_days" {
  description = "Log Analytics retention in days"
  type        = number
  default     = 30
}

variable "search_sku" {
  description = "Azure AI Search SKU"
  type        = string
  default     = "basic"

  validation {
    condition     = contains(["free", "basic", "standard", "standard2", "standard3"], var.search_sku)
    error_message = "Search SKU must be free, basic, standard, standard2, or standard3."
  }
}
