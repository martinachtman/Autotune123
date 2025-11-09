"""
Autotune Implementation - Modern Python class-based approach
Direct API integration without bash/subprocess dependencies
"""

import os
import json
import pandas as pd
from urllib.parse import urlparse
from datetime import datetime
from typing import Optional, Tuple, Dict, List
import logging

from autotune_engine import AutotuneEngine, AutotuneConfig
from get_profile import get_profile
from definitions import ROOT_DIR, UPLOAD_FOLDER, PROFILE_FILES, recommendations_file_path
from file_management import checkdir
from log import logging as app_logging


class Autotune:
    """Modern Python-only implementation of Autotune"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.autotune_engine: Optional[AutotuneEngine] = None
    
    def url_validator(self, url: str) -> bool:
        """Validate URL format"""
        try:
            result = urlparse(url)
            return all([result.scheme, result.netloc])
        except Exception as e:
            self.logger.error(f"URL validation failed: {e}")
            return False
    
    def clean_up(self):
        """Clean up temporary files"""
        directory = os.path.join(os.path.expanduser('~'), "myopenaps/settings")
        
        for profile_file in PROFILE_FILES:
            file_path = os.path.join(directory, profile_file)
            if os.path.exists(file_path):
                try:
                    os.remove(file_path)
                    self.logger.info(f"Removed {file_path}")
                except OSError as e:
                    self.logger.warning(f"Could not remove {file_path}: {e}")
        
        if os.path.exists(recommendations_file_path):
            try:
                os.remove(recommendations_file_path)
                self.logger.info(f"Removed {recommendations_file_path}")
            except OSError as e:
                self.logger.warning(f"Could not remove {recommendations_file_path}: {e}")
    
    def get(self, nightscout: str, token: Optional[str] = None, 
            insulin_type: str = "rapid-acting") -> Tuple[pd.DataFrame, pd.DataFrame, Dict]:
        """Get profile data from Nightscout"""
        try:
            profile = get_profile(nightscout, insulin_type, token=token)
            self.logger.info("Nightscout profile successfully retrieved")
            
            # Extract data for DataFrame format
            carb_ratio = profile["carb_ratios"]["schedule"][0]["ratio"]
            sensitivity = profile["isfProfile"]["sensitivities"][0]["sensitivity"]
            
            df_basals = pd.DataFrame.from_dict(profile["basalprofile"])
            df_basals = df_basals.drop(["i", "minutes"], axis=1)
            df_basals["start"] = df_basals["start"].str.slice(stop=-3)
            df_basals = df_basals.rename(columns={"start": "Time", "rate": "Rate"})
            
            df_non_basals = pd.DataFrame(data={
                'ISF [mg/dL/U]': [sensitivity], 
                'ISF [mmol/L/U]': [sensitivity/18],  
                'Carbratio (gr/U)': [carb_ratio]
            })
            
            return df_basals, df_non_basals, profile
            
        except Exception as e:
            self.logger.error(f"Failed to get profile: {e}")
            raise

    def get_specific_profile(self, nightscout: str, token: Optional[str] = None, 
                           insulin_type: str = "rapid-acting", profile_name: Optional[str] = None) -> Tuple[pd.DataFrame, pd.DataFrame, Dict]:
        """Get a specific profile by name from Nightscout"""
        if not profile_name:
            # Fall back to current profile
            return self.get(nightscout, token, insulin_type)
        
        try:
            from get_profile import get_profile_by_name, ns_to_oaps
            from correct_current_basals import correct_current_basals
            
            # Format token for API call
            token_param = f"token={token}" if token and not token.startswith("token=") else token
            
            # Get specific profile data
            ns_profile = get_profile_by_name(nightscout, profile_name, token_param)
            
            # Convert to OpenAPS format
            profile_openaps = ns_to_oaps(ns_profile)
            profile = correct_current_basals(profile_openaps)
            profile["curve"] = insulin_type
            
            self.logger.info(f"Successfully loaded profile '{profile_name}'")
            
            # Extract data same way as get() method
            carb_ratio = profile["carb_ratios"]["schedule"][0]["ratio"]
            sensitivity = profile["isfProfile"]["sensitivities"][0]["sensitivity"]
            df_basals = pd.DataFrame.from_dict(profile["basalprofile"])
            df_basals = df_basals.drop(["i", "minutes"], axis=1)
            df_basals["start"] = df_basals["start"].str.slice(stop=-3)
            df_basals = df_basals.rename(columns={"start": "Time", "rate": "Rate"})
            df_non_basals = pd.DataFrame(data={'ISF [mg/dL/U]': [sensitivity], 'ISF [mmol/L/U]': [sensitivity/18],  'Carbratio (gr/U)': [carb_ratio]})
            
            return df_basals, df_non_basals, profile
            
        except Exception as e:
            self.logger.error(f"Error loading specific profile '{profile_name}': {e}")
            # Fall back to current profile
            return self.get(nightscout, token, insulin_type)
    
    def run_modern(self, nightscout: str, start_date: str, end_date: str, 
                   uam: bool = False, token: Optional[str] = None, 
                   aggressive_mode: bool = False) -> Optional[pd.DataFrame]:
        """
        Modern Python-only autotune implementation
        No subprocess calls, no bash dependencies
        """
        try:
            # Validate inputs
            if not self.url_validator(nightscout):
                raise ValueError(f"Invalid Nightscout URL: {nightscout}")
            
            # Initialize autotune engine
            self.autotune_engine = AutotuneEngine(nightscout, token, aggressive_mode=aggressive_mode)
            
            # Create autotune configuration
            config = AutotuneConfig(
                start_date=start_date,
                end_date=end_date,
                categorize_uam_as_basal=uam,
                verbose=True
            )
            
            self.logger.info(f"Starting modern autotune run: {start_date} to {end_date}")
            
            # Run autotune analysis
            result = self.autotune_engine.run_autotune(config)
            
            if result['status'] != 'success':
                self.logger.error(f"Autotune failed: {result.get('error', 'Unknown error')}")
                return None
            
            # Convert recommendations to DataFrame format
            recommendations = result['recommendations']
            df_recommendations = pd.DataFrame(recommendations)
            
            self.logger.info(f"Autotune completed successfully with {len(recommendations)} recommendations")
            
            # Save results for web interface
            self._save_results(result, start_date)
            
            return df_recommendations
            
        except Exception as e:
            self.logger.error(f"Autotune run failed: {e}")
            app_logging.error(f"Autotune run failed: {e}")
            return None
    
    def run(self, nightscout: str, start_date: str, end_date: str, 
            uam: bool = False, directory: str = "myopenaps", 
            token: Optional[str] = None) -> Optional[pd.DataFrame]:
        """
        Main run method - uses Python-only implementation
        """
        try:
            self.logger.info("Running Python-only autotune...")
            result = self.run_modern(nightscout, start_date, end_date, uam, token)
            
            if result is not None:
                self.logger.info("Autotune completed successfully")
                return result
            else:
                self.logger.error("Autotune execution failed")
                return None
                
        except Exception as e:
            self.logger.error(f"Autotune run failed: {e}")
            return None
    
    def _save_results(self, result: Dict, start_date: str):
        """Save autotune results to files for web interface"""
        try:
            # Create results directory
            results_dir = os.path.join(ROOT_DIR, "autotune_results")
            os.makedirs(results_dir, exist_ok=True)
            
            # Save complete result
            result_file = os.path.join(results_dir, f"autotune_result_{start_date}.json")
            with open(result_file, 'w') as f:
                json.dump(result, f, indent=2, default=str)
            
            # Save recommendations in CSV format
            if result['recommendations']:
                df = pd.DataFrame(result['recommendations'])
                csv_file = os.path.join(results_dir, f"recommendations_{start_date}.csv")
                df.to_csv(csv_file, index=False)
                
            self.logger.info(f"Results saved to {results_dir}")
            
        except Exception as e:
            self.logger.warning(f"Could not save results: {e}")
    
    def create_adjusted_profile(self, autotune_recomm: List[Dict], current_profile: Dict) -> Dict:
        """Create adjusted profile based on autotune recommendations"""
        try:
            d = current_profile.copy()
            
            # Extract sensitivity and carb ratio from recommendations
            for recommendation in autotune_recomm:
                param = str(recommendation["Parameter"])
                
                if "ISF[mg/dL/U]" in param:
                    sensitivity = recommendation["Autotune"]
                    d["isfProfile"]["sensitivities"][0]["sensitivity"] = round(float(sensitivity) / 18, 1)
                
                elif "CarbRatio" in param:
                    carb_ratio = recommendation["Autotune"]
                    d["carb_ratios"]["schedule"][0]["ratio"] = round(float(carb_ratio), 1)
                    d["carb_ratio"] = round(float(carb_ratio), 1)
            
            # Process basal recommendations
            basal_updates = []
            ftr = [3600, 60, 1]  # time conversion factors
            
            for recommendation in autotune_recomm:
                param = recommendation["Parameter"]
                
                # Skip non-time parameters
                if any(c.isalpha() for c in param) or ":" not in param:
                    continue
                
                # Convert time string to seconds
                try:
                    sec = sum([a * b for a, b in zip(ftr, map(int, param.split(':')))])
                    hour = sec // 3600
                    
                    if 0 <= hour < 24:
                        basal_entry = {
                            'i': hour,
                            'minutes': 60.0 * hour,
                            'start': f'{hour:02d}:00:00',
                            'rate': f"{float(recommendation['Autotune']):.2f}"
                        }
                        basal_updates.append(basal_entry)
                        
                except (ValueError, IndexError) as e:
                    self.logger.warning(f"Could not parse time parameter {param}: {e}")
            
            if basal_updates:
                d["basalprofile"] = sorted(basal_updates, key=lambda x: x['i'])
            
            return d
            
        except Exception as e:
            self.logger.error(f"Failed to create adjusted profile: {e}")
            return current_profile
    
    def upload(self, nightscout: str, profile: Dict, token: str) -> bool:
        """Upload profile to Nightscout (placeholder - needs API implementation)"""
        try:
            # This would need to be implemented with direct API calls
            # rather than external tool dependencies
            self.logger.warning("Profile upload not yet implemented")
            return False
            
        except Exception as e:
            self.logger.error(f"Profile upload failed: {e}")
            return False


# Example usage and testing
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    autotune = Autotune()
    
    # Test with your Nightscout instance
    result = autotune.run_modern(
        nightscout="https://your-nightscout-site.herokuapp.com",
        start_date="2025-11-04",
        end_date="2025-11-05",
        uam=False,
        token="your-api-secret-here"  # Replace with actual token
    )
    
    if result is not None:
        print("Modern autotune successful!")
        print(result.head())
    else:
        print("Modern autotune failed")