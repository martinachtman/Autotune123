# 🧪 Complete Autotune Test - Setup Guide

This test validates the complete autotune pipeline using your real Nightscout configuration.

## 📋 **SETUP STEPS**

### 1. **Configure Environment File**
```bash
# Copy the example configuration
cp env.example .env

# Edit with your actual Nightscout details
nano .env
```

**Required .env content:**
```bash
# Your actual Nightscout URL
NS_SITE=https://yourname.herokuapp.com

# Your actual API secret (without 'token=' prefix)
API_SECRET=your-real-api-secret-here

# Optional: Set environment type
ENV=development
```

### 2. **Start the Container**
```bash
# Build and start with your .env configuration
docker-compose up --build -d

# Verify container is running
docker-compose ps
```

### 3. **Run the Test**
```bash
# Execute the complete test
docker-compose exec autotune123 python3 test_complete_autotune.py

# Alternative: Run test profile with comprehensive test suite
docker-compose --profile test run --rm autotune123-test

# Run specific test categories
docker-compose --profile test run --rm unit-tests
docker-compose --profile test run --rm integration-tests

# Interactive testing
docker-compose exec autotune123 bash
python3 test_complete_autotune.py
```

## 🎯 **WHAT THE TEST DOES**

### **Configuration Validation**
- ✅ Checks if .env file is properly configured
- ✅ Validates Nightscout URL and API secret are set
- ✅ Prevents running with placeholder values

### **Pipeline Testing**
1. **Profile Loading** - Tests fetching profile from your Nightscout
2. **Autotune Execution** - Runs complete autotune analysis
3. **File Output Check** - Verifies all expected files are created
4. **Results Validation** - Checks data structure and content

### **Date Range**
- **Default**: Last 3 days from current date
- **Automatic**: Updates daily for current testing
- **Realistic**: Uses recent data for meaningful results

## ⚠️ **IMPORTANT NOTES**

### **Security**
- ✅ **Uses real credentials** - Test runs with your actual Nightscout data
- ✅ **No hardcoded secrets** - All sensitive data from .env file
- ✅ **Safe execution** - Runs in isolated container environment

### **Data Requirements**
- **Minimum**: 1-2 days of glucose and treatment data
- **Optimal**: 3-7 days for meaningful results
- **Quality**: Ensure accurate carb logging and pump disconnections

### **Expected Behavior**
- **First Run**: May take 2-3 minutes to complete
- **Network Dependent**: Requires Nightscout connectivity
- **Data Dependent**: Results vary based on available data quality

## 🔧 **TROUBLESHOOTING**

### **Configuration Issues**
```bash
❌ NS_SITE not found in environment
```
**Solution**: Check .env file exists and contains `NS_SITE=https://...`

```bash
❌ API_SECRET is still placeholder value  
```
**Solution**: Replace `your-api-secret-here` with your real API secret

### **Connection Issues**
```bash
❌ Profile loading failed: HTTP 401 Unauthorized
```
**Solution**: Verify API secret has correct permissions in Nightscout admin

```bash
❌ Profile loading failed: Connection timeout
```
**Solution**: Check Nightscout URL is accessible and correct

### **Data Issues**
```bash
❌ No data found for date range
```
**Solution**: Try longer date range or verify data exists in Nightscout

### **Container Issues**
```bash
❌ ModuleNotFoundError: No module named 'autotune'
```
**Solution**: Rebuild container with `docker-compose up --build`

## 📊 **INTERPRETING RESULTS**

### **Successful Test Output**
```
✅ Profile loaded successfully
✅ Autotune execution completed
✅ /root/myopenaps/settings/profile.json (1234 bytes)
✅ /root/myopenaps/autotune_recommendations.log (5678 bytes)
```

### **Expected Files Created**
- `pumpprofile.json` - Current pump profile
- `profile.json` - Nightscout profile format
- `autotune.json` - Autotune-ready profile
- `autotune.YYYY-MM-DD.json` - Daily analysis results
- `autotune_recommendations.log` - Final recommendations

### **Performance Indicators**
- **Execution Time**: 30 seconds - 3 minutes (normal)
- **Profile Size**: 500-2000 bytes (typical)
- **Recommendations**: 10-50 entries (depends on profile complexity)

## 🚀 **NEXT STEPS**

### **After Successful Test**
1. **Review Results**: Check autotune_recommendations.log content
2. **Web Interface**: Test complete workflow at http://localhost:8080
3. **Profile Upload**: Test uploading recommendations to Nightscout
4. **Production Use**: Run with longer date ranges (7-14 days)

### **For Development**
1. **Debug Mode**: Set `ENV=development` in .env for verbose logging
2. **Multiple Runs**: Test with different date ranges
3. **Error Handling**: Review logs for edge cases
4. **Integration**: Validate with web interface workflow

---

*This test validates the complete autotune pipeline end-to-end using your real Nightscout configuration in a safe, containerized environment.*