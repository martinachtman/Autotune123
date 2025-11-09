"""
AutotuneEngine - Pure Python implementation of autotune logic
Replaces the bash/JavaScript oref0 tool chain with proper Python classes
"""

import requests
import json
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import logging
from dataclasses import dataclass
from urllib.parse import urljoin, urlparse


@dataclass
class AutotuneConfig:
    """Configuration for autotune run"""
    start_date: str
    end_date: str
    categorize_uam_as_basal: bool = False
    tune_insulin_curve: bool = False
    timezone: str = "UTC"
    dia: float = 4.0
    verbose: bool = True


@dataclass
class BGReading:
    """Blood glucose reading from Nightscout"""
    timestamp: datetime
    sgv: int
    direction: str
    device: str


@dataclass
class Treatment:
    """Treatment entry from Nightscout"""
    timestamp: datetime
    event_type: str
    insulin: Optional[float] = None
    carbs: Optional[float] = None
    rate: Optional[float] = None  # for temp basals
    duration: Optional[int] = None  # for temp basals
    absolute: Optional[float] = None  # for temp basals


class NightscoutClient:
    """Handle all Nightscout API communications"""
    
    def __init__(self, base_url: str, api_secret: Optional[str] = None):
        self.base_url = base_url.rstrip('/')
        self.api_secret = api_secret
        self.session = requests.Session()
        
        # Store token for query parameter authentication (Nightscout standard)
        self.token_param = None
        if api_secret:
            # Clean token format - remove 'token=' prefix if present, then add it back
            clean_token = api_secret
            if api_secret.startswith('token='):
                clean_token = api_secret[6:]  # Remove 'token=' prefix
            self.token_param = f'token={clean_token}'
    
    def _make_request(self, endpoint: str, params: Optional[Dict] = None) -> Dict:
        """Make authenticated request to Nightscout API"""
        url = urljoin(self.base_url + '/', endpoint)
        
        # Add token as query parameter if available (Nightscout standard method)
        if self.token_param:
            if '?' in url:
                url += '&' + self.token_param
            else:
                url += '?' + self.token_param
        
        try:
            response = self.session.get(url, params=params)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            logging.error(f"Nightscout API request failed: {e}")
            raise
    
    def get_entries(self, start_date: str, end_date: str, count: int = 1500) -> List[BGReading]:
        """Get BG entries from Nightscout"""
        # Convert dates to timestamps
        start_dt = datetime.strptime(start_date, "%Y-%m-%d")
        end_dt = datetime.strptime(end_date, "%Y-%m-%d") + timedelta(days=1)
        
        start_ts = int(start_dt.timestamp() * 1000)
        end_ts = int(end_dt.timestamp() * 1000)
        
        params = {
            'find[date][$gte]': start_ts,
            'find[date][$lte]': end_ts,
            'count': count
        }
        
        entries_data = self._make_request('api/v1/entries/sgv.json', params)
        
        entries = []
        for entry in entries_data:
            if entry.get('type') == 'sgv' and entry.get('sgv'):
                # Create timezone-aware datetime to match treatments
                bg_timestamp = datetime.fromtimestamp(entry['date'] / 1000)
                bg_timestamp = bg_timestamp.replace(tzinfo=None)  # Make offset-naive for consistency
                
                bg_reading = BGReading(
                    timestamp=bg_timestamp,
                    sgv=entry['sgv'],
                    direction=entry.get('direction', 'Unknown'),
                    device=entry.get('device', 'Unknown')
                )
                entries.append(bg_reading)
        
        return sorted(entries, key=lambda x: x.timestamp)
    
    def get_treatments(self, start_date: str, end_date: str) -> List[Treatment]:
        """Get treatment entries from Nightscout"""
        # Convert to ISO format for treatments API
        start_dt = datetime.strptime(start_date, "%Y-%m-%d")
        end_dt = datetime.strptime(end_date, "%Y-%m-%d") + timedelta(days=1)
        
        params = {
            'find[created_at][$gte]': start_dt.isoformat() + 'Z',
            'find[created_at][$lte]': end_dt.isoformat() + 'Z'
        }
        
        treatments_data = self._make_request('api/v1/treatments.json', params)
        
        treatments = []
        for treatment in treatments_data:
            if not treatment.get('isValid', True):
                continue
                
            # Parse timestamp and make offset-naive for consistency
            timestamp_str = treatment['created_at'].replace('Z', '+00:00')
            treatment_timestamp = datetime.fromisoformat(timestamp_str)
            treatment_timestamp = treatment_timestamp.replace(tzinfo=None)  # Make offset-naive
            
            treatment_obj = Treatment(
                timestamp=treatment_timestamp,
                event_type=treatment.get('eventType', ''),
                insulin=treatment.get('insulin'),
                carbs=treatment.get('carbs'),
                rate=treatment.get('rate'),
                duration=treatment.get('duration'),
                absolute=treatment.get('absolute')
            )
            treatments.append(treatment_obj)
        
        return sorted(treatments, key=lambda x: x.timestamp)
    
    def get_profile(self) -> Dict:
        """Get current profile from Nightscout"""
        profile_data = self._make_request('api/v1/profile.json')
        
        if not profile_data:
            raise ValueError("No profile data found in Nightscout")
        
        # Get the default profile
        store = profile_data[0]['store']
        default_profile_name = profile_data[0]['defaultProfile']
        profile = store[default_profile_name]
        
        return profile


