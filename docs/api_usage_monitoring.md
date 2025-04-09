# API Usage Monitoring

## Overview

The API Usage Monitoring system provides comprehensive tracking and rate limiting for API endpoints. It includes:

- API key validation and authentication
- Rate limiting with multiple time windows
- Usage statistics and logging
- Response time tracking
- Error handling and reporting

## Configuration

### Rate Limits

The system supports three levels of rate limiting:

```python
RATE_LIMITS = {
    "minute": 100,  # Requests per minute
    "hour": 1000,   # Requests per hour
    "day": 10000    # Requests per day
}
```

### Response Time Thresholds

Response time thresholds for monitoring:

```python
RESPONSE_TIME_THRESHOLDS = {
    "warning": 1.0,  # Warning threshold in seconds
    "critical": 2.0  # Critical threshold in seconds
}
```

## API Key Headers

All API requests must include the `X-API-Key` header:

```
X-API-Key: your_api_key_here
```

## Rate Limit Headers

The system provides detailed rate limit information in response headers:

```
X-RateLimit-Minute-Limit: 100
X-RateLimit-Minute-Remaining: 95
X-RateLimit-Minute-Reset: 60
X-RateLimit-Hour-Limit: 1000
X-RateLimit-Hour-Remaining: 950
X-RateLimit-Hour-Reset: 3600
X-RateLimit-Day-Limit: 10000
X-RateLimit-Day-Remaining: 9500
X-RateLimit-Day-Reset: 86400
```

## Usage Statistics

### API Usage Model

Each API call is logged with the following information:

```python
class APIUsage(Base):
    id: int
    user_id: int
    api_key_id: int
    endpoint: str
    method: str
    status_code: int
    response_time: float
    created_at: datetime
```

### API Key Statistics

API keys track usage statistics:

```python
class APIKey(Base):
    id: int
    user_id: int
    name: str
    description: str
    key: str
    is_active: bool
    usage_count: int
    last_used: datetime
    created_at: datetime
    updated_at: datetime
```

## Error Handling

The system handles various error scenarios:

1. Missing API Key (401):
   ```json
   {
     "detail": "Missing API key"
   }
   ```

2. Invalid API Key (401):
   ```json
   {
     "detail": "Invalid API key"
   }
   ```

3. Inactive API Key (403):
   ```json
   {
     "detail": "API key is inactive"
   }
   ```

4. Rate Limit Exceeded (429):
   ```json
   {
     "detail": "Rate limit exceeded for minute. Try again in 60 seconds"
   }
   ```

5. Server Error (500):
   ```json
   {
     "detail": "Internal server error"
   }
   ```

## Best Practices

1. **API Key Management**
   - Rotate API keys regularly
   - Use descriptive names for API keys
   - Monitor usage patterns for anomalies

2. **Rate Limiting**
   - Implement exponential backoff when hitting rate limits
   - Monitor rate limit headers to optimize request patterns
   - Consider implementing request queuing for high-volume applications

3. **Error Handling**
   - Implement proper error handling for all error responses
   - Log and monitor error patterns
   - Set up alerts for unusual error rates

4. **Performance Monitoring**
   - Monitor response times for performance degradation
   - Set up alerts for slow endpoints
   - Regularly review and optimize slow endpoints

## Integration Examples

### Python Client

```python
import requests
from datetime import datetime

class APIClient:
    def __init__(self, api_key):
        self.api_key = api_key
        self.base_url = "https://api.example.com"
        self.session = requests.Session()
        self.session.headers.update({"X-API-Key": api_key})

    def make_request(self, endpoint, method="GET", **kwargs):
        try:
            response = self.session.request(
                method,
                f"{self.base_url}{endpoint}",
                **kwargs
            )
            
            # Check rate limits
            self._check_rate_limits(response.headers)
            
            return response.json()
        except requests.exceptions.RequestException as e:
            # Handle request errors
            print(f"Request failed: {e}")
            raise

    def _check_rate_limits(self, headers):
        # Monitor rate limits
        for period in ["minute", "hour", "day"]:
            remaining = int(headers.get(f"X-RateLimit-{period.capitalize()}-Remaining", 0))
            if remaining < 10:  # Alert when running low
                print(f"Warning: Low {period} rate limit remaining: {remaining}")
```

### JavaScript Client

```javascript
class APIClient {
    constructor(apiKey) {
        this.apiKey = apiKey;
        this.baseUrl = 'https://api.example.com';
    }

    async makeRequest(endpoint, method = 'GET', options = {}) {
        try {
            const response = await fetch(`${this.baseUrl}${endpoint}`, {
                method,
                headers: {
                    'X-API-Key': this.apiKey,
                    ...options.headers
                },
                ...options
            });

            // Check rate limits
            this.checkRateLimits(response.headers);

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            return await response.json();
        } catch (error) {
            console.error('Request failed:', error);
            throw error;
        }
    }

    checkRateLimits(headers) {
        // Monitor rate limits
        ['minute', 'hour', 'day'].forEach(period => {
            const remaining = parseInt(headers.get(`X-RateLimit-${period}-Remaining`));
            if (remaining < 10) {
                console.warn(`Warning: Low ${period} rate limit remaining: ${remaining}`);
            }
        });
    }
}
```

