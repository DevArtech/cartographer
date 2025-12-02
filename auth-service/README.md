# Cartographer Auth Service

User authentication and authorization microservice for the Cartographer network mapping application.

## Features

- **First-run Setup**: Owner account creation on initial startup
- **JWT Authentication**: Secure token-based authentication
- **Role-based Access Control**:
  - `owner`: Full access - can manage users and modify network map
  - `readwrite`: Can view and modify the network map
  - `readonly`: Can only view the network map
- **User Management**: Create, update, and delete users (owner only)
- **Password Management**: Secure password hashing with bcrypt

## API Endpoints

### Setup
- `GET /api/auth/setup/status` - Check if initial setup is complete
- `POST /api/auth/setup/owner` - Create the initial owner account

### Authentication
- `POST /api/auth/login` - Authenticate and get access token
- `POST /api/auth/logout` - Logout (client-side token discard)
- `GET /api/auth/session` - Get current session info
- `POST /api/auth/verify` - Verify token validity

### User Management (Owner only)
- `GET /api/auth/users` - List all users
- `POST /api/auth/users` - Create a new user
- `GET /api/auth/users/{id}` - Get user by ID
- `PATCH /api/auth/users/{id}` - Update user
- `DELETE /api/auth/users/{id}` - Delete user

### Profile
- `GET /api/auth/me` - Get current user profile
- `PATCH /api/auth/me` - Update current user profile
- `POST /api/auth/me/change-password` - Change password

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `JWT_SECRET` | `cartographer-dev-secret...` | Secret key for JWT signing (change in production!) |
| `JWT_EXPIRATION_HOURS` | `24` | Token expiration time in hours |
| `AUTH_DATA_DIR` | `/app/data` | Directory for persistent user data |
| `CORS_ORIGINS` | `*` | Allowed CORS origins |

## Development

```bash
# Install dependencies
pip install -r requirements.txt

# Run the service
uvicorn app.main:app --host 0.0.0.0 --port 8002 --reload
```

## Docker

```bash
# Build
docker build -t cartographer-auth .

# Run
docker run -p 8002:8002 -v auth-data:/app/data cartographer-auth
```

## Security Notes

1. **Change `JWT_SECRET` in production** - The default is for development only
2. **Use HTTPS in production** - JWT tokens should only be transmitted over secure connections
3. **Password Requirements**: Minimum 8 characters
4. **Token Expiration**: Tokens expire after 24 hours by default

## Data Persistence

User data is stored in JSON format at `$AUTH_DATA_DIR/users.json`. Mount a volume to persist data across container restarts.
