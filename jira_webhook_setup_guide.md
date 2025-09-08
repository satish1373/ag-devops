# 🔗 Setting Up Real Jira Webhook Integration

## Prerequisites
- Jira Administrator access
- Public URL for your webhook endpoint
- LangGraph DevOps server running

## Step 1: Expose Your Local Server (Choose One)

### Option A: Using ngrok (Recommended)
```bash
# Install ngrok: https://ngrok.com/download
# Then expose your local server:
ngrok http 8000

# You'll get a URL like: https://abc123.ngrok.io
# Your webhook URL will be: https://abc123.ngrok.io/webhook/jira
```

### Option B: Using localtunnel
```bash
# Install localtunnel
npm install -g localtunnel

# Expose your server
lt --port 8000 --subdomain langgraph-devops

# Your webhook URL: https://langgraph-devops.loca.lt/webhook/jira
```

### Option C: Deploy to Cloud (Production)
```bash
# Deploy to Heroku, Railway, or your cloud provider
# Update JIRA_WEBHOOK_SECRET in production environment
```

## Step 2: Configure Jira Webhook

1. **Access Jira Settings**
   - Go to: `https://yourcompany.atlassian.net`
   - Click: ⚙️ Settings → System → WebHooks

2. **Create New Webhook**
   - Click: "Create a WebHook"
   - **Name**: "LangGraph DevOps Autocoder"
   - **Status**: Enabled
   - **URL**: `https://your-ngrok-url.ngrok.io/webhook/jira`

3. **Configure Events**
   Select these events:
   - ✅ Issue Created
   - ✅ Issue Updated
   - ✅ Issue Commented

4. **Set JQL Filter (Optional)**
   ```jql
   project = "YOUR_PROJECT" AND labels in (automation, devops)
   ```

5. **Advanced Settings**
   - **Exclude body**: Unchecked
   - **Secret**: Enter your webhook secret from `.env`

## Step 3: Test Webhook Connection

```bash
# Test webhook endpoint
curl -X POST https://your-ngrok-url.ngrok.io/webhook/jira \
  -H "Content-Type: application/json" \
  -H "X-Atlassian-Webhook-Identifier: test" \
  -d '{"test": "connection"}'

# Should return: {"status": "accepted", "message": "..."}
```

## Step 4: Create Test Issues

### Example 1: Export Feature
- **Project**: Your project
- **Issue Type**: Story
- **Summary**: "Add CSV export functionality to user dashboard"
- **Description**: "Add export button that allows users to download their data as CSV file with all details including timestamps and categories"
- **Labels**: `automation`, `frontend`, `export`

### Example 2: Search Feature  
- **Project**: Your project
- **Issue Type**: Story
- **Summary**: "Implement real-time search and filtering"
- **Description**: "Add search bar with real-time filtering capabilities for todos by title, description, and priority level"
- **Labels**: `automation`, `frontend`, `search`

### Example 3: Notification System
- **Project**: Your project
- **Issue Type**: Story  
- **Summary**: "Add notification system with due date alerts"
- **Description**: "Add notification badges and due date alerts for todos with priority indicators and overdue warnings"
- **Labels**: `automation`, `frontend`, `notifications`

## Step 5: Monitor Automation

After creating issues:

1. **Check LangGraph Logs**
   ```bash
   # Monitor real-time logs
   tail -f logs/devops_autocoder.log
   
   # Or via API
   curl http://localhost:8000/logs?lines=100
   ```

2. **Check Issue Status**
   ```bash
   # Replace with your actual issue key
   curl http://localhost:8000/status/PROJ-123
   ```

3. **Download Reports**
   ```bash
   # Get automation report
   curl http://localhost:8000/reports/PROJ-123 -o automation-report.md
   ```

## Troubleshooting

### Webhook Not Firing
- Check Jira webhook logs: Settings → System → WebHooks → View details
- Verify ngrok tunnel is active: `ngrok status`
- Check webhook URL accessibility: `curl https://your-url.ngrok.io/health`

### Authentication Issues
- Verify API token is correct
- Check Jira username/email
- Ensure user has project permissions

### Processing Errors
- Monitor LangGraph logs: `tail -f logs/devops_autocoder.log`
- Check webhook payload format
- Verify issue description contains automation keywords

## Security Best Practices

1. **Use Strong Webhook Secrets**
   ```bash
   # Generate secure webhook secret
   openssl rand -hex 32
   ```

2. **Restrict Webhook Access**
   - Use JQL filters to limit which issues trigger automation
   - Set up IP allowlisting if possible

3. **Monitor Activity**
   - Regularly check automation logs
   - Set up alerts for failed automations
   - Review generated code before production deployment

## Success Indicators

✅ **Webhook Configured**: Jira shows webhook as active
✅ **Connection Working**: Test webhook returns success
✅ **Issues Processing**: New issues trigger automation
✅ **Files Generated**: Code appears in your repository
✅ **Features Working**: New functionality visible in application

## Next Steps

After successful setup:
1. Create issues with automation keywords
2. Watch real-time code generation
3. Review generated reports
4. Test generated features
5. Scale to production workflows