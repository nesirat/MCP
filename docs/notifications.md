# Notification System Documentation

## Overview

The notification system provides a flexible way to receive alerts about API usage and system events through multiple channels. It supports email, webhook, Slack, and Microsoft Teams notifications, with configurable templates and delivery options.

## Notification Types

### 1. Email Notifications

Email notifications are sent to specified recipients when alerts are triggered. They include:
- Configurable recipient list
- Customizable subject template
- HTML-formatted message body
- Alert details and context

Configuration options:
```json
{
    "recipients": ["user@example.com", "team@example.com"],
    "subject_template": "Alert: {{alert.type}} - {{alert.level}}"
}
```

### 2. Webhook Notifications

Webhook notifications send HTTP requests to specified endpoints with alert data. Features:
- Configurable HTTP method (POST/PUT)
- Customizable payload format
- Retry mechanism for failed deliveries
- Authentication support

Configuration options:
```json
{
    "url": "https://example.com/webhook",
    "method": "POST",
    "headers": {
        "Authorization": "Bearer token"
    }
}
```

### 3. Slack Notifications

Slack notifications post messages to specified channels using Slack's webhook API. Features:
- Channel selection
- Rich message formatting
- Interactive buttons
- Thread support

Configuration options:
```json
{
    "webhook_url": "https://hooks.slack.com/services/...",
    "channel": "#alerts"
}
```

### 4. Microsoft Teams Notifications

Teams notifications post messages to specified channels using Microsoft Teams' webhook API. Features:
- Channel selection
- Rich card formatting
- Action buttons
- Adaptive cards support

Configuration options:
```json
{
    "webhook_url": "https://outlook.office.com/webhook/..."
}
```

## Alert Templates

Each notification type supports customizable templates for alert messages:

### Email Template
```html
<h2>Alert: {{alert.type}}</h2>
<p><strong>Level:</strong> {{alert.level}}</p>
<p><strong>Message:</strong> {{alert.message}}</p>
<p><strong>Value:</strong> {{alert.value}}</p>
<p><strong>Threshold:</strong> {{alert.threshold}}</p>
<p><strong>Timestamp:</strong> {{alert.timestamp}}</p>
```

### Webhook Payload
```json
{
    "type": "{{alert.type}}",
    "level": "{{alert.level}}",
    "message": "{{alert.message}}",
    "value": {{alert.value}},
    "threshold": {{alert.threshold}},
    "timestamp": "{{alert.timestamp}}"
}
```

### Slack Message
```json
{
    "blocks": [
        {
            "type": "header",
            "text": {
                "type": "plain_text",
                "text": "Alert: {{alert.type}}"
            }
        },
        {
            "type": "section",
            "fields": [
                {
                    "type": "mrkdwn",
                    "text": "*Level:*\n{{alert.level}}"
                },
                {
                    "type": "mrkdwn",
                    "text": "*Value:*\n{{alert.value}}"
                }
            ]
        }
    ]
}
```

### Teams Card
```json
{
    "type": "message",
    "attachments": [
        {
            "contentType": "application/vnd.microsoft.card.adaptive",
            "content": {
                "type": "AdaptiveCard",
                "body": [
                    {
                        "type": "TextBlock",
                        "size": "Medium",
                        "weight": "Bolder",
                        "text": "Alert: {{alert.type}}"
                    },
                    {
                        "type": "FactSet",
                        "facts": [
                            {
                                "title": "Level:",
                                "value": "{{alert.level}}"
                            },
                            {
                                "title": "Value:",
                                "value": "{{alert.value}}"
                            }
                        ]
                    }
                ]
            }
        }
    ]
}
```

## Configuration

### Environment Variables

```env
# Email Configuration
SMTP_HOST=smtp.example.com
SMTP_PORT=587
SMTP_USER=user@example.com
SMTP_PASSWORD=password
SMTP_FROM=noreply@example.com

# Webhook Configuration
WEBHOOK_TIMEOUT=5
WEBHOOK_RETRY_ATTEMPTS=3
WEBHOOK_RETRY_DELAY=1

# Slack Configuration
SLACK_TIMEOUT=5
SLACK_RETRY_ATTEMPTS=3

# Teams Configuration
TEAMS_TIMEOUT=5
TEAMS_RETRY_ATTEMPTS=3
```

### API Endpoints

1. **List Notifications**
   ```
   GET /api/notifications
   ```

2. **Create Notification**
   ```
   POST /api/notifications
   ```

3. **Get Notification**
   ```
   GET /api/notifications/{id}
   ```

4. **Update Notification**
   ```
   PUT /api/notifications/{id}
   ```

5. **Delete Notification**
   ```
   DELETE /api/notifications/{id}
   ```

6. **Get Notification Logs**
   ```
   GET /api/notifications/{id}/logs
   ```

7. **Test Notification**
   ```
   POST /api/notifications/{id}/test
   ```

## Best Practices

1. **Configuration**
   - Use environment variables for sensitive data
   - Configure appropriate timeouts and retry attempts
   - Enable notifications only when needed
   - Use descriptive names for notification configurations

2. **Templates**
   - Keep templates simple and readable
   - Include essential information only
   - Use consistent formatting
   - Test templates with different alert types

3. **Monitoring**
   - Regularly check notification logs
   - Monitor delivery success rates
   - Set up alerts for notification failures
   - Review and update configurations periodically

4. **Security**
   - Use secure connections (HTTPS)
   - Implement proper authentication
   - Rotate credentials regularly
   - Limit access to notification settings

## Troubleshooting

### Common Issues

1. **Email Notifications Not Sent**
   - Check SMTP configuration
   - Verify recipient addresses
   - Check spam filters
   - Review email server logs

2. **Webhook Failures**
   - Verify endpoint URL
   - Check authentication
   - Review network connectivity
   - Check payload format

3. **Slack/Teams Integration Issues**
   - Verify webhook URLs
   - Check channel permissions
   - Review message formatting
   - Check rate limits

### Debugging Steps

1. Check notification logs
2. Verify configuration settings
3. Test with simple messages
4. Review network connectivity
5. Check authentication
6. Verify template formatting

## Integration Examples

### Python
```python
import requests

# Create email notification
email_config = {
    "name": "API Alerts",
    "type": "email",
    "enabled": True,
    "config": {
        "recipients": ["team@example.com"],
        "subject_template": "Alert: {{alert.type}}"
    }
}

response = requests.post(
    "http://api.example.com/notifications",
    json=email_config,
    headers={"Authorization": "Bearer token"}
)
```

### JavaScript
```javascript
// Create webhook notification
const webhookConfig = {
    name: "API Monitoring",
    type: "webhook",
    enabled: true,
    config: {
        url: "https://example.com/webhook",
        method: "POST"
    }
};

fetch("http://api.example.com/notifications", {
    method: "POST",
    headers: {
        "Authorization": "Bearer token",
        "Content-Type": "application/json"
    },
    body: JSON.stringify(webhookConfig)
});
```

## Maintenance

### Regular Tasks
1. Review notification configurations
2. Check delivery success rates
3. Update templates as needed
4. Rotate credentials
5. Clean up old logs

### Backup and Recovery
1. Export notification configurations
2. Backup templates
3. Document integration settings
4. Test recovery procedures
5. Maintain contact lists 