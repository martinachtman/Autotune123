# 📊 Profile Management Guide

Complete guide for managing insulin pump profiles with Autotune123's advanced profile features.

## 🎯 Overview

Autotune123 provides comprehensive profile management capabilities including:

- **Profile Browser** - View and compare all your Nightscout profiles
- **Profile Generation** - Create new profiles from autotune recommendations  
- **Profile Export** - Download profiles as JSON files
- **Upload Integration** - Direct upload to Nightscout or detailed instructions
- **Profile Comparison** - Side-by-side analysis of profile differences

---

## 🔍 **PROFILE BROWSER**

### Accessing Profile Browser
1. Navigate to Step 1 of the Autotune123 interface
2. Enter your Nightscout URL and API secret
3. Click **"Browse Profiles"** instead of "Load Profile"

### Features
- **Profile History**: View all profiles with creation and activation dates
- **Profile Details**: See key parameters (DIA, carb ratios, ISF, targets, total daily basal)
- **Profile Evolution**: Track how your settings have changed over time
- **Selection Interface**: Choose profiles for comparison or modification

### Profile Information Displayed
| Column | Description |
|--------|-------------|
| **Profile Name** | Custom name for the profile |
| **Start Date** | When profile became active |
| **Created At** | When profile was first created |
| **DIA** | Duration of Insulin Action (hours) |
| **Carb Ratio** | Carbs covered per unit of insulin |
| **ISF** | Insulin Sensitivity Factor |
| **Target** | Blood glucose target ranges |
| **Total Daily Basal** | Sum of all basal rates for 24 hours |

---

## ⚖️ **PROFILE COMPARISON**

### How to Compare Profiles
1. In the profile browser, select **exactly 2 profiles** using checkboxes
2. Click **"Compare Selected"** to view differences
3. Review the detailed comparison results

### Comparison Results Include
- **Basic Settings Differences**: Changes in DIA, carb ratio, ISF, and targets
- **Basal Rate Differences**: Time-by-time comparison of basal rates  
- **Percentage Changes**: Shows relative impact of modifications
- **Summary Statistics**: Overall effect on insulin delivery

### Understanding Results
- **🟢 Green Values**: Increases from profile 1 to profile 2
- **🔴 Red Values**: Decreases from profile 1 to profile 2
- **Difference**: Absolute change (Profile 2 - Profile 1)
- **Change %**: Percentage change from original value

---

## 📄 **PROFILE GENERATION & EXPORT**

### After Running Autotune

Once you've completed an autotune analysis, you can:

#### 1. **View Profile JSON**
- Click **"Show Profile JSON"** to see the complete Nightscout-compatible structure
- Review all parameters including basal rates, ISF, carb ratios, and targets
- Validate that all values look correct before export

#### 2. **Download Profile File**
- Click **"Download JSON"** to export as a `.json` file
- **Filename Format**: `autotune_profile_YYYYMMDD_HHMMSS.json`
- **Nightscout Compatible**: Ready for direct upload

#### 3. **Get Upload Instructions**
- Detailed instructions for both API upload and manual entry
- Pre-formatted cURL commands for advanced users
- Step-by-step web interface instructions

### Generated Profile Structure
```json
{
  "_id": "autotune_20251107_113616",
  "defaultProfile": "Autotune_Profile_Name", 
  "store": {
    "Autotune_Profile_Name": {
      "dia": 8.0,
      "carb_ratio": 8.5,
      "carb_ratios": {
        "first": 1,
        "units": "grams", 
        "schedule": [...]
      },
      "isfProfile": {
        "first": 1,
        "sensitivities": [...]
      },
      "basalprofile": [...],
      "bg_targets": {...},
      "timezone": "Europe/Zurich",
      "min_5m_carbimpact": 8.0,
      "autosens_max": 1.2,
      "autosens_min": 0.7
    }
  },
  "startDate": "2025-11-07T11:36:16.722701",
  "created_at": "2025-11-07T11:36:16.722703",
  "mills": 1762515376722
}
```

---

## 📤 **UPLOADING TO NIGHTSCOUT**

### Option A: API Upload (Advanced Users)

#### Prerequisites
- API secret with `api:create` permission
- cURL installed or similar HTTP client

#### Steps
1. Click **"Show Upload Instructions"** in Autotune123
2. Copy the provided cURL command
3. Replace placeholders:
   - `[Your API Secret]` → Your actual API secret
   - `[JSON Profile Data]` → Contents of downloaded JSON file
4. Execute the command:

```bash
curl -X POST "https://your-nightscout-site.com/api/v1/profile" \
  -H "Content-Type: application/json" \
  -H "API-SECRET: your-api-secret" \
  -d @autotune_profile_20251107_113616.json
```

### Option B: Manual Upload (Recommended)

