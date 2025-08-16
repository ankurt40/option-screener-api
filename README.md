# Option Screener API

A FastAPI-based Python application for screening stock options from NSE (National Stock Exchange) with support for multiple data sources including NSE API and Dhan API.

## Features

- 📈 **Option Chain Data**: Fetch real-time option chain data for NSE stocks
- 📊 **Analytics**: Calculate strike analytics including premium percentages and strike gaps
- 🎯 **Multiple Data Sources**: Support for NSE API and Dhan API
- 📋 **Stock Listings**: Get comprehensive stock lists from various exchanges
- 🗞️ **Corporate Announcements**: Access corporate announcement data
- ⚡ **Caching**: Built-in caching for improved performance
- 🔍 **Advanced Filtering**: Filter options by various criteria

## API Endpoints

- `GET /` - Health check and API information
- `GET /api/v1/option-chain` - Get option chain data (NSE API)
- `GET /api/v1/dhan/option-chain-by-symbol` - Get option chain by symbol (Dhan API)
- `GET /api/v1/analytics/option-scanner` - Advanced option screening
- `GET /api/v1/stocks/list` - Get stock listings
- `GET /api/v1/corporate-announcements` - Get corporate announcements
- `GET /api/v1/cache/info` - Cache information and management

## Setup

1. Create a virtual environment:
   ```bash
   python -m venv venv
   ```

2. Activate the virtual environment:
   ```bash
   # On macOS/Linux
   source venv/bin/activate
   
   # On Windows
   venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Run the application:
   ```bash
   python main.py
   ```

The API will be available at `http://localhost:8000`

## Development

Install development dependencies:
```bash
pip install -r requirements-dev.txt
```

## Deployment to Fly.io

### Prerequisites

1. **Install Fly CLI**:
   ```bash
   curl -L https://fly.io/install.sh | sh
   ```

2. **Add Fly CLI to PATH** (add to your `.bashrc` or `.zshrc`):
   ```bash
   export FLYCTL_INSTALL="$HOME/.fly"
   export PATH="$FLYCTL_INSTALL/bin:$PATH"
   ```

3. **Authenticate with Fly.io**:
   ```bash
   flyctl auth login
   ```

### Initial Deployment

1. **Initialize your Fly.io app** (first time only):
   ```bash
   flyctl launch
   ```
   
   This will:
   - Create a `fly.toml` configuration file
   - Set up your app on Fly.io
   - Build and deploy your Docker image

2. **Configure your app settings** during the interactive setup:
   - Choose your app name (or use the generated one)
   - Select your preferred region
   - Configure resources (1GB RAM recommended)

### Subsequent Deployments

For updates after the initial deployment:

```bash
flyctl deploy
```

### Deployment Management Commands

#### **Monitoring & Status**
```bash
# Check app status
flyctl status

# View real-time logs
flyctl logs

# Follow logs in real-time
flyctl logs -f

# Open app in browser
flyctl open

# Monitor app performance
flyctl monitor
```

#### **App Management**
```bash
# View app information
flyctl info

# Scale your app (increase instances)
flyctl scale count 2

# SSH into your running app
flyctl ssh console

# Restart your app
flyctl apps restart
```

#### **Cache Management**
```bash
# Clear deployment cache if needed
flyctl deploy --no-cache
```

### Environment Variables

If your app requires environment variables, set them using:

```bash
# Set environment variables
flyctl secrets set API_KEY=your_api_key

# List all secrets
flyctl secrets list

# Remove a secret
flyctl secrets unset API_KEY
```

### Dockerfile Optimization

The project includes an optimized multi-stage Dockerfile that:
- Uses Python 3.11 slim base image
- Implements multi-stage build for smaller image size
- Runs as non-root user for security
- Includes health checks
- Caches dependencies effectively

### Troubleshooting Deployment

1. **Build Issues**:
   ```bash
   # Check build logs
   flyctl logs --app your-app-name
   
   # Deploy with verbose output
   flyctl deploy --verbose
   ```

2. **App Not Responding**:
   - Ensure your app listens on `0.0.0.0:8000`
   - Check the `fly.toml` port configuration
   - Verify health check endpoint

3. **Memory Issues**:
   ```bash
   # Scale up memory if needed
   flyctl scale memory 1024
   ```

4. **View Detailed App Status**:
   ```bash
   flyctl status --all
   ```

### Custom Domain (Optional)

To use a custom domain:

```bash
# Add your domain
flyctl certs add yourdomain.com

# Check certificate status
flyctl certs show yourdomain.com
```

### Production Considerations

- **Scaling**: Use `flyctl scale` to adjust resources based on traffic
- **Monitoring**: Set up monitoring and alerts through Fly.io dashboard
- **Backups**: Implement data backup strategies if using databases
- **Security**: Keep your `access_token` and other secrets secure using Fly secrets

## Project Structure

```
option-screener-api/
├── main.py                     # FastAPI application entry point
├── Dockerfile                  # Multi-stage Docker build configuration
├── fly.toml                   # Fly.io deployment configuration
├── requirements.txt           # Production dependencies
├── requirements-dev.txt       # Development dependencies
├── docker-compose.yml         # Local development setup
├── .gitignore                # Git ignore rules
├── .dockerignore             # Docker ignore rules
├── src/                      # Source code
│   ├── __init__.py
│   ├── controllers/          # API route controllers
│   │   ├── option_chain_controller.py
│   │   ├── dhan_controller.py
│   │   ├── analytics_controller.py
│   │   ├── corporate_announcements_controller.py
│   │   ├── list_stocks_controller.py
│   │   └── cache_controller.py
│   ├── services/            # Business logic services
│   │   ├── nse_service.py
│   │   ├── dhan_service.py
│   │   └── analytics_service.py
│   ├── models/             # Data models
│   │   └── option_models.py
│   └── data/              # Static data files
│       └── fno-symbols-dhan.json
├── frontend/              # Frontend application (if applicable)
└── tests/                # Test files
```

## API Documentation

Once deployed, visit your app URL to access:
- **Interactive API Documentation**: `https://your-app.fly.dev/docs`
- **Alternative Documentation**: `https://your-app.fly.dev/redoc`

## Data Sources

- **NSE India API**: Real-time option chain data from National Stock Exchange
- **Dhan API**: Alternative data source for option chains and analytics

## References

- [NSE India API Documentation](https://bennythadikaran.github.io/NseIndiaApi/usage.html)
- [Fly.io Documentation](https://fly.io/docs/)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)

## Support

For deployment issues or questions:
1. Check the Fly.io logs: `flyctl logs`
2. Review the Fly.io documentation
3. Check the GitHub issues for common problems
