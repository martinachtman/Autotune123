# Autotune123 - Modern Python Autotune Implementation

A modern, Docker-based implementation of OpenAPS autotune functionality with an enhanced web interface.

## 🎯 **Key Features**

✅ **Modern Python Implementation** - Pure Python rewrite, no bash scripts or oref0 dependencies  
✅ **Aggressive Autotune Mode** - Enhanced sensitivity option for detecting subtle insulin changes  
✅ **Enhanced Web Interface** - Interactive Dash application with real-time feedback  
✅ **Docker-Based Deployment** - Easy setup and consistent execution environment  
✅ **Comprehensive Testing** - Full test suite with unit, integration, and performance tests  
✅ **Production Ready** - Environment variable configuration and security features  

## Aggressive Autotune Mode

This implementation includes an optional **Aggressive Mode** with enhanced sensitivity:

- **Standard Mode**: Uses OpenAPS reference thresholds (±20 mg/dL, 3+ data points)
- **Aggressive Mode**: Enhanced sensitivity (±10 mg/dL, 2+ data points) for detecting subtle changes
- **Toggle Option**: Easy switching between modes via web interface
- **Full Documentation**: Clear references to original OpenAPS algorithm parameters

**When to use Aggressive Mode:**
- You suspect insulin sensitivity changes that standard mode doesn't detect
- You want more responsive basal rate adjustments
- Your glucose control is stable and you want fine-tuning

**Reference**: Based on OpenAPS autotune algorithm parameters documented at:
- https://openaps.readthedocs.io/en/latest/docs/Customize-Iterate/autotune.html
- https://github.com/openaps/oref0/tree/master/bin

---

