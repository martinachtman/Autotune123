# Test Data Files

This directory contains various data formats used in the Autotune123 pipeline.

## Files:

### Autotune Recommendations (Pipe-delimited format)
- **sample_autotune.log** - Standard test data with sparse basal entries (only when rates change)
- **alternative_autotune.log** - Alternative test data with different timing pattern
- These are the output files from running autotune analysis

### Nightscout Profile Data (JSON format)
- **nightscout_profile.json** - Single profile in Nightscout format
- **nightscout_profiles_api.json** - Full API response with profile store
- **openaps_profile.json** - Converted OpenAPS format profile
- These represent input data from Nightscout API

## Data Flow

1. **Nightscout JSON** → Profile download from Nightscout API
2. **OpenAPS JSON** → Converted profile format 
3. **Autotune Process** → Generates recommendations
4. **Autotune Log** → Pipe-delimited recommendations file
5. **Web Interface** → Displays recommendations and allows filtering

## Usage:

### For Autotune Recommendations Testing:
```bash
# Copy autotune recommendations to container
docker cp tests/testdata/sample_autotune.log autotune123-autotune123-1:/app/Autotune123/autotune.log
```

### For Profile Testing:
```bash
# Test with Nightscout profile format
python3 -c "import json; print(json.load(open('tests/testdata/nightscout_profile.json')))"
```

### For Unit Tests:
Reference these files in unit tests for data processing validation of each pipeline stage.