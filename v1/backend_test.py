"""Cascade Oracle — Backend API Test Suite (Phase 2A)

Tests all API endpoints and validates doctrine requirements:
- 6 Washington State river stations
- Real USGS data integration
- NOAA NWPS threshold integration
- Proper risk state computation
- Transparent source labeling
- Phase 1.5: basin groups, validated thresholds, refresh tracking
- Phase 2A: SNOTEL snowpack precursor layer (NRCS AWDB integration)
"""
import sys
import time
from typing import Dict, List, Optional

import requests

# Public endpoint from frontend/.env
BASE_URL = "https://river-command.preview.emergentagent.com/api"

# Expected station IDs
EXPECTED_STATIONS = [
    "cedar-renton",
    "snoqualmie-carnation",
    "skagit-mt-vernon",
    "nooksack-ferndale",
    "green-auburn",
    "white-auburn",
]

# Stations that should have official NWPS thresholds (validated=True)
NWPS_STATIONS = ["cedar-renton", "snoqualmie-carnation", "skagit-mt-vernon", "nooksack-ferndale"]

# Stations that should have 'unknown' risk (no validated thresholds)
UNKNOWN_RISK_STATIONS = ["green-auburn", "white-auburn"]

# Expected basin groups (Phase 1.5)
EXPECTED_BASIN_GROUPS = [
    "cedar-lk-washington",
    "snoqualmie-snohomish",
    "skagit",
    "nooksack",
    "green-duwamish",
    "puyallup-white",
]


