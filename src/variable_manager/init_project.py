import os
import shutil
from pathlib import Path

STANDARD_TEST_PALETTE_CONTENT = """id: https://example.org/electronic-manufacturing-test-palette
name: electronic_manufacturing_test_palette
title: Electronic Manufacturing Test & Calibration Palette (LinkML)
description: >
  TestStand-inspired type palette for electronic manufacturing test and calibration sequences.
  Defines customized data types, measurement units, and default values.

classes:
  VoltageMeasurement:
    description: Voltage test measurement specification
    slots:
      - nominal_value
      - upper_limit
      - lower_limit
      - unit
    slot_usage:
      nominal_value:
        range: float
        description: Expected nominal voltage
        ifabsent: "5.0"
      upper_limit:
        range: float
        description: Maximum acceptable voltage limit
        ifabsent: "5.25"
      lower_limit:
        range: float
        description: Minimum acceptable voltage limit
        ifabsent: "4.75"
      unit:
        range: string
        description: Measurement unit
        ifabsent: "V"

  CalibrationParameter:
    description: Sensor or circuit calibration coefficient
    slots:
      - gain
      - offset
    slot_usage:
      gain:
        range: float
        description: Multiplicative calibration gain factor
        ifabsent: "1.0"
      offset:
        range: float
        description: Additive calibration offset
        ifabsent: "0.0"

  InstrumentReference:
    description: Reference to test bench instrument (e.g. DMM, Oscilloscope)
    slots:
      - instrument_id
      - connection_address
    slot_usage:
      instrument_id:
        range: string
        description: Instrument name
        ifabsent: "DMM_Keysight_34401A"
      connection_address:
        range: string
        description: VISA or IP address
        ifabsent: "TCPIP0::192.168.1.100::INSTR"

slots:
  nominal_value:
    name: nominal_value
    range: float
  upper_limit:
    name: upper_limit
    range: float
  lower_limit:
    name: lower_limit
    range: float
  unit:
    name: unit
    range: string
  gain:
    name: gain
    range: float
  offset:
    name: offset
    range: float
  instrument_id:
    name: instrument_id
    range: string
  connection_address:
    name: connection_address
    range: string
"""

TEMPLATE_SEQUENCE_CONTENT = '''"""
Electronic Manufacturing Test & Calibration Sequence Example
Inspired by NI TestStand execution model with multi-namespace variables and LinkML types.
"""
import requests

API_URL = "http://localhost:8000"

def initialize_test_station():
    print("Initializing Test Station and Loading Station Globals...")
    # Station globals: defining concrete reachable test equipment & calibration bench
    requests.post(f"{API_URL}/variables", json={
        "namespace": "station_globals",
        "name": "active_multimeter",
        "type": "InstrumentReference",
        "description": "Primary digital multimeter for board power test"
    })

def run_test_case(serial_number: str):
    print(f"\\n--- Running Test & Calibration Sequence for UUT: {serial_number} ---")
    
    # 1. Sequence Global: test batch configuration
    requests.post(f"{API_URL}/variables", json={
        "namespace": "sequence_global",
        "name": "uut_serial_number",
        "value": serial_number,
        "type": "string"
    })
    
    # 2. Local: individual test case step (Voltage measurement test using LinkML palette default)
    requests.post(f"{API_URL}/variables", json={
        "namespace": "local",
        "name": "vcc_rail_test",
        "type": "VoltageMeasurement",
        "description": "5V VCC power rail verification"
    })
    
    # Retrieve runtime execution values
    vcc_spec = requests.get(f"{API_URL}/variables/local/vcc_rail_test").json()
    multimeter = requests.get(f"{API_URL}/variables/station_globals/active_multimeter").json()
    
    print(f"Executing test step with instrument: {multimeter['value']}")
    print(f"Voltage test spec -> Nominal: {vcc_spec['value']['nominal_value']} {vcc_spec['value']['unit']} "
          f"(Limits: [{vcc_spec['value']['lower_limit']}, {vcc_spec['value']['upper_limit']}])")
    print("Test Result: PASS [Measured: 5.02 V]")

if __name__ == "__main__":
    initialize_test_station()
    run_test_case("SN-2026-9988")
'''

TEMPLATE_STATION_CONFIG = """station_id: "TEST_BENCH_ALPHA_01"
manufacturer: "Electronics Test Solutions Corp"
instruments:
  - name: "DMM_Keysight_34401A"
    type: "DigitalMultimeter"
    address: "TCPIP0::192.168.1.100::INSTR"
  - name: "DC_Power_Supply"
    type: "ProgrammablePowerSupply"
    address: "GPIB0::5::INSTR"
safety_interlock: true
"""

def initialize_project(project_name: str):
    base_path = Path(project_name)
    print(f"Initializing Electronic Manufacturing Test Project at: {base_path.absolute()}")
    
    # Create directory structure
    dirs = [
        base_path / "types",
        base_path / "sequences",
        base_path / "station",
        base_path / "models",
        base_path / "ontologies"
    ]
    for d in dirs:
        d.mkdir(parents=True, exist_ok=True)
        
    # Write standard type palette
    palette_path = base_path / "types" / "standard_test_palette.yaml"
    palette_path.write_text(STANDARD_TEST_PALETTE_CONTENT)
    print(f"Created standard LinkML type palette: {palette_path}")
    
    # Write sample sequence script
    seq_path = base_path / "sequences" / "test_calibration_sequence.py"
    seq_path.write_text(TEMPLATE_SEQUENCE_CONTENT)
    print(f"Created sample test sequence: {seq_path}")
    
    # Write station configuration
    station_path = base_path / "station" / "station_config.yaml"
    station_path.write_text(TEMPLATE_STATION_CONFIG)
    print(f"Created station configuration: {station_path}")
    
    print(f"Project '{project_name}' successfully initialized!")