class AutotuneDataProcessor:
    """Process Nightscout data for autotune analysis"""
    
    def __init__(self, bg_readings: List[BGReading], treatments: List[Treatment], profile: Dict):
        self.bg_readings = bg_readings
        self.treatments = treatments
        self.profile = profile
        
    def calculate_deviations(self) -> pd.DataFrame:
        """Calculate BG deviations from expected based on treatments"""
        # This is a simplified version - the full oref0 logic is quite complex
        deviations = []
        
        for i, bg in enumerate(self.bg_readings[1:], 1):
            prev_bg = self.bg_readings[i-1]
            time_diff = (bg.timestamp - prev_bg.timestamp).total_seconds() / 60  # minutes
            
            if time_diff > 0 and time_diff <= 15:  # Valid BG pair
                actual_change = bg.sgv - prev_bg.sgv
                
                # Find relevant treatments in this time window
                relevant_treatments = [
                    t for t in self.treatments 
                    if prev_bg.timestamp <= t.timestamp <= bg.timestamp
                ]
                
                # Calculate expected change based on treatments
                expected_change = self._calculate_expected_bg_change(
                    prev_bg, bg, relevant_treatments
                )
                
                deviation = actual_change - expected_change
                
                deviations.append({
                    'timestamp': bg.timestamp,
                    'bg': bg.sgv,
                    'deviation': deviation,
                    'treatments': len(relevant_treatments),
                    'basal_only': len(relevant_treatments) == 0,  # No treatments = basal period
                    'time_diff_min': time_diff
                })
        
        return pd.DataFrame(deviations)
    
    def _calculate_expected_bg_change(self, prev_bg: BGReading, current_bg: BGReading, 
                                    treatments: List[Treatment]) -> float:
        """Calculate expected BG change based on treatments"""
        # Simplified calculation - real oref0 has complex ISF/IOB calculations
        expected_change = 0.0
        
        for treatment in treatments:
            if treatment.insulin:
                # Use ISF from profile to calculate expected drop
                isf = self.profile.get('sens', [{'value': 50}])[0]['value']
                expected_change -= treatment.insulin * isf
            
            if treatment.carbs:
                # Use carb ratio to calculate expected rise
                carb_ratio = self.profile.get('carbratio', [{'value': 10}])[0]['value']
                expected_change += treatment.carbs / carb_ratio * 50  # Simplified
        
        return expected_change