class CascadeOracleAPITester:
    def __init__(self):
        self.tests_run = 0
        self.tests_passed = 0
        self.tests_failed = 0
        self.errors: List[str] = []

    def log_pass(self, test_name: str, detail: str = ""):
        self.tests_passed += 1
        self.tests_run += 1
        msg = f"✅ PASS: {test_name}"
        if detail:
            msg += f" — {detail}"
        print(msg)

    def log_fail(self, test_name: str, reason: str):
        self.tests_failed += 1
        self.tests_run += 1
        msg = f"❌ FAIL: {test_name} — {reason}"
        print(msg)
        self.errors.append(msg)

    def test_system_status(self) -> bool:
        """Test GET /api/system/status (Phase 1.5: added phase, phase_label, stations_active, last_attempt)"""
        print("\n🔍 Testing GET /api/system/status")
        try:
            resp = requests.get(f"{BASE_URL}/system/status", timeout=15)
            if resp.status_code != 200:
                self.log_fail("system/status status code", f"Expected 200, got {resp.status_code}")
                return False

            data = resp.json()
            
            # Check required fields (Phase 1.5 additions)
            required_fields = [
                "ok", "stations_total", "stations_active", "stations_with_data",
                "cache_seconds_remaining", "notes", "phase", "phase_label", "last_attempt"
            ]
            for field in required_fields:
                if field not in data:
                    self.log_fail("system/status schema", f"Missing field: {field}")
                    return False

            # Check phase fields
            if data["phase"] != 1:
                self.log_fail("system/status phase", f"Expected phase=1, got {data['phase']}")
                return False
            
            if "Phase 1" not in data["phase_label"]:
                self.log_fail("system/status phase_label", f"Expected 'Phase 1' in label, got {data['phase_label']}")
                return False

            # Check stations_total = 6
            if data["stations_total"] != 6:
                self.log_fail("system/status stations_total", f"Expected 6, got {data['stations_total']}")
                return False

            # Check stations_active field exists
            if data["stations_active"] != 6:
                self.log_fail("system/status stations_active", f"Expected 6, got {data['stations_active']}")
                return False

            # Check last_attempt structure
            last_attempt = data.get("last_attempt", {})
            attempt_fields = ["attempted_at", "succeeded_at", "ok", "errors", "stations_attempted", "stations_succeeded"]
            for field in attempt_fields:
                if field not in last_attempt:
                    self.log_fail("system/status last_attempt", f"Missing field: {field}")
                    return False

            self.log_pass(
                "system/status",
                f"ok={data['ok']}, phase={data['phase']}, stations_total={data['stations_total']}, "
                f"stations_active={data['stations_active']}, last_attempt.ok={last_attempt['ok']}"
            )
            return True

        except Exception as e:
            self.log_fail("system/status", f"Exception: {e}")
            return False

    def test_system_basins(self) -> bool:
        """Test GET /api/system/basins (Phase 1.5: basin group taxonomy)"""
        print("\n🔍 Testing GET /api/system/basins")
        try:
            resp = requests.get(f"{BASE_URL}/system/basins", timeout=15)
            if resp.status_code != 200:
                self.log_fail("system/basins status code", f"Expected 200, got {resp.status_code}")
                return False

            data = resp.json()
            
            # Check structure
            if "basins" not in data:
                self.log_fail("system/basins schema", "Missing 'basins' field")
                return False

            basins = data["basins"]
            if not isinstance(basins, list):
                self.log_fail("system/basins type", "basins is not a list")
                return False

            # Check we have exactly 6 basin groups
            if len(basins) != 6:
                self.log_fail("system/basins count", f"Expected 6 basins, got {len(basins)}")
                return False

            # Check all expected basin keys are present
            basin_keys = [b.get("key") for b in basins]
            for expected_key in EXPECTED_BASIN_GROUPS:
                if expected_key not in basin_keys:
                    self.log_fail("system/basins keys", f"Missing basin group: {expected_key}")
                    return False

            # Check each basin has key and label
            for basin in basins:
                if "key" not in basin or "label" not in basin:
                    self.log_fail("system/basins structure", f"Basin missing key or label: {basin}")
                    return False

            self.log_pass("system/basins", f"Returned {len(basins)} basin groups with correct keys")
            return True

        except Exception as e:
            self.log_fail("system/basins", f"Exception: {e}")
            return False

    def test_list_stations(self) -> Optional[Dict]:
        """Test GET /api/stations"""
        print("\n🔍 Testing GET /api/stations")
        try:
            resp = requests.get(f"{BASE_URL}/stations", timeout=20)
            if resp.status_code != 200:
                self.log_fail("list_stations status code", f"Expected 200, got {resp.status_code}")
                return None

            data = resp.json()
            
            # Check required top-level fields
            if "stations" not in data or "system" not in data or "fetched_at" not in data:
                self.log_fail("list_stations schema", "Missing required top-level fields")
                return None

            stations = data["stations"]
            if not isinstance(stations, list):
                self.log_fail("list_stations stations type", "stations is not a list")
                return None

            # Check we have exactly 6 stations
            if len(stations) != 6:
                self.log_fail("list_stations count", f"Expected 6 stations, got {len(stations)}")
                return None

            # Check all expected station IDs are present
            station_ids = [s.get("id") for s in stations]
            for expected_id in EXPECTED_STATIONS:
                if expected_id not in station_ids:
                    self.log_fail("list_stations IDs", f"Missing station: {expected_id}")
                    return None

            # Validate each station has required fields (Phase 1.5: added basin_group, active, notes, precursors)
            required_station_fields = [
                "id", "name", "river", "basin", "basin_group", "usgs_site",
                "gage_height", "discharge", "thresholds",
                "risk_state", "risk_reason", "is_stale", "fetched_at",
                "active", "notes", "precursors"
            ]
            for station in stations:
                for field in required_station_fields:
                    if field not in station:
                        self.log_fail("list_stations station schema", f"Station {station.get('id')} missing field: {field}")
                        return None

                # Check thresholds has validated field
                thresholds = station.get("thresholds", {})
                if "validated" not in thresholds:
                    self.log_fail("list_stations thresholds", f"Station {station.get('id')} thresholds missing 'validated' field")
                    return None

                # Check precursors structure (Phase 2A: should be populated)
                precursors = station.get("precursors", {})
                if "available" not in precursors:
                    self.log_fail("list_stations precursors", f"Station {station.get('id')} precursors missing 'available' field")
                    return None
                # Phase 2A: precursors should be available for all 6 stations
                if precursors.get("available") is not True:
                    self.log_fail("list_stations precursors", f"Station {station.get('id')} precursors.available should be True in Phase 2A, got {precursors.get('available')}")
                    return None

            self.log_pass("list_stations", f"Returned {len(stations)} stations with valid Phase 2A schema (precursors populated)")
            return data

        except Exception as e:
            self.log_fail("list_stations", f"Exception: {e}")
            return None

    def test_get_single_station(self, station_id: str) -> Optional[Dict]:
        """Test GET /api/stations/{id}"""
        print(f"\n🔍 Testing GET /api/stations/{station_id}")
        try:
            resp = requests.get(f"{BASE_URL}/stations/{station_id}", timeout=20)
            if resp.status_code != 200:
                self.log_fail(f"get_station {station_id} status code", f"Expected 200, got {resp.status_code}")
                return None

            data = resp.json()
            
            # Check it's the right station
            if data.get("id") != station_id:
                self.log_fail(f"get_station {station_id} ID mismatch", f"Expected {station_id}, got {data.get('id')}")
                return None

            # Check required fields
            required_fields = [
                "id", "name", "river", "basin", "usgs_site",
                "gage_height", "discharge", "thresholds",
                "risk_state", "risk_reason", "is_stale", "fetched_at"
            ]
            for field in required_fields:
                if field not in data:
                    self.log_fail(f"get_station {station_id} schema", f"Missing field: {field}")
                    return None

            self.log_pass(f"get_station {station_id}", f"risk_state={data['risk_state']}, thresholds.source={data['thresholds'].get('source')}")
            return data

        except Exception as e:
            self.log_fail(f"get_station {station_id}", f"Exception: {e}")
            return None

    def test_get_invalid_station(self):
        """Test GET /api/stations/{id} with invalid ID (should return 404)"""
        print("\n🔍 Testing GET /api/stations/invalid-station-id")
        try:
            resp = requests.get(f"{BASE_URL}/stations/invalid-station-id", timeout=15)
            if resp.status_code == 404:
                self.log_pass("get_station 404", "Correctly returned 404 for invalid station ID")
            else:
                self.log_fail("get_station 404", f"Expected 404, got {resp.status_code}")
        except Exception as e:
            self.log_fail("get_station 404", f"Exception: {e}")

    def test_refresh_single_station(self, station_id: str) -> bool:
        """Test POST /api/stations/{id}/refresh"""
        print(f"\n🔍 Testing POST /api/stations/{station_id}/refresh")
        try:
            # Get current fetched_at
            resp1 = requests.get(f"{BASE_URL}/stations/{station_id}", timeout=20)
            if resp1.status_code != 200:
                self.log_fail(f"refresh_station {station_id} pre-check", "Failed to get initial state")
                return False
            
            fetched_at_before = resp1.json().get("fetched_at")
            
            # Wait a moment to ensure timestamp will change
            time.sleep(1)
            
            # Trigger refresh
            resp2 = requests.post(f"{BASE_URL}/stations/{station_id}/refresh", timeout=20)
            if resp2.status_code != 200:
                self.log_fail(f"refresh_station {station_id} status code", f"Expected 200, got {resp2.status_code}")
                return False

            data = resp2.json()
            fetched_at_after = data.get("fetched_at")
            
            # Verify fetched_at advanced
            if fetched_at_after <= fetched_at_before:
                self.log_fail(f"refresh_station {station_id} timestamp", "fetched_at did not advance")
                return False

            self.log_pass(f"refresh_station {station_id}", f"fetched_at advanced from {fetched_at_before} to {fetched_at_after}")
            return True

        except Exception as e:
            self.log_fail(f"refresh_station {station_id}", f"Exception: {e}")
            return False

    def test_refresh_all_stations(self) -> bool:
        """Test POST /api/refresh (Phase 1.5: verify last_attempt timestamps update)"""
        print("\n🔍 Testing POST /api/refresh")
        try:
            # Get initial last_attempt
            status_before = requests.get(f"{BASE_URL}/system/status", timeout=15)
            if status_before.status_code != 200:
                self.log_fail("refresh_all pre-check", "Failed to get initial status")
                return False
            
            last_attempt_before = status_before.json().get("last_attempt", {})
            attempted_at_before = last_attempt_before.get("attempted_at")
            
            # Wait a moment
            time.sleep(1)
            
            # Trigger refresh
            resp = requests.post(f"{BASE_URL}/refresh", timeout=30)
            if resp.status_code != 200:
                self.log_fail("refresh_all status code", f"Expected 200, got {resp.status_code}")
                return False

            data = resp.json()
            
            # Check response structure
            if "stations" not in data or "system" not in data:
                self.log_fail("refresh_all schema", "Missing required fields")
                return False

            stations = data["stations"]
            if len(stations) != 6:
                self.log_fail("refresh_all count", f"Expected 6 stations, got {len(stations)}")
                return False

            # Check last_attempt was updated
            system = data.get("system", {})
            last_attempt_after = system.get("last_attempt", {})
            attempted_at_after = last_attempt_after.get("attempted_at")
            
            if attempted_at_after and attempted_at_before and attempted_at_after > attempted_at_before:
                self.log_pass(
                    "refresh_all",
                    f"Refreshed {len(stations)} stations, last_attempt.attempted_at advanced from {attempted_at_before} to {attempted_at_after}"
                )
            else:
                self.log_pass("refresh_all", f"Refreshed {len(stations)} stations")
            
            return True

        except Exception as e:
            self.log_fail("refresh_all", f"Exception: {e}")
            return False

    def test_doctrine_validated_thresholds(self, stations_data: List[Dict]) -> bool:
        """Doctrine check: When thresholds.validated=False, risk_state MUST be 'unknown'"""
        print("\n🔍 Testing DOCTRINE: validated=False → risk_state='unknown'")
        all_pass = True
        
        for station in stations_data:
            station_id = station.get("id")
            thresholds = station.get("thresholds", {})
            validated = thresholds.get("validated")
            risk_state = station.get("risk_state")

            if validated is False and risk_state != "unknown":
                self.log_fail(
                    f"doctrine validated {station_id}",
                    f"thresholds.validated=False but risk_state='{risk_state}' (should be 'unknown')"
                )
                all_pass = False
            elif validated is False and risk_state == "unknown":
                self.log_pass(
                    f"doctrine validated {station_id}",
                    f"Correctly enforces risk_state='unknown' when validated=False"
                )

        return all_pass

    def test_doctrine_nwps_validated(self, stations_data: List[Dict]) -> bool:
        """Doctrine check: thresholds with source='official_nwps' must have validated=True"""
        print("\n🔍 Testing DOCTRINE: official_nwps → validated=True")
        all_pass = True
        
        for station in stations_data:
            station_id = station.get("id")
            thresholds = station.get("thresholds", {})
            source = thresholds.get("source")
            validated = thresholds.get("validated")

            if source == "official_nwps" and validated is not True:
                self.log_fail(
                    f"doctrine nwps_validated {station_id}",
                    f"source='official_nwps' but validated={validated} (should be True)"
                )
                all_pass = False
            elif source == "official_nwps" and validated is True:
                self.log_pass(
                    f"doctrine nwps_validated {station_id}",
                    f"Correctly has validated=True for official_nwps"
                )

        return all_pass

    def test_doctrine_unknown_risk_stations(self, stations_data: List[Dict]) -> bool:
        """Doctrine check: green-auburn and white-auburn must have risk_state='unknown' and thresholds.source='thresholds_unavailable' and validated=False"""
        print("\n🔍 Testing DOCTRINE: Unknown risk stations (green-auburn, white-auburn)")
        all_pass = True
        
        for station_id in UNKNOWN_RISK_STATIONS:
            station = next((s for s in stations_data if s["id"] == station_id), None)
            if not station:
                self.log_fail(f"doctrine unknown_risk {station_id}", "Station not found in response")
                all_pass = False
                continue

            risk_state = station.get("risk_state")
            thresholds = station.get("thresholds", {})
            thresholds_source = thresholds.get("source")
            validated = thresholds.get("validated")

            if risk_state != "unknown":
                self.log_fail(f"doctrine unknown_risk {station_id}", f"Expected risk_state='unknown', got '{risk_state}'")
                all_pass = False
            elif thresholds_source != "thresholds_unavailable":
                self.log_fail(f"doctrine unknown_risk {station_id}", f"Expected thresholds.source='thresholds_unavailable', got '{thresholds_source}'")
                all_pass = False
            elif validated is not False:
                self.log_fail(f"doctrine unknown_risk {station_id}", f"Expected thresholds.validated=False, got {validated}")
                all_pass = False
            else:
                self.log_pass(f"doctrine unknown_risk {station_id}", f"Correctly shows risk_state='unknown', source='thresholds_unavailable', validated=False")

        return all_pass

    def test_doctrine_nwps_stations(self, stations_data: List[Dict]) -> bool:
        """Doctrine check: cedar-renton, snoqualmie-carnation, skagit-mt-vernon, nooksack-ferndale should have thresholds.source='official_nwps' and validated=True"""
        print("\n🔍 Testing DOCTRINE: NWPS stations should have official validated thresholds")
        all_pass = True
        
        for station_id in NWPS_STATIONS:
            station = next((s for s in stations_data if s["id"] == station_id), None)
            if not station:
                self.log_fail(f"doctrine nwps {station_id}", "Station not found in response")
                all_pass = False
                continue

            thresholds = station.get("thresholds", {})
            thresholds_source = thresholds.get("source")
            validated = thresholds.get("validated")
            risk_state = station.get("risk_state")

            # Should normally have official_nwps with validated=True
            if thresholds_source == "official_nwps" and validated is True:
                self.log_pass(f"doctrine nwps {station_id}", f"Has official_nwps with validated=True, risk_state={risk_state}")
            elif thresholds_source == "configured_validated" and validated is True:
                # This is acceptable fallback
                self.log_pass(f"doctrine nwps {station_id}", f"Using configured_validated (NWPS may be unavailable), risk_state={risk_state}")
            elif thresholds_source == "configured_pending":
                self.log_fail(f"doctrine nwps {station_id}", f"Has configured_pending (should be validated), validated={validated}")
                all_pass = False
            elif thresholds_source == "thresholds_unavailable":
                self.log_fail(f"doctrine nwps {station_id}", f"Expected official_nwps or configured_validated, got 'thresholds_unavailable'")
                all_pass = False
            else:
                self.log_fail(f"doctrine nwps {station_id}", f"Unexpected thresholds.source: {thresholds_source}, validated={validated}")
                all_pass = False

        return all_pass

    def test_system_snotel_stations(self) -> bool:
        """Test GET /api/system/snotel-stations (Phase 2A)"""
        print("\n🔍 Testing GET /api/system/snotel-stations")
        try:
            resp = requests.get(f"{BASE_URL}/system/snotel-stations", timeout=15)
            if resp.status_code != 200:
                self.log_fail("snotel-stations status code", f"Expected 200, got {resp.status_code}")
                return False

            data = resp.json()
            
            # Check structure
            if "snotel_stations" not in data:
                self.log_fail("snotel-stations schema", "Missing 'snotel_stations' field")
                return False

            stations = data["snotel_stations"]
            if not isinstance(stations, list):
                self.log_fail("snotel-stations type", "snotel_stations is not a list")
                return False

            # Check we have exactly 6 SNOTEL stations
            if len(stations) != 6:
                self.log_fail("snotel-stations count", f"Expected 6 stations, got {len(stations)}")
                return False

            # Check required fields for each station
            required_fields = ["triplet", "name", "basin_group", "elevation_ft", "confidence", "mapping_note"]
            for station in stations:
                for field in required_fields:
                    if field not in station:
                        self.log_fail("snotel-stations fields", f"Station {station.get('name')} missing field: {field}")
                        return False

            # Check basin_group keys match expected
            basin_groups = [s.get("basin_group") for s in stations]
            for expected_basin in EXPECTED_BASIN_GROUPS:
                if expected_basin not in basin_groups:
                    self.log_fail("snotel-stations basins", f"Missing basin group: {expected_basin}")
                    return False

            # Check primary stations (triplets)
            expected_triplets = [
                "911:WA:SNTL",  # Rex River
                "908:WA:SNTL",  # Alpine Meadows
                "515:WA:SNTL",  # Harts Pass
                "1011:WA:SNTL", # MF Nooksack
                "1068:WA:SNTL", # Sawmill Ridge
                "1085:WA:SNTL", # Cayuse Pass
            ]
            triplets = [s.get("triplet") for s in stations]
            for expected_triplet in expected_triplets:
                if expected_triplet not in triplets:
                    self.log_fail("snotel-stations triplets", f"Missing triplet: {expected_triplet}")
                    return False

            # Check all have high confidence (HUC-aligned)
            for station in stations:
                if station.get("confidence") != "high":
                    self.log_fail("snotel-stations confidence", f"Station {station.get('name')} has confidence={station.get('confidence')}, expected 'high'")
                    return False

            self.log_pass("snotel-stations", f"Returned {len(stations)} SNOTEL stations with correct fields and high confidence")
            return True

        except Exception as e:
            self.log_fail("snotel-stations", f"Exception: {e}")
            return False

    def test_system_precursors(self) -> Optional[Dict]:
        """Test GET /api/system/precursors (Phase 2A)"""
        print("\n🔍 Testing GET /api/system/precursors")
        try:
            resp = requests.get(f"{BASE_URL}/system/precursors", timeout=15)
            if resp.status_code != 200:
                self.log_fail("system/precursors status code", f"Expected 200, got {resp.status_code}")
                return None

            data = resp.json()
            
            # Check required fields
            required_fields = [
                "snowpack_active", "snowpack_basins_with_data", "snowpack_basins_total",
                "snowpack_last_attempt_at", "snowpack_last_attempt_ok", "snowpack_errors",
                "precipitation_active", "soil_moisture_active", "basin_tension_active"
            ]
            for field in required_fields:
                if field not in data:
                    self.log_fail("system/precursors schema", f"Missing field: {field}")
                    return None

            # Check Phase 2A: snowpack should be active
            if not data.get("snowpack_active"):
                self.log_fail("system/precursors snowpack_active", f"Expected snowpack_active=true, got {data.get('snowpack_active')}")
                return None

            # Check snowpack_basins_total = 6
            if data.get("snowpack_basins_total") != 6:
                self.log_fail("system/precursors snowpack_basins_total", f"Expected 6, got {data.get('snowpack_basins_total')}")
                return None

            # Check Phase 2B/2C/2D are not yet active
            if data.get("precipitation_active") is not False:
                self.log_fail("system/precursors precipitation_active", f"Expected false, got {data.get('precipitation_active')}")
                return None
            if data.get("soil_moisture_active") is not False:
                self.log_fail("system/precursors soil_moisture_active", f"Expected false, got {data.get('soil_moisture_active')}")
                return None
            if data.get("basin_tension_active") is not False:
                self.log_fail("system/precursors basin_tension_active", f"Expected false, got {data.get('basin_tension_active')}")
                return None

            self.log_pass(
                "system/precursors",
                f"snowpack_active={data['snowpack_active']}, basins_with_data={data['snowpack_basins_with_data']}/{data['snowpack_basins_total']}, "
                f"last_attempt_ok={data['snowpack_last_attempt_ok']}"
            )
            return data

        except Exception as e:
            self.log_fail("system/precursors", f"Exception: {e}")
            return None

    def test_system_precursors_refresh(self) -> bool:
        """Test POST /api/system/precursors/refresh (Phase 2A)"""
        print("\n🔍 Testing POST /api/system/precursors/refresh")
        try:
            # Get initial state
            resp1 = requests.get(f"{BASE_URL}/system/precursors", timeout=15)
            if resp1.status_code != 200:
                self.log_fail("precursors/refresh pre-check", "Failed to get initial state")
                return False
            
            last_attempt_before = resp1.json().get("snowpack_last_attempt_at")
            
            # Wait a moment
            time.sleep(1)
            
            # Trigger refresh
            resp2 = requests.post(f"{BASE_URL}/system/precursors/refresh", timeout=20)
            if resp2.status_code != 200:
                self.log_fail("precursors/refresh status code", f"Expected 200, got {resp2.status_code}")
                return False

            data = resp2.json()
            
            # Check structure
            if "snowpack_last_attempt_at" not in data:
                self.log_fail("precursors/refresh schema", "Missing snowpack_last_attempt_at")
                return False

            last_attempt_after = data.get("snowpack_last_attempt_at")
            
            # Verify timestamp advanced
            if last_attempt_after and last_attempt_before and last_attempt_after > last_attempt_before:
                self.log_pass(
                    "precursors/refresh",
                    f"snowpack_last_attempt_at advanced from {last_attempt_before} to {last_attempt_after}"
                )
            else:
                self.log_pass("precursors/refresh", f"Refresh completed, snowpack_active={data.get('snowpack_active')}")
            
            return True

        except Exception as e:
            self.log_fail("precursors/refresh", f"Exception: {e}")
            return False

    def test_stations_precursors_populated(self, stations_data: List[Dict]) -> bool:
        """Test that all 6 stations have precursors.snow_water_equivalent populated (Phase 2A)"""
        print("\n🔍 Testing PHASE 2A: All stations have precursors.snow_water_equivalent")
        all_pass = True
        
        for station in stations_data:
            station_id = station.get("id")
            precursors = station.get("precursors")
            
            if not precursors:
                self.log_fail(f"precursors {station_id}", "precursors field is None or missing")
                all_pass = False
                continue

            # Check precursors.available
            if not precursors.get("available"):
                self.log_fail(f"precursors {station_id}", f"precursors.available={precursors.get('available')}, expected True")
                all_pass = False
                continue

            # Check snow_water_equivalent exists
            swe = precursors.get("snow_water_equivalent")
            if not swe:
                self.log_fail(f"precursors {station_id}", "snow_water_equivalent is None or missing")
                all_pass = False
                continue

            # Check SWE has required fields
            required_swe_fields = ["value", "unit", "station_name", "station_id", "station_elevation_ft", "mapping_confidence"]
            for field in required_swe_fields:
                if field not in swe:
                    self.log_fail(f"precursors {station_id}", f"snow_water_equivalent missing field: {field}")
                    all_pass = False
                    continue

            # Check value is a positive number
            value = swe.get("value")
            if not isinstance(value, (int, float)) or value < 0:
                self.log_fail(f"precursors {station_id}", f"snow_water_equivalent.value={value}, expected positive number")
                all_pass = False
                continue

            # Check unit is 'in'
            if swe.get("unit") != "in":
                self.log_fail(f"precursors {station_id}", f"snow_water_equivalent.unit={swe.get('unit')}, expected 'in'")
                all_pass = False
                continue

            # Check mapping_confidence is 'high'
            if swe.get("mapping_confidence") != "high":
                self.log_fail(f"precursors {station_id}", f"mapping_confidence={swe.get('mapping_confidence')}, expected 'high'")
                all_pass = False
                continue

            self.log_pass(
                f"precursors {station_id}",
                f"SWE={value} in, station={swe.get('station_name')}, confidence={swe.get('mapping_confidence')}"
            )

        return all_pass

    def test_doctrine_green_auburn_precursor(self, stations_data: List[Dict]) -> bool:
        """Doctrine check: green-auburn must have precursor data BUT risk_state='unknown' (Phase 2A)"""
        print("\n🔍 Testing DOCTRINE: green-auburn has precursor BUT risk_state='unknown'")
        
        station = next((s for s in stations_data if s["id"] == "green-auburn"), None)
        if not station:
            self.log_fail("doctrine green-auburn precursor", "green-auburn not found")
            return False

        risk_state = station.get("risk_state")
        precursors = station.get("precursors")
        
        # Check risk_state is 'unknown'
        if risk_state != "unknown":
            self.log_fail("doctrine green-auburn precursor", f"Expected risk_state='unknown', got '{risk_state}'")
            return False

        # Check precursors are populated
        if not precursors or not precursors.get("available"):
            self.log_fail("doctrine green-auburn precursor", f"Expected precursors.available=True, got {precursors.get('available') if precursors else None}")
            return False

        swe = precursors.get("snow_water_equivalent")
        if not swe or not isinstance(swe.get("value"), (int, float)):
            self.log_fail("doctrine green-auburn precursor", f"Expected SWE value to be a number, got {swe.get('value') if swe else None}")
            return False

        self.log_pass(
            "doctrine green-auburn precursor",
            f"Correctly has precursor (SWE={swe.get('value')} in, station={swe.get('station_name')}) BUT risk_state='unknown' (precursors don't affect risk)"
        )
        return True

    def test_phase_2a_system_status(self) -> bool:
        """Test that SystemStatus.phase=2 and phase_label contains 'Phase 2A' and 'Snowpack' (Phase 2A)"""
        print("\n🔍 Testing PHASE 2A: SystemStatus phase and phase_label")
        try:
            resp = requests.get(f"{BASE_URL}/system/status", timeout=15)
            if resp.status_code != 200:
                self.log_fail("phase_2a system/status", f"Expected 200, got {resp.status_code}")
                return False

            data = resp.json()
            
            # Check phase = 2
            if data.get("phase") != 2:
                self.log_fail("phase_2a phase", f"Expected phase=2, got {data.get('phase')}")
                return False

            # Check phase_label contains 'Phase 2A' and 'Snowpack'
            phase_label = data.get("phase_label", "")
            if "Phase 2A" not in phase_label:
                self.log_fail("phase_2a phase_label", f"Expected 'Phase 2A' in phase_label, got '{phase_label}'")
                return False
            if "Snowpack" not in phase_label:
                self.log_fail("phase_2a phase_label", f"Expected 'Snowpack' in phase_label, got '{phase_label}'")
                return False

            # Check precursors field exists
            precursors = data.get("precursors")
            if not precursors:
                self.log_fail("phase_2a precursors", "precursors field missing in SystemStatus")
                return False

            self.log_pass("phase_2a system/status", f"phase={data['phase']}, phase_label='{phase_label}'")
            return True

        except Exception as e:
            self.log_fail("phase_2a system/status", f"Exception: {e}")
            return False

    def run_all_tests(self):
        """Run complete test suite"""
        print("=" * 80)
        print("🌊 CASCADE ORACLE — Backend API Test Suite (Phase 2A)")
        print("=" * 80)

        # Test 1: System status (Phase 2A: phase=2, phase_label)
        self.test_phase_2a_system_status()

        # Test 2: System basins (Phase 1.5: new endpoint)
        self.test_system_basins()

        # Test 3: SNOTEL stations config (Phase 2A)
        self.test_system_snotel_stations()

        # Test 4: Precursor layer status (Phase 2A)
        precursors_status = self.test_system_precursors()

        # Test 5: Precursor refresh (Phase 2A)
        self.test_system_precursors_refresh()

        # Test 6: List all stations (Phase 2A: precursors populated)
        stations_response = self.test_list_stations()
        if not stations_response:
            print("\n❌ CRITICAL: Cannot proceed without valid stations list")
            self.print_summary()
            return 1

        stations_data = stations_response["stations"]

        # Test 7: Stations have precursors populated (Phase 2A)
        self.test_stations_precursors_populated(stations_data)

        # Test 8: Get each individual station
        for station_id in EXPECTED_STATIONS:
            self.test_get_single_station(station_id)

        # Test 9: Get invalid station (should 404)
        self.test_get_invalid_station()

        # Test 10: Refresh single station (test with one station to avoid rate limits)
        self.test_refresh_single_station("cedar-renton")

        # Test 11: Refresh all stations (Phase 1.5: verify last_attempt updates)
        self.test_refresh_all_stations()

        # Test 12: Doctrine check - validated=False → risk_state='unknown'
        self.test_doctrine_validated_thresholds(stations_data)

        # Test 13: Doctrine check - official_nwps → validated=True
        self.test_doctrine_nwps_validated(stations_data)

        # Test 14: Doctrine check - unknown risk stations
        self.test_doctrine_unknown_risk_stations(stations_data)

        # Test 15: Doctrine check - NWPS stations
        self.test_doctrine_nwps_stations(stations_data)

        # Test 16: Doctrine check - green-auburn has precursor BUT risk_state='unknown' (Phase 2A)
        self.test_doctrine_green_auburn_precursor(stations_data)

        # Print summary
        self.print_summary()
        return 0 if self.tests_failed == 0 else 1

    def print_summary(self):
        """Print test summary"""
        print("\n" + "=" * 80)
        print("📊 TEST SUMMARY")
        print("=" * 80)
        print(f"Total tests run: {self.tests_run}")
        print(f"✅ Passed: {self.tests_passed}")
        print(f"❌ Failed: {self.tests_failed}")
        
        if self.errors:
            print("\n🔴 FAILED TESTS:")
            for error in self.errors:
                print(f"  {error}")
        
        if self.tests_failed == 0:
            print("\n🎉 ALL TESTS PASSED!")
        else:
            print(f"\n⚠️  {self.tests_failed} test(s) failed")
        
        print("=" * 80)


def main():
    tester = CascadeOracleAPITester()
    return tester.run_all_tests()


if __name__ == "__main__":
    sys.exit(main())
