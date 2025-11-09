# 🐳 Docker Configuration Guide

This document explains the unified Docker setup for Autotune123 with different profiles for production, development, and testing.

## 📋 **AVAILABLE PROFILES**

### **Production (Default)**
```bash
# Standard production deployment
docker-compose up -d

# Or explicitly
docker-compose --profile production up -d
```

### **Development** 
```bash
# Development with live reload
docker-compose --profile dev up -d

# Access at http://localhost:5000 (different port to avoid conflicts)
```

### **Testing**
```bash
# Run comprehensive test suite
docker-compose --profile test run --rm autotune123-test

# Run specific test categories
docker-compose --profile test run --rm unit-tests
docker-compose --profile test run --rm integration-tests
```

---

## 🎯 **USAGE SCENARIOS**

### **Standard Usage (Production)**
```bash
# 1. Configure environment
cp env.example .env
nano .env  # Add your Nightscout details

# 2. Start application
docker-compose up -d

# 3. Access web interface
open http://localhost:8080
```

### **Development Workflow**
```bash
# 1. Start development environment
docker-compose --profile dev up -d

# 2. Access development server (with live reload)
open http://localhost:5000

# 3. Make code changes - they reload automatically

# 4. Stop development
docker-compose --profile dev down
```

### **Testing Workflow**
```bash
# 1. Run complete test suite
docker-compose --profile test run --rm autotune123-test

# 2. Run specific tests
docker-compose --profile test run --rm unit-tests

# 3. Test with real configuration
docker-compose exec autotune123 python3 test_complete_autotune.py
```

---

## 🔧 **SERVICE DETAILS**

### **autotune123** (Production)
- **Port**: 8080
- **Environment**: Production 
- **Restart**: Automatic
- **Health Check**: Enabled
- **Use Case**: Normal application usage

### **autotune123-dev** (Development)
- **Port**: 5000 (to avoid conflicts)
- **Environment**: Development
- **Volume Mount**: Live source code
- **Debug Mode**: Enabled
- **Use Case**: Code development and debugging

### **autotune123-test** (Testing)
- **Container**: Runs once and exits
- **Environment**: Testing
- **Volume Mount**: Tests directory
- **Coverage**: HTML and terminal reports
- **Use Case**: Comprehensive testing with coverage

### **unit-tests** (Unit Testing)
- **Container**: Runs once and exits
- **Environment**: Testing
- **Scope**: Unit tests only
- **Use Case**: Fast unit test validation

### **integration-tests** (Integration Testing)
- **Container**: Runs once and exits
- **Environment**: Testing with .env config
- **Scope**: Integration tests only
- **Use Case**: Testing with real Nightscout data

---

## 📊 **COMPARISON**

| Profile | Port | Environment | Volume Mounts | Use Case |
|---------|------|-------------|---------------|----------|
| **Production** | 8080 | Production | Timezone only | Normal usage |
| **Development** | 5000 | Development | Source code + timezone | Live development |
| **Testing** | None | Testing | Tests + coverage | Automated testing |

---

## 🛠️ **ADVANCED USAGE**

### **Multiple Profiles**
```bash
# Run production and development simultaneously  
docker-compose --profile dev up -d
# Production runs on :8080, development on :5000
```

### **Custom Commands**
```bash
# Run custom command in production container
docker-compose exec autotune123 python3 your_script.py

# Run custom command in development container  
docker-compose exec autotune123-dev python3 your_script.py

# Debug with shell access
docker-compose exec autotune123 bash
```

### **Log Monitoring**
```bash
# Follow logs for all services
docker-compose logs -f

# Follow logs for specific service
docker-compose logs -f autotune123
docker-compose logs -f autotune123-dev
```

---

## 🔄 **MIGRATION FROM OLD SETUP**

### **Before (Separate Files)**
```bash
# Old way with separate files
docker-compose -f docker-compose.test.yml up    # Testing
docker build -f Dockerfile.test .               # Test builds
```

### **After (Unified Setup)**
```bash
# New way with profiles
docker-compose --profile test run --rm autotune123-test  # Testing
docker-compose up -d                                     # Production
docker-compose --profile dev up -d                       # Development
```

### **Benefits of Unified Setup**
- ✅ **Single Configuration** - One docker-compose.yml for everything
- ✅ **No Duplicate Dockerfiles** - One Dockerfile handles all cases
- ✅ **Profile-based Selection** - Choose what you need
- ✅ **Simplified Maintenance** - Fewer files to maintain
- ✅ **Cleaner Repository** - Less configuration sprawl

---

## 🔍 **TROUBLESHOOTING**

### **Port Conflicts**
```bash
# If port 8080 is in use
docker-compose down
lsof -i :8080  # Find what's using the port
# Kill the process or change port in docker-compose.yml
```

### **Profile Not Found**
```bash
# Ensure you specify the profile for dev/test services
docker-compose up autotune123-dev    # ❌ Won't work
docker-compose --profile dev up -d   # ✅ Correct
```

### **Volume Mount Issues**  
```bash
# Check volume mounts
docker-compose exec autotune123 ls -la /app/Autotune123/

# For development, ensure source code is mounted
docker-compose exec autotune123-dev ls -la /app/Autotune123/
```

### **Test Failures**
```bash
# Run tests with verbose output
docker-compose --profile test run --rm autotune123-test

# Debug failed tests interactively
docker-compose run --rm --entrypoint bash autotune123-test
```

---

## 📚 **RELATED DOCUMENTATION**

- **[TEST_SETUP_GUIDE.md](TEST_SETUP_GUIDE.md)** - Testing with real Nightscout data
- **[README.md](README.md)** - Main application documentation
- **[tests/README.md](tests/README.md)** - Detailed testing information

---

*This unified Docker setup provides a clean, maintainable configuration for all development, testing, and production needs.*