*This modernized version is based on the original [Autotune123](https://github.com/KelvinKramp/Autotune123) project by Kelvin Kramp.*

## What is Autotune123?

Autotune123 is a web application for type 1 diabetics to configure their insulin pump basal rate. It provides:

- **Web-based interface** - No command line required
- **Visual dashboard** - See your current profile and recommendations graphically  
- **Savitzky-Golay filtering** - Smooth out recommendations
- **Direct Nightscout integration** - Fetch profiles and upload results
- **Multiple profile support** - Select and modify specific Nightscout profiles
- **Profile activation** - Directly activate recommendations on your pump
- **Real-time adjustments** - Modify individual basal values before activation
- **JSON profile export** - Download Nightscout-compatible profile files

## Features

### Core Functionality
- **Visualisation of recommendations** - Interactive charts and tables
- **Multiple profile management** - Select, compare, and modify any Nightscout profile
- **Enhanced download options** - Clean CSV, Excel, and text exports
- **Direct activation of recommendations** on pump
- **Real-time adjustments** - Change individual basal values before activation
- **Apply smoothing filters** - Savitzky-Golay filtering for smoother recommendations

### Profile Management
- **Profile selection dropdown** - Choose which profile to modify from all available Nightscout profiles
- **Profile browser** - Compare multiple profiles side-by-side with detailed information
- **JSON profile export** - Download Nightscout-compatible profile files
- **Upload options** - Create new profiles or update existing ones with detailed instructions

### Technical Features
- **Switch between insulin types** - Fast-acting and ultra-rapid insulin support
- **UAM (Unannounced Meals) option** - Enhanced autotune analysis
- **Web interface accessible from any device** - Responsive design
- **Enhanced error handling** - Better debugging and user feedback

## 🚀 Quick Start

### **Production (Recommended)**

1. **Create environment configuration:**
   ```bash
   # Copy the example configuration
   cp env.example .env
   
   # Edit with your Nightscout details
   nano .env
   ```

2. **Start the application:**
   ```bash
   # Build and run the container
   docker-compose up --build -d
   ```

3. **Access the web interface:**
   - Open http://localhost:8080
   - Your Nightscout details will be pre-populated from `.env`

### **Development**

```bash
# Start development environment (with live reload)
docker-compose --profile dev up --build -d

# Access at http://localhost:5000 (different port to avoid conflicts)
```

### **Testing**

```bash
# Run comprehensive test suite
docker-compose --profile test run --rm autotune123-test

# Run specific test types
docker-compose --profile test run --rm unit-tests
docker-compose --profile test run --rm integration-tests

# Test with your real Nightscout configuration
docker-compose exec autotune123 python3 test_complete_autotune.py
```

## 🐳 Docker Configuration

This project uses a unified Docker setup with profiles for different environments:

### **Available Profiles**

| Profile | Port | Use Case | Command |
|---------|------|----------|---------|
| **Production** (default) | 8080 | Normal usage | `docker-compose up -d` |
| **Development** | 5000 | Live development | `docker-compose --profile dev up -d` |
| **Testing** | None | Automated testing | `docker-compose --profile test run --rm autotune123-test` |

### **Service Details**

#### **autotune123** (Production)
- **Environment**: Production optimized
- **Restart Policy**: Automatic restart
- **Health Check**: HTTP endpoint monitoring
- **Security**: Non-root user, minimal dependencies
- **Use Case**: Standard application deployment

#### **autotune123-dev** (Development)
- **Port**: 5000 (to avoid production conflicts)
- **Volume Mount**: Live source code for instant reload
- **Debug Mode**: Enhanced logging and error details
- **Use Case**: Code development and testing

#### **autotune123-test** (Testing)
- **Environment**: Testing configuration
- **Volume Mounts**: Tests directory and coverage output
- **Coverage Reports**: HTML and terminal formats
- **Use Case**: Comprehensive automated testing

### **Advanced Docker Usage**

#### **Multiple Environments**
```bash
# Run production AND development simultaneously
docker-compose up -d                    # Production on :8080
docker-compose --profile dev up -d      # Development on :5000
```

#### **Log Monitoring**
```bash
# Follow logs for all services
docker-compose logs -f

# Follow logs for specific service
docker-compose logs -f autotune123
docker-compose logs -f autotune123-dev
```

#### **Custom Commands**
```bash
# Run custom command in production container
docker-compose exec autotune123 python3 your_script.py

# Debug with shell access
docker-compose exec autotune123 bash

# Run tests interactively
docker-compose exec autotune123 python3 test_complete_autotune.py
```

### **Direct Docker Usage** (Advanced)

```bash
# Build the container
docker build -t autotune123 .

# Run with environment variables
docker run -p 8080:8080 \
  -e NS_SITE=https://your.nightscout.url \
  -e API_SECRET=your-api-secret \
  autotune123
```

## Usage

1. **Access the web interface** at http://localhost:8080
2. **Nightscout details** will be pre-populated if configured in `.env`
3. **Select insulin type** (Rapid Acting or Ultra Rapid)
4. **Choose profile to modify**:
   - Load Current Profile (default active profile)
   - Select specific profile from dropdown (populated with your Nightscout profiles)
   - Browse All Profiles (detailed comparison view) - *See [Profile Guide](PROFILE_GUIDE.md)*
5. **Select date range** for analysis (up to 14 days)
6. **Run Autotune** analysis
7. **Review recommendations** with optional filtering and real-time editing
8. **Export and upload profiles**:
   - Generate Nightscout-compatible JSON profiles
   - Download profiles for backup or manual upload
   - Get detailed upload instructions for API or web interface
   - *Complete guide: [Profile Management](PROFILE_GUIDE.md)*

## Configuration

### Environment Variables

The application uses environment variables for configuration. Create a `.env` file from the template:

```bash
# Copy the example configuration
cp env.example .env

# Edit with your actual values
nano .env
```

Example `.env` configuration:
```bash
# Nightscout Configuration (required)
NS_SITE=https://your.nightscout.url
API_SECRET=your-api-secret

# Application Settings (optional)
ENV=production
FLASK_DEBUG=false

# Timezone Configuration (CRITICAL - Fallback only)
# Primary: Container inherits host timezone automatically
# Uncomment only if automatic detection fails:
# TIMEZONE=Europe/Amsterdam
```

#### ⚠️ **CRITICAL: Timezone Configuration**

Timezone configuration is **extremely important** and directly affects basal rate scheduling and data interpretation:

**Why it matters:**
- Your insulin pump operates in a specific timezone
- Basal rates are scheduled by time (e.g., "2.0 units/hr at 14:30")
- If Autotune uses a different timezone, basal rates will be applied at the wrong times
- This can cause dangerous high or low blood glucose levels

**Configuration Methods (in order of reliability):**

1. **System Timezone (Recommended)**: The container automatically inherits your host system's timezone via volume mount:
   ```yaml
   volumes:
     - /etc/localtime:/etc/localtime:ro
   ```
   This is the most reliable method and requires no manual configuration. The `/etc/localtime` file contains all necessary timezone information including DST rules.

2. **Environment Variable (Fallback)**: If system timezone detection fails:
   ```bash
   # Set this to match your insulin pump's timezone EXACTLY
   TIMEZONE=Europe/Amsterdam     # Netherlands, Belgium, etc.
   TIMEZONE=America/New_York     # US Eastern Time
   TIMEZONE=Australia/Sydney     # Australian Eastern Time
   TIMEZONE=UTC                  # Default if unset (may cause misalignment)
   ```

**Common timezone formats:**
- `UTC` - Coordinated Universal Time (default)
- `Europe/London` - United Kingdom
- `Europe/Amsterdam` - Netherlands, Belgium
- `Europe/Berlin` - Germany, Austria
- `America/New_York` - US Eastern Time
- `America/Chicago` - US Central Time
- `America/Los_Angeles` - US Pacific Time
- `Australia/Sydney` - Australian Eastern Time
- `Asia/Tokyo` - Japan Standard Time

**IMPORTANT WARNINGS:**
1. **Verify your pump's timezone matches this setting** before using any recommendations
2. **Never change timezone after generating profiles** - this will cause basal rate misalignment
3. **If in doubt, consult your healthcare team** about proper timezone configuration
4. **Test with small changes first** - don't apply large basal rate adjustments immediately

**Important**: 
- The `.env` file contains sensitive information and should not be committed to version control
- The `.env` file is automatically loaded by docker-compose
- Pre-configuring these values will auto-populate the web interface forms

## Available Modes

- **Production** (default): Optimized for production use
- **Development**: Enhanced logging and debugging

Set the mode in your `.env` file:
```bash
# Production mode (default)
ENV=production

# Development mode (verbose logging)
ENV=development
```

## Requirements

### For Autotune123 to work properly:

- **Nightscout account** properly configured
- **Accurate carb logging** in amount and time
- **Proper pump disconnection logging** when physically disconnected
- **Nightscout synchronization enabled** for profile uploads:
  - "Upload data to nightscout" turned on
  - "Receive profile store" turned on  
  - "Receive profile switches" turned on

## Important Safety Information

> ⚠️ **Warning**: Autotune is a tool to help calculate potential adjustments to ISF, carb ratio, and basal rates. Do not blindly make changes to your pump settings without careful consideration. Always review recommendations with your care team and consider using 3-4 weeks of data before making long-term changes.

## 🛠️ Development Setup

### **Getting Started**
```bash
# Clone this repository
git clone <this-repository>
cd <repository-directory>

# Set up configuration
cp env.example .env
nano .env  # Add your Nightscout details
```

### **Development Workflow**
```bash
# Start development environment (live reload enabled)
docker-compose --profile dev up --build -d

# Access development server at http://localhost:5000
# Changes to code will automatically reload

# View development logs
docker-compose logs -f autotune123-dev

# Stop development environment
docker-compose --profile dev down
```

### **Testing Workflow**
```bash
# Run comprehensive test suite
docker-compose --profile test run --rm autotune123-test

# Run specific test categories
docker-compose --profile test run --rm unit-tests          # Fast unit tests
docker-compose --profile test run --rm integration-tests   # Integration tests

# Test with real Nightscout data (requires .env configuration)
docker-compose exec autotune123 python3 test_complete_autotune.py
```

### **Production Testing**
```bash
# Build and test production configuration
docker-compose up --build -d

# Verify application is working
curl http://localhost:8080

# Check logs for issues
docker-compose logs autotune123
```

## 🔧 Troubleshooting

### **Docker Issues**

#### **Container won't start**
```bash
# Check if port is in use
lsof -i :8080

# Verify Docker is running
docker --version
docker-compose --version

# Check container logs
docker-compose logs autotune123
```

#### **Port conflicts**
```bash
# If port 8080 is in use, find what's using it
lsof -i :8080

# Kill the process or use development profile on port 5000
docker-compose --profile dev up -d  # Uses port 5000
```

#### **Profile not found errors**
```bash
# Ensure you specify the profile for dev/test services
docker-compose up autotune123-dev    # ❌ Won't work
docker-compose --profile dev up -d   # ✅ Correct

docker-compose --profile test run --rm autotune123-test  # ✅ Correct
```

### **Application Issues**

#### **Web interface not accessible**
- Ensure the container is running: `docker-compose ps`
- Check firewall settings for port 8080
- Verify you're accessing http://localhost:8080
- For development: use http://localhost:5000

#### **Configuration issues**
- Ensure `.env` file exists and contains valid values
- Check that NS_SITE doesn't have a trailing slash
- Verify API_SECRET has correct permissions in Nightscout
- Test configuration: `docker-compose exec autotune123 python3 test_complete_autotune.py`

### **Nightscout Integration Issues**

#### **Autotune analysis fails**
- **"TypeError: string indices must be integers"**: Nightscout returned an error instead of profile data
  - Verify your Nightscout URL is correct and accessible
  - Check that your API secret has the correct permissions
  - Ensure your Nightscout has at least one profile configured  
  - Test API access: `curl "https://your-nightscout-url/api/v1/profile.json?token=your-api-secret"`

#### **API Authentication Issues**
- **URL format**: Use `https://yourname.herokuapp.com` (no trailing slash)
- **API Secret**: Must have `readable` permission for profiles
- **Profile missing**: Ensure at least one profile exists in Nightscout
- **Authentication**: API secret should be prefixed with `token=` for API calls

#### **Data Issues**
- Check API secret permissions in Nightscout admin panel
- Ensure sufficient data exists for the selected time period
- Review container logs: `docker-compose logs`
- Test with longer date ranges (7-14 days recommended)

### **Testing Issues**

#### **Test failures**
```bash
# Run tests with verbose output
docker-compose --profile test run --rm autotune123-test

# Debug failed tests interactively
docker-compose run --rm --entrypoint bash autotune123-test

# Check test configuration
docker-compose exec autotune123 python3 test_complete_autotune.py
```

#### **Coverage issues**
```bash
# Generate coverage report
docker-compose --profile test run --rm autotune123-test

# View coverage report (generated in ./coverage directory)
open coverage/htmlcov/index.html
```

## 📚 Documentation

### **Main Documentation**

| Document | Purpose | Audience |
|----------|---------|----------|
| **[PROFILE_GUIDE.md](PROFILE_GUIDE.md)** | Complete profile management, comparison, and upload guide | Users managing pump profiles |
| **[TEST_SETUP_GUIDE.md](TEST_SETUP_GUIDE.md)** | Step-by-step testing with real Nightscout configuration | Users testing functionality |



### **Testing Documentation**

| Document | Purpose | Audience |
|----------|---------|----------|
| **[tests/README.md](tests/README.md)** | Test suite overview and running instructions | Developers |
| **[tests/testdata/README.md](tests/testdata/README.md)** | Test data files and formats explanation | Developers |

### **Quick Start Paths**

#### **For New Users**
1. **Start here**: Complete setup and basic usage (this document)
2. **Then explore**: [PROFILE_GUIDE.md](PROFILE_GUIDE.md) - Advanced profile features

#### **For Developers**
1. **Application Overview**: Architecture and configuration (this document)
2. **Testing**: [tests/README.md](tests/README.md) - Running and contributing to tests
3. **Test Data**: [tests/testdata/README.md](tests/testdata/README.md) - Understanding test formats

#### **For Healthcare Providers**
1. **Safety Information**: [Important Safety Information](#important-safety-information) - Critical safety warnings
2. **Profile Management**: [PROFILE_GUIDE.md](PROFILE_GUIDE.md) - Patient profile oversight tools

## 🌐 **Nginx Reverse Proxy Setup**

For production deployments behind a reverse proxy, use the included nginx configuration:

### **Basic Setup**

1. **Start Autotune123:**
   ```bash
   docker-compose up -d
   # Autotune123 will be running on localhost:8080
   ```

2. **Configure Nginx:**
   ```bash
   # Copy the sample configuration
   sudo cp nginx-autotune.conf /etc/nginx/sites-available/autotune123
   
   # Enable the site
   sudo ln -s /etc/nginx/sites-available/autotune123 /etc/nginx/sites-enabled/
   
   # Test configuration
   sudo nginx -t
   
   # Reload nginx
   sudo systemctl reload nginx
   ```

3. **Access via Nginx:**
   - Visit `http://your-server/` (nginx will proxy to Autotune123)
   - Direct access still available at `http://your-server:8080`

### **Configuration Notes**

The `nginx-autotune.conf` provides:
- **Simple reverse proxy** to localhost:8080
- **Basic security headers** for protection
- **Static asset caching** for better performance  
- **Proper proxy headers** for client IP forwarding

### **For Path-Based Setup** (e.g., `/autotune`)

Modify the nginx config location block:
```nginx
location /autotune/ {
    proxy_pass http://127.0.0.1:8080/;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
}
```

## Support

- **Original Autotune123**: https://github.com/KelvinKramp/Autotune123
- **OpenAPS Autotune Documentation**: https://openaps.readthedocs.io/en/latest/docs/Customize-Iterate/autotune.html
- **Report Issues**: Create an issue in the repository

## License

This project follows the same license as the original Autotune123 project (MIT License).
