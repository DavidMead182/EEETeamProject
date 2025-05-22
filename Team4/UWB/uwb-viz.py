#!/usr/bin/env python3
"""
UWB RTLS Visualization with Debug Logging
A visualization tool for ultra-wideband real-time location systems.
Automatically polls UWB system with "les" command to get tag positions.
"""

import serial
import re
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
import numpy as np
import argparse
import time
from matplotlib.patches import Circle
import threading
import queue
import serial.tools.list_ports
import random
from enum import Enum
import os
import configparser

class SimulationMode(Enum):
    OFF = 0
    BASIC = 1    # Simple tag movement (original demo mode)
    FULL = 2     # Full simulation including anchor placement and multiple tags

class UWBVisualizer:
    def __init__(self, port=None, baud_rate=115200, simulation_mode=None, config_file=None, poll_interval=0.5):
        print(f"[INIT] Initializing UWB Visualizer")
        print(f"[INIT] Port: {port}, Baud: {baud_rate}, Simulation: {simulation_mode}")
        print(f"[INIT] Config file: {config_file}, Poll interval: {poll_interval}s")
        
        # Initialize state variables
        self.default_anchors = [
            {"id": 1, "name": "Reference Anchor", "x": 0, "y": 0, "z": 0, "placed": False},
            {"id": 2, "name": "Right Anchor", "x": 1500, "y": 0, "z": 0, "placed": False},
            {"id": 3, "name": "Front Anchor", "x": 0, "y": 2100, "z": 0, "placed": False},
            {"id": 4, "name": "Diagonal Anchor", "x": 1500, "y": 2100, "z": 0, "placed": False},
        ]
        
        self.anchors = []
        
        # Load anchors from config file if provided
        if config_file and os.path.exists(config_file):
            print(f"[CONFIG] Loading configuration from {config_file}")
            self.load_config(config_file)
        else:
            print(f"[CONFIG] Using default anchor configuration")
            self.anchors = self.default_anchors.copy()
        
        self.tags = {}  # Dictionary to store tag data by ID
        self.tag_history = {}  # Store position history for each tag
        self.max_history = 20  # Number of positions to keep in history
        
        # UWB polling settings
        self.poll_interval = poll_interval  # Time between "les" commands
        self.last_poll_time = 0
        self.polling_enabled = True  # Enable/disable automatic polling
        self.les_command_sent = False  # Track if we've sent the initial "les" command
        
        # FIX: Determine simulation mode correctly
        if simulation_mode is not None:
            # Explicit simulation mode was requested
            self.simulation_mode = simulation_mode
            self.demo_mode = True
            self.polling_enabled = False  # Disable polling in simulation mode
            print(f"[INIT] Running in {simulation_mode.name} simulation mode")
        elif port is None:
            # No port specified, default to demo mode
            self.simulation_mode = SimulationMode.BASIC
            self.demo_mode = True
            self.polling_enabled = False
            print(f"[INIT] Running in demo mode (no port specified)")
        else:
            # Port specified, hardware mode
            self.simulation_mode = SimulationMode.OFF
            self.demo_mode = False
            self.polling_enabled = True
            print(f"[INIT] Hardware mode - will connect to {port}")
            
        self.setup_mode = True  # Start in setup mode (placing anchors)
        self.current_anchor_idx = 0
        
        # Simulation variables
        self.sim_time = 0
        self.sim_tags = ["D9AC", "E5F2", "B7C1"]  # Multiple tag IDs for full simulation
        self.sim_anchor_placement_time = 0
        self.auto_place_anchors = self.simulation_mode == SimulationMode.FULL
        self.sim_phase = "setup"  # setup, transition, tracking
        
        # Serial communication
        self.port = port
        self.baud_rate = baud_rate
        self.serial_connection = None
        self.data_queue = queue.Queue()
        
        # Config changes via serial commands
        self.command_mode = False
        self.command_buffer = ""
        
        # Statistics
        self.poll_count = 0
        self.last_data_time = time.time()
        
        # Set up the plot
        print(f"[INIT] Setting up visualization plot")
        self.setup_plot()
        
        # Connect to serial port if specified and not in simulation mode
        if not self.demo_mode:
            print(f"[INIT] Connecting to serial port...")
            self.connect_serial()
            # Start reading thread
            self.read_thread = threading.Thread(target=self.read_serial_data)
            self.read_thread.daemon = True
            self.read_thread.start()
            print(f"[INIT] Serial read thread started")
        else:
            print(f"[INIT] Skipping serial connection (demo/simulation mode)")
        
        print(f"[INIT] Initialization complete")
    
    def load_config(self, config_file):
        """Load anchor configuration from a file."""
        print(f"[CONFIG] Loading anchor configuration from {config_file}")
        try:
            if config_file.endswith('.ini'):
                self.load_ini_config(config_file)
            elif config_file.endswith('.txt'):
                self.load_txt_config(config_file)
            else:
                print(f"[CONFIG] Unsupported config file format: {config_file}")
                self.anchors = self.default_anchors.copy()
        except Exception as e:
            print(f"[CONFIG] Error loading config file: {e}")
            self.anchors = self.default_anchors.copy()
    
    def load_ini_config(self, config_file):
        """Load anchor configuration from an INI file."""
        config = configparser.ConfigParser()
        config.read(config_file)
        
        self.anchors = []
        print(f"[CONFIG] Found {len(config.sections())} sections in INI file")
        
        for section in config.sections():
            if section.startswith('Anchor'):
                try:
                    anchor_id = int(config[section].get('id', len(self.anchors) + 1))
                    anchor = {
                        "id": anchor_id,
                        "name": config[section].get('name', f"Anchor {anchor_id}"),
                        "x": float(config[section].get('x', 0)),
                        "y": float(config[section].get('y', 0)),
                        "z": float(config[section].get('z', 0)),
                        "placed": False
                    }
                    self.anchors.append(anchor)
                    print(f"[CONFIG] Loaded anchor {anchor_id}: {anchor['name']} at ({anchor['x']}, {anchor['y']}, {anchor['z']})")
                except Exception as e:
                    print(f"[CONFIG] Error parsing anchor {section}: {e}")
        
        # If no valid anchors were found, use default
        if not self.anchors:
            print("[CONFIG] No valid anchors found in config file, using default")
            self.anchors = self.default_anchors.copy()
        else:
            print(f"[CONFIG] Successfully loaded {len(self.anchors)} anchors from INI file")
    
    def load_txt_config(self, config_file):
        """Load anchor configuration from a text file."""
        self.anchors = []
        try:
            with open(config_file, 'r') as f:
                lines = f.readlines()
                
            print(f"[CONFIG] Processing {len(lines)} lines from TXT file")
            
            for i, line in enumerate(lines):
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                
                parts = line.split(',')
                if len(parts) >= 3:  # At least id, x, y needed
                    try:
                        anchor_id = int(parts[0])
                        anchor = {
                            "id": anchor_id,
                            "name": parts[1] if len(parts) > 1 else f"Anchor {anchor_id}",
                            "x": float(parts[2]),
                            "y": float(parts[3]) if len(parts) > 3 else 0,
                            "z": float(parts[4]) if len(parts) > 4 else 0,
                            "placed": False
                        }
                        self.anchors.append(anchor)
                        print(f"[CONFIG] Loaded anchor {anchor_id}: {anchor['name']} at ({anchor['x']}, {anchor['y']}, {anchor['z']})")
                    except Exception as e:
                        print(f"[CONFIG] Error parsing line {i+1}: {line} - {e}")
            
            # If no valid anchors were found, use default
            if not self.anchors:
                print("[CONFIG] No valid anchors found in config file, using default")
                self.anchors = self.default_anchors.copy()
            else:
                print(f"[CONFIG] Successfully loaded {len(self.anchors)} anchors from TXT file")
        except Exception as e:
            print(f"[CONFIG] Error reading config file: {e}")
            self.anchors = self.default_anchors.copy()
    
    def list_serial_ports(self):
        """List all available serial ports."""
        print(f"[SERIAL] Scanning for available serial ports...")
        ports = serial.tools.list_ports.comports()
        for port in ports:
            print(f"[SERIAL] Found port: {port.device} - {port.description}")
        return ports
    
    def connect_serial(self):
        """Connect to the specified serial port with debug output."""
        try:
            print(f"[CONNECT] Attempting to connect to {self.port} at {self.baud_rate} baud...")
            self.serial_connection = serial.Serial(self.port, self.baud_rate, timeout=1)
            print(f"[CONNECT] ✅ Connected successfully!")
            print(f"[CONNECT] Serial settings: {self.serial_connection}")
            
            
            print(f"[CONNECT] Sending initial setup commands...")
            self.send_uwb_command("")  # Send empty line to ensure we're at prompt
            time.sleep(0.2)
            self.send_uwb_command("")  # Send another empty line
            time.sleep(0.2)
            
            print(f"[CONNECT] UWB system ready for polling")
            print(f"[CONNECT] Will poll every {self.poll_interval} seconds")
            
        except Exception as e:
            print(f"[CONNECT] ❌ Connection failed: {e}")
            print("[CONNECT] Available ports:")
            self.list_serial_ports()
            self.demo_mode = True
            self.polling_enabled = False
    
    def send_uwb_command(self, command):
        """Send a command to the UWB system with debug output."""
        if self.serial_connection and self.serial_connection.is_open:
            try:
                full_command = f"{command}\r\n"
                bytes_written = self.serial_connection.write(full_command.encode('utf-8'))
                self.serial_connection.flush()  # Ensure data is sent immediately
                
                if command:  # Don't log empty commands
                    print(f"[SERIAL TX]: '{command}' ({bytes_written} bytes)")
                    print(f"             Raw: {repr(full_command)}")
                else:
                    print(f"[SERIAL TX]: <empty line> ({bytes_written} bytes)")
                    
            except Exception as e:
                print(f"[ERROR] Failed to send UWB command '{command}': {e}")
        else:
            print(f"[ERROR] Cannot send command '{command}' - serial not connected")
    
    def poll_uwb_data(self):
        """Monitor for incoming location data without sending commands."""
        if not self.polling_enabled or self.setup_mode or self.demo_mode:
            return
        
        # Just monitor - don't send any commands since device is already configured
        current_time = time.time()
        time_since_data = current_time - self.last_data_time
        
        # Only show warnings if we've been tracking for a while
        if hasattr(self, 'tracking_start_time'):
            tracking_duration = current_time - self.tracking_start_time
            
            if tracking_duration > 15.0 and time_since_data > 10.0:  # Warn after 10 seconds of no data
                print(f"[WARNING] No location data for {time_since_data:.1f} seconds")
                print(f"[WARNING] Make sure tags are active and in range")
                print(f"[WARNING] Expected format: TagID[x,y,z,quality,xSTATUS]")
        else:
            # Mark when we first enter tracking mode
            if not self.setup_mode:
                self.tracking_start_time = current_time
                print(f"[UWB] Entering tracking mode - listening for location data...")
                print(f"[UWB] Expected format: TagID[x,y,z,quality,xSTATUS]")
                print(f"[UWB] Device should already be configured to stream data")
                
                # Mark that we've "sent" the command (even though we didn't)
                # This prevents the old logic from trying to send les
                self.les_command_sent = True
    
    def read_serial_data(self):
        """Read serial data optimized for the clean format."""
        print("[SERIAL] Starting serial read thread...")
        
        while True:
            if self.serial_connection and self.serial_connection.is_open:
                try:
                    # Check if data is available
                    if self.serial_connection.in_waiting > 0:
                        print(f"[SERIAL] {self.serial_connection.in_waiting} bytes waiting")
                    
                    line = self.serial_connection.readline().decode('utf-8').strip()
                    if not line:
                        time.sleep(0.01)
                        continue
                    
                    # DEBUG: Show ALL serial input with timestamp
                    current_time = time.time()
                    timestamp = time.strftime("%H:%M:%S", time.localtime(current_time))
                    ms = int((current_time * 1000) % 1000)
                    print(f"[{timestamp}.{ms:03d}] RX: '{line}'")
                    print(f"                Raw: {repr(line)}")
                    
                    # Identify different types of lines
                    if line.startswith('CMD:'):
                        print(f"[SERIAL] Processing command response")
                        self.process_command(line[4:].strip())
                    elif line.startswith('RESP:'):
                        print(f"[SERIAL] Received response: {line[5:]}")
                    elif line.startswith('dwm>'):
                        print(f"[SERIAL] Received DWM command prompt")
                    elif 'DWM1001' in line or 'Copyright' in line or 'License' in line:
                        print(f"[SERIAL] Received system info/banner")
                    elif 'INF] loc_data:' in line:
                        print(f"[SERIAL] Location data header detected")
                    elif line.strip().startswith(')') and '[' in line and ']' in line:
                        # This looks like location data: " 0) D9AC[-0.26,3.05,3.12,64,x03]"
                        print(f"[SERIAL] Location data line detected - queuing for parsing")
                        self.data_queue.put(line)
                    elif 'INF]' in line:
                        print(f"[SERIAL] System info message")
                    else:
                        # Queue other data for processing
                        print(f"[SERIAL] Queuing data line for parsing")
                        self.data_queue.put(line)
                            
                except UnicodeDecodeError as e:
                    print(f"[ERROR] Unicode decode error: {e}")
                    raw_bytes = self.serial_connection.readline()
                    print(f"[ERROR] Raw bytes: {raw_bytes}")
                except Exception as e:
                    print(f"[ERROR] Serial read error: {e}")
                    print(f"[ERROR] Connection status: {self.serial_connection.is_open if self.serial_connection else 'None'}")
                    time.sleep(1)
            else:
                print("[SERIAL] No connection, waiting...")
                time.sleep(1)

    def parse_location_data(self, line):
        """Parse the clean DWM1001 location data format."""
        print(f"[PARSE] Input: '{line}'")
        print(f"[PARSE] Length: {len(line)} chars")
        
        # Format: D9AC[-0.26,3.05,3.12,64,x03]
        # This is the clean, original format we want
        pattern = r'(\w+)\[([-\d\.]+),([-\d\.]+),([-\d\.]+),(\d+),x([0-9A-Fa-f]+)\]'
        print(f"[PARSE] Looking for pattern: {pattern}")
        
        match = re.search(pattern, line)
        if match:
            print(f"[PARSE] ✅ Regex match found!")
            print(f"[PARSE] Groups: {match.groups()}")
            
            tag_id = match.group(1)
            raw_x = match.group(2)
            raw_y = match.group(3) 
            raw_z = match.group(4)
            quality = int(match.group(5))
            status_hex = match.group(6)
            status = int(status_hex, 16)
            
            # Convert coordinates from meters to mm
            x = float(raw_x) * 1000  # Convert to mm
            y = float(raw_y) * 1000
            z = float(raw_z) * 1000
            
            print(f"[PARSE] Tag ID: '{tag_id}'")
            print(f"[PARSE] Raw coords: ({raw_x}, {raw_y}, {raw_z}) meters")
            print(f"[PARSE] Converted:  ({x:.0f}, {y:.0f}, {z:.0f}) mm")
            print(f"[PARSE] Quality: {quality}%")
            print(f"[PARSE] Status: 0x{status:02X} (from '{status_hex}')")
            print(f"[PARSE] Status bits: valid={status & 0x01}, updated={status & 0x02}")
            
            # Update tag data
            old_tag = self.tags.get(tag_id, None)
            if old_tag:
                print(f"[PARSE] Updating existing tag {tag_id}")
                old_x, old_y = old_tag['x'], old_tag['y']
                distance_moved = ((x - old_x)**2 + (y - old_y)**2)**0.5
                print(f"[PARSE] Movement: {distance_moved:.0f}mm from last position")
                
                if distance_moved > 100:  # More than 10cm
                    print(f"[PARSE] ✅ Significant movement detected!")
                elif distance_moved > 10:  # More than 1cm
                    print(f"[PARSE] ✅ Small movement detected")
                else:
                    print(f"[PARSE] ⚠️  Minimal movement (noise/precision)")
            else:
                print(f"[PARSE] Creating new tag {tag_id}")
            
            self.tags[tag_id] = {
                "id": tag_id, "x": x, "y": y, "z": z,
                "quality": quality, "status": status,
                "valid": status & 0x01, "updated": status & 0x02,
                "high_confidence": status & 0x04, "low_confidence": status & 0x08,
                "timestamp": time.time()
            }
            
            # Update history
            if tag_id not in self.tag_history:
                self.tag_history[tag_id] = []
                print(f"[PARSE] Created new history for tag {tag_id}")
            
            self.tag_history[tag_id].append((x, y))
            if len(self.tag_history[tag_id]) > self.max_history:
                self.tag_history[tag_id].pop(0)
                
            print(f"[PARSE] History length: {len(self.tag_history[tag_id])}")
            
            self.last_data_time = time.time()
            print(f"[PARSE] ✅ Successfully processed tag {tag_id}")
            return True
        else:
            print(f"[PARSE] ❌ No regex match found")
            # Try to identify what type of line this might be
            if 'dwm>' in line.lower():
                print(f"[PARSE] Looks like a DWM prompt")
            elif 'loc_data:' in line:
                print(f"[PARSE] Location data header - next line should have coordinates")
            elif 'INF]' in line:
                print(f"[PARSE] System info/log message")
            elif len(line) == 0:
                print(f"[PARSE] Empty line")
            elif line.isspace():
                print(f"[PARSE] Whitespace only")
            elif line.strip().isdigit():
                print(f"[PARSE] Looks like a line number")
            else:
                print(f"[PARSE] Unknown format - might be partial data")
                # Show character analysis for debugging
                print(f"[PARSE] First 50 chars: {repr(line[:50])}")
            return False

    def parse_anchor_distances(self, line):
        """Parse anchor position and distance data from the line."""
        print(f"[PARSE] Parsing anchor distance data...")
        
        # Pattern for anchor data: 938D[3.30,2.10,0.00]=1.87
        anchor_pattern = r'([0-9A-Fa-f]{4})\[([-\d\.]+),([-\d\.]+),([-\d\.]+)\]=([-\d\.]+)'
        anchor_matches = re.findall(anchor_pattern, line)
        
        if anchor_matches:
            print(f"[PARSE] Found {len(anchor_matches)} anchor measurements:")
            
            for anchor_data in anchor_matches:
                anchor_id = anchor_data[0]
                anchor_x = float(anchor_data[1]) * 1000  # Convert to mm
                anchor_y = float(anchor_data[2]) * 1000
                anchor_z = float(anchor_data[3]) * 1000
                distance = float(anchor_data[4])
                
                print(f"[PARSE]   Anchor {anchor_id}: pos=({anchor_x:.0f},{anchor_y:.0f},{anchor_z:.0f})mm, dist={distance:.2f}m")
                
                # You could use this data to verify anchor positions or show distances
                # For now, just log it for debugging
        
        # Parse timing data
        timing_match = re.search(r'le_us=(\d+)', line)
        if timing_match:
            timing_us = int(timing_match.group(1))
            print(f"[PARSE] Localization time: {timing_us} microseconds")
    
    def setup_plot(self):
        """Initialize the matplotlib plot."""
        self.fig, self.ax = plt.subplots(figsize=(10, 8))
        self.fig.canvas.manager.set_window_title('UWB RTLS Visualization')
        
        # Set up the plot area
        if self.anchors:
            max_x = max([anchor["x"] for anchor in self.anchors]) * 1.2
            max_y = max([anchor["y"] for anchor in self.anchors]) * 1.2
        else:
            max_x = 2000
            max_y = 2000
        
        self.ax.set_xlim(-500, max_x)
        self.ax.set_ylim(-500, max_y)
        self.ax.set_xlabel('X Position (mm)')
        self.ax.set_ylabel('Y Position (mm)')
        self.ax.grid(True)
        
        # Add interactive elements
        self.fig.canvas.mpl_connect('key_press_event', self.on_key_press)
        
        # Status text
        self.status_text = self.ax.text(0.02, 0.98, 'Setup Mode: Place anchors', 
                                       transform=self.ax.transAxes, fontsize=12,
                                       verticalalignment='top')
        
        # Add a demo mode indicator if in demo mode
        if self.demo_mode:
            self.ax.text(0.98, 0.02, 'DEMO MODE', transform=self.ax.transAxes, fontsize=12,
                         color='red', horizontalalignment='right')
    
    def on_key_press(self, event):
        """Handle key press events for interaction."""
        print(f"[KEY] Key pressed: {event.key}")
        
        if event.key == ' ':  # Space bar
            if self.setup_mode and self.current_anchor_idx < len(self.anchors):
                # Mark the current anchor as placed
                self.anchors[self.current_anchor_idx]["placed"] = True
                print(f"[KEY] Placed anchor {self.current_anchor_idx + 1}: {self.anchors[self.current_anchor_idx]['name']}")
                self.current_anchor_idx += 1
                
                if self.current_anchor_idx >= len(self.anchors):
                    self.setup_mode = False
                    print(f"[KEY] All anchors placed, entering tracking mode")
        elif event.key == 'r':  # Reset
            print(f"[KEY] Resetting visualization")
            self.reset_visualization()
        elif event.key == 'p':  # Toggle UWB polling
            if not self.demo_mode:
                self.polling_enabled = not self.polling_enabled
                print(f"[KEY] UWB polling: {'ON' if self.polling_enabled else 'OFF'}")
                if self.polling_enabled:
                    print(f"[KEY] Polling every {self.poll_interval} seconds")
            else:
                print("[KEY] UWB polling not available in demo mode")
        else:
            print(f"[KEY] Unhandled key: {event.key}")
    
    def reset_visualization(self):
        """Reset the visualization to setup mode."""
        self.setup_mode = True
        self.current_anchor_idx = 0
        for anchor in self.anchors:
            anchor["placed"] = False
        self.tags = {}
        self.tag_history = {}
        self.poll_count = 0
        self.last_data_time = time.time()
        self.les_command_sent = False  # Reset so "les" can be sent again
        print("[RESET] Visualization reset to setup mode")
    
    def update_plot(self, frame):
        """Update the plot with the latest data."""
        self.ax.clear()
        
        # Poll for UWB data if connected to real hardware
        if self.polling_enabled and not self.demo_mode:
            self.poll_uwb_data()
        
        # Set up the plot area again
        if self.anchors:
            max_x = max([anchor["x"] for anchor in self.anchors]) * 1.2
            max_y = max([anchor["y"] for anchor in self.anchors]) * 1.2
            max_x = max(max_x, 2000)  # Ensure minimum size
            max_y = max(max_y, 2000)
        else:
            max_x = 2000
            max_y = 2000
        
        self.ax.set_xlim(-500, max_x)
        self.ax.set_ylim(-500, max_y)
        self.ax.set_xlabel('X Position (mm)')
        self.ax.set_ylabel('Y Position (mm)')
        self.ax.grid(True)
        
        # Process any new data in the queue
        queue_size = self.data_queue.qsize()
        if queue_size > 0:
            print(f"[QUEUE] Processing {queue_size} items from data queue")

        processed_items = 0
        while not self.data_queue.empty():
            line = self.data_queue.get()
            print(f"[QUEUE] Processing item {processed_items + 1}: '{line}'")
            success = self.parse_location_data(line)
            if success:
                print(f"[QUEUE] ✅ Item {processed_items + 1} parsed successfully")
            else:
                print(f"[QUEUE] ❌ Item {processed_items + 1} failed to parse")
            processed_items += 1

        if processed_items > 0:
            print(f"[QUEUE] Finished processing {processed_items} items")
        
        # Handle simulation if enabled
        if self.simulation_mode != SimulationMode.OFF:
            self.run_simulation()
        
        # Draw anchors
        for i, anchor in enumerate(self.anchors):
            if anchor["placed"] or not self.setup_mode:
                self.ax.plot(anchor["x"], anchor["y"], 'bs', markersize=10)
                self.ax.text(anchor["x"], anchor["y"] + 100, anchor["name"], 
                           ha='center', va='bottom', fontsize=8)
            elif i == self.current_anchor_idx:
                # Highlight the current anchor to be placed
                self.ax.plot(anchor["x"], anchor["y"], 'bs', markersize=10, alpha=0.5)
                self.ax.text(anchor["x"], anchor["y"] + 100, f"Place {anchor['name']} (Press Space)", 
                           ha='center', va='bottom', fontsize=8, color='blue')
        
        # Draw tags and their trails
        for tag_id, tag in self.tags.items():
            # Don't show tags in setup mode
            if self.setup_mode:
                continue
                
            quality_color = self.get_quality_color(tag["quality"])
            
            # Draw the tag
            self.ax.plot(tag["x"], tag["y"], 'ro', markersize=8, color=quality_color)
            
            # Draw the tag's trail
            if tag_id in self.tag_history:
                history = self.tag_history[tag_id]
                if len(history) > 1:
                    x_values, y_values = zip(*history)
                    self.ax.plot(x_values, y_values, '-', color=quality_color, alpha=0.5)
            
            # Draw tag info
            self.ax.text(tag["x"], tag["y"] + 100, 
                      f"Tag {tag_id}\nQuality: {tag['quality']:.0f}%\nStatus: 0x{tag['status']:02X}", 
                      ha='center', va='bottom', fontsize=8)
        
        # Update status text
        if self.setup_mode:
            if len(self.anchors) == 0:
                status = 'No anchors configured.'
            elif self.current_anchor_idx < len(self.anchors):
                status = f'Setup Mode: Place {self.anchors[self.current_anchor_idx]["name"]} (Press Space)'
            else:
                self.setup_mode = False
                status = 'Tracking Mode: Monitoring tags'
        else:
            # Show polling status in tracking mode
            status = 'Tracking Mode: Monitoring tags (Press R to reset)'
            if self.polling_enabled and not self.demo_mode:
                time_since_data = time.time() - self.last_data_time
                status += f'\nPolling UWB every {self.poll_interval}s (polls: {self.poll_count})'
                if time_since_data > 5:
                    status += f'\nNo data for {time_since_data:.1f}s'
        
        self.status_text = self.ax.text(0.02, 0.98, status, 
                                     transform=self.ax.transAxes, fontsize=12,
                                     verticalalignment='top')
        
        # Add mode indicator
        if not self.demo_mode and self.polling_enabled:
            mode_text = f"UWB POLLING ({self.poll_interval}s)"
            color = 'green'
        elif not self.demo_mode:
            mode_text = "UWB CONNECTED"
            color = 'orange'
        else:
            mode_text = "DEMO MODE"
            color = 'red'
            
        self.ax.text(0.98, 0.02, mode_text, transform=self.ax.transAxes, fontsize=12,
                 color=color, horizontalalignment='right')
        
        # Add key controls info
        controls_text = "Controls:\n- Space: Place anchor\n- R: Reset\n- P: Toggle polling"
        self.ax.text(0.98, 0.98, controls_text, transform=self.ax.transAxes, fontsize=10,
                  horizontalalignment='right', verticalalignment='top',
                  bbox=dict(facecolor='white', alpha=0.5))
        
        return self.ax,
    
    def get_quality_color(self, quality):
        """Return a color based on the quality percentage."""
        if quality >= 75:
            return 'green'
        elif quality >= 50:
            return 'orange'
        elif quality >= 25:
            return 'darkorange'
        else:
            return 'red'
    
    def run_simulation(self):
        """Run basic simulation for demo purposes."""
        pass  # Simplified for debugging focus
    
    def run(self):
        """Run the visualization."""
        print("[START] Starting UWB RTLS Visualization")
        print(f"[START] Anchors configured: {len(self.anchors)}")
        for anchor in self.anchors:
            print(f"[START]   {anchor['name']}: ({anchor['x']}, {anchor['y']}, {anchor['z']})")
        
        # Fix the matplotlib warning by setting cache_frame_data=False
        self.animation = FuncAnimation(self.fig, self.update_plot, interval=100, 
                                     blit=False, cache_frame_data=False)
        plt.tight_layout()
        
        try:
            plt.show()
        except KeyboardInterrupt:
            print("\n[EXIT] Received keyboard interrupt, shutting down...")
            if self.serial_connection and self.serial_connection.is_open:
                print("[EXIT] Closing serial connection...")
                self.serial_connection.close()
            print("[EXIT] Goodbye!")

