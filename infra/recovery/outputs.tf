# =============================================================================
# OUTPUTS
# =============================================================================

output "resource_group_name" {
  description = "Name of the resource group"
  value       = azurerm_resource_group.main.name
}

output "resource_group_id" {
  description = "ID of the resource group"
  value       = azurerm_resource_group.main.id
}

output "openai_endpoint" {
  description = "Azure OpenAI endpoint"
  value       = azurerm_cognitive_account.openai.endpoint
}

output "openai_deployment_name" {
  description = "Azure OpenAI deployment name"
  value       = azurerm_cognitive_deployment.gpt4.name
}

output "communication_service_name" {
  description = "Azure Communication Services name"
  value       = azurerm_communication_service.main.name
}

output "container_registry_login_server" {
  description = "Container Registry login server"
  value       = azurerm_container_registry.main.login_server
}

output "container_app_url" {
  description = "Container App URL"
  value       = "https://${azurerm_container_app.main.latest_revision_fqdn}"
}

output "search_service_name" {
  description = "Azure AI Search service name"
  value       = azurerm_search_service.main.name
}

output "storage_account_name" {
  description = "Storage account name"
  value       = azurerm_storage_account.main.name
}

output "application_insights_connection_string" {
  description = "Application Insights connection string"
  value       = azurerm_application_insights.main.connection_string
  sensitive   = true
}

output "log_analytics_workspace_id" {
  description = "Log Analytics Workspace ID"
  value       = azurerm_log_analytics_workspace.main.id
}