class AutotuneEngine:
    """Main autotune engine that orchestrates the entire process"""
    
    def __init__(self, nightscout_url: str, api_secret: Optional[str] = None, aggressive_mode: bool = False):
        self.nightscout_client = NightscoutClient(nightscout_url, api_secret)
        self.logger = logging.getLogger(__name__)
        self.aggressive_mode = aggressive_mode
    
    def run_autotune(self, config: AutotuneConfig) -> Dict:
        """Run complete autotune analysis"""
        try:
            # Step 1: Fetch data from Nightscout
            self.logger.info("Fetching BG readings from Nightscout...")
            bg_readings = self.nightscout_client.get_entries(
                config.start_date, config.end_date
            )
            
            self.logger.info("Fetching treatments from Nightscout...")
            treatments = self.nightscout_client.get_treatments(
                config.start_date, config.end_date
            )
            
            self.logger.info("Fetching profile from Nightscout...")
            profile = self.nightscout_client.get_profile()
            
            # Step 2: Validate data
            if len(bg_readings) < 10:
                raise ValueError("Insufficient BG readings for autotune analysis")
            
            self.logger.info(f"Data summary: {len(bg_readings)} BG readings, {len(treatments)} treatments")
            
            # Step 3: Process data
            processor = AutotuneDataProcessor(bg_readings, treatments, profile)
            deviations_df = processor.calculate_deviations()
            
            # Step 4: Calculate recommendations
            recommendations = self._calculate_recommendations(deviations_df, profile)
            
            # Step 5: Format results
            result = {
                'status': 'success',
                'config': config.__dict__,
                'data_summary': {
                    'bg_readings': len(bg_readings),
                    'treatments': len(treatments),
                    'deviations': len(deviations_df)
                },
                'recommendations': recommendations,
                'profile': profile
            }
            
            return result
            
        except Exception as e:
            self.logger.error(f"Autotune run failed: {e}")
            return {
                'status': 'error',
                'error': str(e),
                'config': config.__dict__
            }
    
    def _calculate_recommendations(self, deviations_df: pd.DataFrame, profile: Dict) -> List[Dict]:
        """Calculate autotune recommendations based on deviations"""
        recommendations = []
        
        # ISF recommendation (simplified)
        if not deviations_df.empty:
            avg_deviation = deviations_df['deviation'].mean()
            current_isf = profile.get('sens', [{'value': 50}])[0]['value']
            
            # If consistently running high (positive deviations), ISF might be too high
            if avg_deviation > 5:
                recommended_isf = current_isf * 0.9  # Decrease ISF by 10%
            elif avg_deviation < -5:
                recommended_isf = current_isf * 1.1  # Increase ISF by 10%
            else:
                recommended_isf = current_isf
            
            recommendations.append({
                'Parameter': 'ISF[mg/dL/U]',
                'Pump': current_isf,
                'Autotune': round(recommended_isf, 1),
                'Days Missing': 0
            })
        
        # Carb ratio recommendation (simplified)
        current_cr = profile.get('carbratio', [{'value': 10}])[0]['value']
        recommendations.append({
            'Parameter': 'CarbRatio(g/U)',
            'Pump': current_cr,
            'Autotune': current_cr,  # Simplified - no change for now
            'Days Missing': 0
        })
        
        # Basal recommendations based on deviations analysis
        self.logger.info(f"Analyzing basal rates with {len(deviations_df)} total deviations")
        if not deviations_df.empty:
            basal_only_count = len(deviations_df[deviations_df['basal_only'] == True])
            self.logger.info(f"Found {basal_only_count} basal-only periods for analysis")
        
        basal_schedule = profile.get('basal', [])
        self.logger.info(f"Processing {len(basal_schedule)} basal time periods")
        
        for basal_entry in basal_schedule:
            time_str = basal_entry.get('time', '00:00')
            current_rate = basal_entry.get('value', 0.5)
            
            # Analyze deviations during this basal period
            recommended_rate = self._calculate_basal_recommendation(
                deviations_df, time_str, current_rate
            )
            
            recommendations.append({
                'Parameter': time_str,
                'Pump': current_rate,
                'Autotune': recommended_rate,
                'Days Missing': 0
            })
        
        return recommendations
    
    def _calculate_basal_recommendation(self, deviations_df: pd.DataFrame, 
                                      time_str: str, current_rate: float) -> float:
        """Calculate basal rate recommendation for a specific time period"""
        self.logger.debug(f"Calculating basal recommendation for {time_str}, current rate: {current_rate}")
        
        if deviations_df.empty:
            self.logger.debug(f"  -> No deviations data for {time_str}, keeping current rate")
            return current_rate
        
        # Parse time string to get hour
        try:
            hour = int(time_str.split(':')[0])
        except (ValueError, IndexError):
            hour = 0
        
        # Filter deviations for this basal time period (approximate)
        # Focus on basal-only periods (no treatments) for better accuracy
        relevant_deviations = deviations_df[
            (deviations_df['timestamp'].dt.hour >= hour) & 
            (deviations_df['timestamp'].dt.hour < (hour + 1) % 24) &
            (deviations_df['basal_only'] == True)  # Only periods without treatments
        ]
        
        self.logger.debug(f"  -> Found {len(relevant_deviations)} basal-only deviations for hour {hour}")
        
        # Set thresholds based on mode
        if self.aggressive_mode:
            min_data_points = 2  # Aggressive mode: need fewer data points
            deviation_threshold = 10  # Aggressive mode: more sensitive to smaller deviations
            mode_description = "aggressive"
        else:
            min_data_points = 3  # Standard mode: original oref0-autotune logic
            deviation_threshold = 20  # Standard mode: conservative threshold
            mode_description = "standard"
            
        if len(relevant_deviations) < min_data_points:
            self.logger.debug(f"  -> Not enough data points ({len(relevant_deviations)} < {min_data_points}) for {time_str} in {mode_description} mode, keeping current rate")
            return current_rate
        
        # Analyze deviations during this time period
        avg_deviation = relevant_deviations['deviation'].mean()
        self.logger.debug(f"  -> Average deviation for {time_str}: {avg_deviation:.2f} (using {mode_description} mode, threshold: ±{deviation_threshold} mg/dL)")
        
        # If consistently positive deviations (BG rising more than expected),
        # increase basal rate. If negative, decrease basal rate.
        adjustment_factor = 1.0
        
        if avg_deviation > deviation_threshold:  # BG rising more than expected
            adjustment_factor = 1.1  # Increase basal by 10%
            self.logger.debug(f"  -> BG rising too much ({avg_deviation:.1f} > {deviation_threshold}), increasing basal by 10%")
        elif avg_deviation < -deviation_threshold:  # BG dropping more than expected
            adjustment_factor = 0.9  # Decrease basal by 10%
            self.logger.debug(f"  -> BG dropping too much ({avg_deviation:.1f} < -{deviation_threshold}), decreasing basal by 10%")
        else:
            self.logger.debug(f"  -> Deviation within range (±{deviation_threshold} mg/dL), no change needed")
        
        # Apply safety limits
        recommended_rate = current_rate * adjustment_factor
        recommended_rate = max(0.1, min(5.0, recommended_rate))  # Safety bounds
        
        # Round to reasonable precision
        final_rate = round(recommended_rate, 2)
        self.logger.debug(f"  -> {time_str}: {current_rate} -> {final_rate} (factor: {adjustment_factor})")
        
        return final_rate


# Example usage:
if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(level=logging.INFO)
    
    # Create autotune engine
    engine = AutotuneEngine(
        nightscout_url="https://your-nightscout-site.herokuapp.com",
        api_secret="your-api-secret-here"
    )
    
    # Configure autotune run
    config = AutotuneConfig(
        start_date="2025-11-04",
        end_date="2025-11-05",
        categorize_uam_as_basal=False
    )
    
    # Run autotune
    result = engine.run_autotune(config)
    
    if result['status'] == 'success':
        print("Autotune completed successfully!")
        print(f"Recommendations: {len(result['recommendations'])}")
        for rec in result['recommendations']:
            print(f"  {rec['Parameter']}: {rec['Current']} -> {rec['Autotune']}")
    else:
        print(f"Autotune failed: {result['error']}")