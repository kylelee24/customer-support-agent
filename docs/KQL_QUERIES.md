# KQL Queries for Log Analytics

Useful queries for the Log Analytics workspace connected to the Container App. Run these in **Azure Portal > Log Analytics workspace > Logs**.

## Console Logs

### Clean log output (no metadata)

```kql
ContainerAppConsoleLogs_CL
| where TimeGenerated > ago(1h)
| project TimeGenerated, Log_s
| order by TimeGenerated desc
```

### All console logs (last 30 minutes)

```kql
ContainerAppConsoleLogs_CL
| where TimeGenerated > ago(30m)
| order by TimeGenerated desc
```

### Filter by keyword

```kql
ContainerAppConsoleLogs_CL
| where TimeGenerated > ago(1h)
| where Log_s contains "property_search"
| project TimeGenerated, Log_s
| order by TimeGenerated desc
```

### Errors only

```kql
ContainerAppConsoleLogs_CL
| where TimeGenerated > ago(24h)
| where Log_s contains "ERROR" or Log_s contains "Traceback" or Log_s contains "Exception"
| project TimeGenerated, Log_s
| order by TimeGenerated desc
```

### Warnings and errors

```kql
ContainerAppConsoleLogs_CL
| where TimeGenerated > ago(24h)
| where Log_s contains "WARNING" or Log_s contains "ERROR" or Log_s contains "Exception"
| project TimeGenerated, Log_s
| order by TimeGenerated desc
```

### Call lifecycle events

```kql
ContainerAppConsoleLogs_CL
| where TimeGenerated > ago(24h)
| where Log_s contains "call" or Log_s contains "hang_up" or Log_s contains "end_call"
| project TimeGenerated, Log_s
| order by TimeGenerated desc
```

### Transcript and email activity

```kql
ContainerAppConsoleLogs_CL
| where TimeGenerated > ago(24h)
| where Log_s contains "transcript" or Log_s contains "email" or Log_s contains "summary"
| project TimeGenerated, Log_s
| order by TimeGenerated desc
```

### Property search requests

```kql
ContainerAppConsoleLogs_CL
| where TimeGenerated > ago(24h)
| where Log_s contains "property" or Log_s contains "realtordr"
| project TimeGenerated, Log_s
| order by TimeGenerated desc
```

### Log volume per hour (last 24h)

```kql
ContainerAppConsoleLogs_CL
| where TimeGenerated > ago(24h)
| summarize Count = count() by bin(TimeGenerated, 1h)
| order by TimeGenerated asc
| render timechart
```

### Error rate per hour

```kql
ContainerAppConsoleLogs_CL
| where TimeGenerated > ago(24h)
| summarize
    Total = count(),
    Errors = countif(Log_s contains "ERROR" or Log_s contains "Exception")
    by bin(TimeGenerated, 1h)
| extend ErrorRate = round(100.0 * Errors / Total, 1)
| order by TimeGenerated asc
```

## System Logs

### Container starts, stops, and restarts

```kql
ContainerAppSystemLogs_CL
| where TimeGenerated > ago(24h)
| project TimeGenerated, Reason_s, Log_s, Type_s
| order by TimeGenerated desc
```

### Container crashes / failures

```kql
ContainerAppSystemLogs_CL
| where TimeGenerated > ago(7d)
| where Reason_s contains "Kill" or Reason_s contains "Fail" or Reason_s contains "BackOff" or Reason_s contains "Unhealthy"
| project TimeGenerated, Reason_s, Log_s
| order by TimeGenerated desc
```

### Revision deployments

```kql
ContainerAppSystemLogs_CL
| where TimeGenerated > ago(7d)
| where Log_s contains "revision" or Reason_s contains "Pull" or Reason_s contains "Created"
| project TimeGenerated, Reason_s, Log_s
| order by TimeGenerated desc
```

## Tips

- Replace `ago(1h)` with `ago(30m)`, `ago(24h)`, `ago(7d)`, etc. to adjust the time window.
- Use `| take 50` at the end to limit result count while exploring.
- `Log_s` is the main log message field. `Reason_s` is used in system logs for event types.
- Use `contains` for case-insensitive matching, `has` for whole-word matching.
