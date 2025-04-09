# API Key Documentation

## Overview

API keys are used to authenticate and authorize access to the API. Each user can create multiple API keys with different permissions and purposes.

## Authentication

All API requests must include an API key in the `X-API-Key` header:

```http
X-API-Key: your_api_key_here
```

## API Key Management

### Create API Key

```http
POST /api/v1/api-keys
```

Request body:
```json
{
    "name": "My API Key",
    "description": "API key for my application"
}
```

Response:
```json
{
    "id": 1,
    "name": "My API Key",
    "description": "API key for my application",
    "key": "generated_api_key",
    "is_active": true,
    "created_at": "2024-03-20T12:00:00Z",
    "last_used": null,
    "usage_count": 0
}
```

### List API Keys

```http
GET /api/v1/api-keys?page=1&size=10
```

Query parameters:
- `page`: Page number (default: 1)
- `size`: Items per page (default: 10)

Response:
```json
{
    "api_keys": [
        {
            "id": 1,
            "name": "My API Key",
            "description": "API key for my application",
            "is_active": true,
            "created_at": "2024-03-20T12:00:00Z",
            "last_used": "2024-03-21T15:30:00Z",
            "usage_count": 42
        }
    ],
    "total": 1,
    "page": 1,
    "size": 10
}
```

### Get API Key Details

```http
GET /api/v1/api-keys/{api_key_id}
```

Response:
```json
{
    "id": 1,
    "name": "My API Key",
    "description": "API key for my application",
    "is_active": true,
    "created_at": "2024-03-20T12:00:00Z",
    "last_used": "2024-03-21T15:30:00Z",
    "usage_count": 42,
    "usage": [
        {
            "id": 1,
            "endpoint": "/api/v1/tickets",
            "method": "GET",
            "status_code": 200,
            "response_time": 0.15,
            "created_at": "2024-03-21T15:30:00Z"
        }
    ]
}
```

### Update API Key

```http
PUT /api/v1/api-keys/{api_key_id}
```

Request body:
```json
{
    "name": "Updated API Key",
    "description": "Updated description",
    "is_active": true
}
```

Response:
```json
{
    "id": 1,
    "name": "Updated API Key",
    "description": "Updated description",
    "is_active": true,
    "created_at": "2024-03-20T12:00:00Z",
    "last_used": "2024-03-21T15:30:00Z",
    "usage_count": 42
}
```

### Delete API Key

```http
DELETE /api/v1/api-keys/{api_key_id}
```

Response:
```json
{
    "message": "API key deleted successfully"
}
```

## Usage Statistics

### Dashboard Statistics

```http
GET /api/v1/dashboard/stats
```

Response:
```json
{
    "open_tickets": 5,
    "resolved_tickets": 10,
    "active_api_keys": 2,
    "total_api_calls": 100,
    "api_usage": {
        "success_rate": 95.5,
        "avg_response_time": 0.15
    },
    "recent_tickets": [
        {
            "id": 1,
            "subject": "Ticket Subject",
            "status": "open",
            "created_at": "2024-03-21T15:30:00Z"
        }
    ],
    "api_keys": [
        {
            "id": 1,
            "name": "My API Key",
            "is_active": true,
            "usage_count": 42,
            "last_used": "2024-03-21T15:30:00Z"
        }
    ]
}
```

## Best Practices

1. **Key Security**
   - Store API keys securely
   - Never commit API keys to version control
   - Rotate API keys regularly
   - Use different API keys for different applications

2. **Usage Monitoring**
   - Monitor API key usage regularly
   - Set up alerts for unusual activity
   - Review and revoke unused API keys

3. **Error Handling**
   - Handle API key errors gracefully
   - Implement retry logic with exponential backoff
   - Log API key usage for debugging

4. **Rate Limiting**
   - Respect rate limits
   - Implement caching where appropriate
   - Use bulk endpoints when available

## Error Codes

| Code | Description |
|------|-------------|
| 401  | Invalid or missing API key |
| 403  | API key is inactive |
| 429  | Rate limit exceeded |
| 500  | Internal server error |

## Rate Limits

- 100 requests per minute per API key
- 1000 requests per hour per API key
- 10000 requests per day per API key

Rate limit headers:
- `X-RateLimit-Limit`: Maximum requests per time window
- `X-RateLimit-Remaining`: Remaining requests in current window
- `X-RateLimit-Reset`: Time until rate limit resets (UTC timestamp) 