def main():
    parser = argparse.ArgumentParser(description='UWB RTLS Visualization with Debug Logging')
    parser.add_argument('--port', type=str, help='Serial port to connect to (e.g., COM3 or /dev/ttyUSB0)')
    parser.add_argument('--baud', type=int, default=115200, help='Baud rate for serial connection')
    parser.add_argument('--list-ports', action='store_true', help='List available serial ports and exit')
    parser.add_argument('--simulation', choices=['basic', 'full'], help='Run in simulation mode without hardware')
    parser.add_argument('--config', type=str, help='Load anchor configuration from file (INI or TXT format)')
    parser.add_argument('--poll-interval', type=float, default=1, help='Interval between UWB polls in seconds (default: 0.5)')
    parser.add_argument('--no-poll', action='store_true', help='Disable automatic UWB polling')
    
    args = parser.parse_args()
    
    print(f"[MAIN] UWB RTLS Visualizer starting...")
    print(f"[MAIN] Arguments: {vars(args)}")
    
    if args.list_ports:
        print("[MAIN] Listing available serial ports...")
        visualizer = UWBVisualizer()
        visualizer.list_serial_ports()
        return
    
    # Determine simulation mode
    sim_mode = None
    if args.simulation == 'basic':
        sim_mode = SimulationMode.BASIC
    elif args.simulation == 'full':
        sim_mode = SimulationMode.FULL
    
    print(f"[MAIN] Creating visualizer...")
    
    # Create the visualizer
    try:
        visualizer = UWBVisualizer(port=args.port, baud_rate=args.baud, 
                                 simulation_mode=sim_mode, config_file=args.config,
                                 poll_interval=args.poll_interval)
        
        # Disable polling if requested
        if args.no_poll:
            visualizer.polling_enabled = False
            print("[MAIN] UWB polling disabled by --no-poll flag")
        
        # Display connection info
        if not visualizer.demo_mode and visualizer.polling_enabled:
            print(f"[MAIN] Connected to UWB system on {args.port}")
            print(f"[MAIN] Polling for tag data every {args.poll_interval} seconds")
            print("[MAIN] Use 'P' key to toggle polling, 'R' to reset")
        elif not visualizer.demo_mode:
            print(f"[MAIN] Connected to UWB system on {args.port} (polling disabled)")
        
        print("[MAIN] Starting visualization...")
        visualizer.run()
        
    except Exception as e:
        print(f"[MAIN] Error creating or running visualizer: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()