## Monitoring and Alerts

### Response Time Monitoring

The system tracks response times and can trigger alerts:

1. Warning: Response time > 1.0 seconds
2. Critical: Response time > 2.0 seconds

### Usage Pattern Monitoring

Monitor for unusual patterns:

1. Sudden spikes in request volume
2. Unusual error rates
3. Unauthorized access attempts
4. API key abuse

### Alert Configuration

Configure alerts for:

1. Rate limit approaching (e.g., 80% of limit)
2. Response time thresholds exceeded
3. Error rate thresholds exceeded
4. Unusual usage patterns detected

## Alert System

### Overview

The alert system monitors API usage patterns and triggers notifications when unusual activity is detected. It includes:

- Response time monitoring
- Error rate tracking
- Usage spike detection
- Unauthorized access monitoring

### Alert Types

1. **Response Time Alerts**
   - Warning: > 1.0 seconds
   - Critical: > 2.0 seconds

2. **Error Rate Alerts**
   - Warning: > 5% error rate
   - Critical: > 10% error rate

3. **Usage Spike Alerts**
   - Warning: > 2x normal usage
   - Critical: > 3x normal usage

4. **Unauthorized Access Alerts**
   - Critical: > 5 failed attempts per hour

### Alert Configuration

Alert thresholds can be configured in `app/core/alerts.py`:

```python
alert_thresholds = {
    "response_time": {
        "warning": 1.0,  # seconds
        "critical": 2.0  # seconds
    },
    "error_rate": {
        "warning": 0.05,  # 5%
        "critical": 0.10  # 10%
    },
    "usage_spike": {
        "warning": 2.0,  # 2x normal usage
        "critical": 3.0  # 3x normal usage
    }
}
```

### Alert Processing

Alerts are processed asynchronously and can trigger multiple notification channels:

1. **Logging**
   - Warnings are logged with level WARNING
   - Critical alerts are logged with level CRITICAL

2. **Notifications** (TODO)
   - Email notifications
   - Slack integration
   - Webhook support

### Alert Management

Alerts can be managed through the web interface or API:

1. **View Alerts**
   - List all active alerts
   - Filter by type and severity
   - View alert details

2. **Alert Settings**
   - Configure notification channels
   - Set alert thresholds
   - Manage alert recipients

3. **Alert History**
   - View historical alerts
   - Analyze alert patterns
   - Generate reports

### Integration Examples

#### Python Client

```python
from app.core.alerts import AlertService

# Initialize alert service
alert_service = AlertService(db_session)

# Check for alerts
await alert_service.check_all_alerts(
    api_key_id=123,
    response_time=1.5,
    endpoint="/api/v1/test"
)
```

#### API Endpoints

```python
# Get active alerts
GET /api/v1/alerts

# Get alert history
GET /api/v1/alerts/history

# Update alert settings
PUT /api/v1/alerts/settings

# Acknowledge alert
POST /api/v1/alerts/{alert_id}/acknowledge
```

### Best Practices

1. **Alert Configuration**
   - Set appropriate thresholds based on your application's needs
   - Consider different thresholds for different environments
   - Regularly review and adjust thresholds

2. **Notification Management**
   - Configure multiple notification channels
   - Set up escalation policies
   - Implement alert deduplication

3. **Response Planning**
   - Document response procedures
   - Train team members on alert handling
   - Maintain incident response playbooks

4. **Monitoring and Optimization**
   - Monitor alert frequency
   - Analyze false positives
   - Optimize alert thresholds

### Troubleshooting

1. **Common Issues**
   - Missing alerts
   - False positives
   - Notification delivery failures

2. **Debugging Tools**
   - Alert logs
   - Notification delivery logs
   - Alert history analysis

3. **Resolution Steps**
   - Verify alert configuration
   - Check notification settings
   - Review alert history
   - Test notification channels

## Troubleshooting

### Common Issues

1. **Rate Limit Errors**
   - Check current usage against limits
   - Implement exponential backoff
   - Consider request batching

2. **Authentication Errors**
   - Verify API key is valid and active
   - Check header formatting
   - Ensure proper key rotation

3. **Performance Issues**
   - Monitor response times
   - Check for endpoint optimization
   - Review database queries

4. **Error Handling**
   - Implement proper error handling
   - Log and monitor error patterns
   - Set up error alerts

### Debugging Tools

1. **Logging**
   - Enable detailed logging for debugging
   - Monitor error logs
   - Track usage patterns

2. **Monitoring**
   - Use monitoring tools to track performance
   - Set up alerts for issues
   - Review usage statistics

3. **Testing**
   - Test rate limiting behavior
   - Verify error handling
   - Check performance under load 