#### Steps
1. **Log into Nightscout**: Access your Nightscout web interface
2. **Open Profile Editor**: Hamburger menu → Profile
3. **Create New Profile**: Click "+" or clone existing profile
4. **Enter Values**: Copy from downloaded JSON:
   - **DIA**: Use `dia` value
   - **Carb Ratios**: Values from `carb_ratios.schedule`
   - **ISF**: Values from `isfProfile.sensitivities`  
   - **Basal Rates**: Values from `basalprofile`
   - **Targets**: Values from `bg_targets.targets`
5. **Save Profile**: Give it a descriptive name
6. **Activate Profile**: Set as active if desired

---

## 🛡️ **SECURITY & SAFETY**

### Security Best Practices
- **🔐 Never share API secrets** - Keep your Nightscout credentials private
- **✅ Verify permissions** - Ensure API secret has correct access levels
- **🔄 Backup profiles** - Always backup current profile before changes
- **🧪 Test small changes** - Don't make large adjustments immediately

### Safety Guidelines
- **👨‍⚕️ Consult healthcare team** - Review significant changes with providers
- **📊 Use sufficient data** - Base profiles on 3-4 weeks of data when possible
- **⚠️ Monitor closely** - Watch blood glucose closely after profile changes
- **🔍 Validate results** - Ensure autotune recommendations make clinical sense

### Profile Validation
The system automatically validates:
- ✅ Required fields are present
- ✅ JSON structure is valid  
- ✅ Numeric values are within reasonable ranges
- ✅ Time schedules are complete (24-hour coverage)

---

## 🔧 **TROUBLESHOOTING**

### Common Issues

#### Profile Browser Problems
- **"No profiles found"** → Check Nightscout URL and API secret
- **"Failed to connect"** → Verify Nightscout site accessibility
- **"API error"** → Ensure API secret has read permissions

#### Export/Download Issues  
- **Profile not showing** → Ensure autotune ran successfully first
- **Download not working** → Check browser download settings and popup blockers
- **Invalid JSON** → Re-run autotune if profile generation failed

#### Upload Problems
- **401 Unauthorized** → Verify API secret and permissions
- **400 Bad Request** → Check JSON structure and required fields
- **Profile not appearing** → May need to refresh Nightscout interface

### API Requirements
- ✅ Nightscout instance with profiles configured
- ✅ API access enabled in Nightscout settings
- ✅ API secret with appropriate read/write permissions
- ✅ Stable network connection

### Debug Steps
1. **Check browser console** for JavaScript errors
2. **Verify Nightscout connectivity** by accessing it directly
3. **Test API access**: `curl "https://your-site.com/api/v1/profile.json?token=your-secret"`
4. **Review autotune logs** for processing errors

---

## 🚀 **ADVANCED FEATURES**

### Multiple Profile Generation
- Generate profiles with different names and parameters
- Keep multiple profile versions organized
- Compare autotune results from different date ranges

### Profile Analytics
- **Total Daily Basal**: Compare insulin delivery between profiles
- **Change Impact**: Quantify the effect of profile modifications
- **Trend Analysis**: Identify patterns in profile evolution

### Integration Features
- **Seamless Workflow**: From autotune analysis to profile activation
- **Data Consistency**: Maintains proper formatting throughout process
- **Error Recovery**: Robust handling of network and API issues

---

## 💡 **BEST PRACTICES**

### For Profile Management
1. **Regular Reviews**: Check profiles monthly or after significant life changes
2. **Gradual Changes**: Make incremental adjustments rather than large jumps
3. **Documentation**: Keep notes about why profiles were changed
4. **Backup Strategy**: Always maintain copies of working profiles

### For Autotune Analysis
1. **Sufficient Data**: Use 1-2 weeks minimum, preferably 3-4 weeks
2. **Clean Data**: Ensure accurate carb logging and pump disconnection logging
3. **Stable Periods**: Avoid periods with illness, stress, or major routine changes
4. **Regular Runs**: Perform autotune analysis regularly to track trends

### For Clinical Use
1. **Healthcare Collaboration**: Share profile changes with your diabetes team
2. **Monitoring Protocol**: Increase blood glucose monitoring after profile changes
3. **Safety Limits**: Set conservative limits for automatic adjustments
4. **Emergency Planning**: Keep previous working profiles readily available

---

## 📞 **SUPPORT**

### Getting Help
- **Check Documentation**: Review this guide and main README.md
- **Browser Console**: Look for JavaScript errors during profile operations
- **Nightscout Logs**: Check Nightscout server logs for API issues
- **Community Resources**: OpenAPS and Nightscout community forums

### Reporting Issues
When reporting problems, include:
- Browser type and version
- Complete error messages
- Steps to reproduce the issue  
- Nightscout version and configuration
- Screenshots of any error screens

---

*This guide covers the complete profile management workflow in Autotune123. For general application setup and usage, see the main README.md file.*