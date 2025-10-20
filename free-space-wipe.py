#!/usr/bin/env python3
import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, GLib
import shutil
import os
import subprocess
import json
import threading
import time
import random
import string

class HealthPanelWindow(Gtk.Window):
    def __init__(self, parent_window, drive_info):
        super().__init__(title="Drive Health Monitor")
        self.parent_window = parent_window
        self.drive_info = drive_info
        self.set_default_size(300, 400)
        self.set_border_width(10)
        self.set_resizable(False)
        self.set_decorated(False)  # Remove window decorations
        
        # Make it stay on top
        self.set_keep_above(True)
        
        # Connect destroy signal
        self.connect("destroy", self.on_health_panel_close)
        
        # Main container
        main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        self.add(main_box)
        
        # Title bar with close button
        title_hbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=5)
        
        title_label = Gtk.Label(label=f"Health: {drive_info['name']}")
        title_label.set_markup(f"<b>Health: {drive_info['name']}</b>")
        title_hbox.pack_start(title_label, True, True, 0)
        
        # Close button
        close_button = Gtk.Button(label="✕")
        close_button.set_size_request(30, 30)
        close_button.connect("clicked", self.on_close_clicked)
        title_hbox.pack_end(close_button, False, False, 0)
        
        main_box.pack_start(title_hbox, False, False, 0)
        
        # Health data container
        self.health_data_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)
        main_box.pack_start(self.health_data_box, True, True, 0)
        
        # Loading label
        self.loading_label = Gtk.Label(label="Loading health data...")
        self.health_data_box.pack_start(self.loading_label, True, True, 0)
        
        # Overall assessment at bottom
        self.assessment_label = Gtk.Label()
        self.assessment_label.set_markup("<b>SSD Status:</b> <span foreground='gray'>Calculating...</span>")
        main_box.pack_end(self.assessment_label, False, False, 10)
        
        # Position window to the right of parent
        self.position_next_to_parent()
        
        # Load health data
        self.load_health_data()
    
    def position_next_to_parent(self):
        """Position the health panel to the right of the main window"""
        if self.parent_window:
            # Get parent window position
            parent_x, parent_y = self.parent_window.get_position()
            parent_width = self.parent_window.get_allocated_width()
            
            # Position to the right of parent with small gap
            self.move(parent_x + parent_width + 10, parent_y)
    
    def on_health_panel_close(self, widget):
        """Called when health panel is closed"""
        # Notify parent that panel is closed
        if self.parent_window:
            self.parent_window.health_panel = None
    
    def on_close_clicked(self, button):
        """Handle close button click"""
        self.destroy()
    
    def load_health_data(self):
        """Load and parse SMART health data"""
        device_name = self.drive_info['name']
        physical_device = self.parent_window._get_physical_device(device_name)
        device_path = f"/dev/{physical_device}"
        
        # Check if smartctl is installed
        try:
            subprocess.run(['which', 'smartctl'], check=True, capture_output=True)
        except subprocess.CalledProcessError:
            self.show_error("smartctl not found")
            return
        
        # Use smartctl for SMART data access (assumes script runs with sudo)
        try:
            result = subprocess.run(
                ['smartctl', '-A', device_path],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode in [0, 4]:
                # Check if this is NVMe format (starts with SMART/Health Information)
                if "SMART/Health Information" in result.stdout:
                    self.parse_nvme_health_data(result.stdout)
                else:
                    self.parse_health_data(result.stdout)
            else:
                self.show_error("Failed to read SMART data")
        except Exception as e:
            self.show_error(f"Error: {str(e)}")
    
    def parse_nvme_health_data(self, smart_output):
        """Parse NVMe SMART data format"""
        # Clear loading label
        self.health_data_box.remove(self.loading_label)
        
        health_data = {}
        lines = smart_output.strip().split('\n')
        
        for line in lines:
            line = line.strip()
            if ':' in line and not line.startswith('==='):
                parts = line.split(':', 1)
                if len(parts) == 2:
                    key = parts[0].strip()
                    value = parts[1].strip()
                    
                    # Map NVMe attributes to our relevant attributes
                    if 'Temperature' in key and 'Sensor' not in key:
                        try:
                            temp = int(value.split()[0])
                            health_data['Temperature'] = f"{temp}°C"
                        except:
                            pass
                    elif 'Available Spare' in key and 'Threshold' not in key:
                        health_data['Available Reserved Space'] = value
                    elif 'Percentage Used' in key:
                        # This is wear indicator - invert it for SSD life left
                        try:
                            used_percent = int(value.replace('%', ''))
                            life_left = 100 - used_percent
                            health_data['Media Wearout Indicator'] = f"{life_left}%"
                            health_data['SSD Life Left'] = f"{life_left}%"
                        except:
                            pass
                    elif 'Data Units Written' in key:
                        # Extract TB written
                        if '[' in value and 'TB' in value:
                            tb_written = value.split('[')[1].split('TB')[0].strip()
                            health_data['Total LBAs Written'] = f"{tb_written} TB"
                            health_data['Total GBs Written'] = f"{float(tb_written) * 1024:.0f} GB"
                    elif 'Data Units Read' in key:
                        if '[' in value and 'TB' in value:
                            tb_read = value.split('[')[1].split('TB')[0].strip()
                            health_data['Total LBAs Read'] = f"{tb_read} TB"
                            health_data['Total GBs Read'] = f"{float(tb_read) * 1024:.0f} GB"
                    elif 'Power Cycles' in key:
                        health_data['Power Cycle Count'] = value
                    elif 'Power On Hours' in key:
                        hours = int(value.replace(',', ''))
                        days = hours // 24
                        health_data['Power On Hours'] = f"{hours}h ({days}d)"
                    elif 'Media and Data Integrity Errors' in key:
                        if int(value) > 0:
                            health_data['Reported Uncorrectable Errors'] = value
                    elif 'Unsafe Shutdowns' in key:
                        if int(value) > 0:
                            health_data['Unexpected Power Loss Count'] = value
                    elif 'Controller Busy Time' in key:
                        health_data['Controller Busy Time'] = f"{value} min"
        
        # Display the health data
        if health_data:
            for attr_name, value in sorted(health_data.items()):
                hbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
                
                name_label = Gtk.Label(label=f"{attr_name}:")
                name_label.set_xalign(0)
                name_label.set_size_request(150, -1)
                
                value_label = Gtk.Label(label=value)
                value_label.set_xalign(0)
                
                hbox.pack_start(name_label, False, False, 0)
                hbox.pack_start(value_label, True, True, 0)
                
                self.health_data_box.pack_start(hbox, False, False, 2)
        else:
            no_data_label = Gtk.Label(label="No NVMe health data found")
            self.health_data_box.pack_start(no_data_label, True, True, 0)
        
        # Calculate and display overall assessment
        self.calculate_ssd_assessment(health_data)
        
        self.show_all()

    def parse_health_data(self, smart_output):
        """Parse SMART attributes and display relevant ones"""
        # Clear loading label
        self.health_data_box.remove(self.loading_label)
        
        # Relevant SMART attributes for SSD health during wiping
        relevant_attributes = {
            '241': 'Total LBAs Written',
            '231': 'SSD Life Left',
            '230': 'Drive Life Protection Status',
            '177': 'Wear Leveling Count',
            '173': 'Wear Leveling Count',
            '232': 'Available Reserved Space',
            '233': 'Media Wearout Indicator',
            '194': 'Temperature',
            '195': 'Hardware ECC Recovered',
            '5': 'Reallocated Sector Count',
            '196': 'Reallocated Event Count',
            '197': 'Current Pending Sector Count',
            '198': 'Offline Uncorrectable Sector Count',
            '9': 'Power On Hours',
            '12': 'Power Cycle Count',
            '170': 'Available Reserved Space',
            '171': 'SSD Program Fail Count',
            '172': 'SSD Erase Fail Count',
            '174': 'Unexpected Power Loss Count',
            '175': 'Power Loss Protection',
            '176': 'Erase Fail Count',
            '179': 'Used Reserved Block Count',
            '180': 'Unused Reserved Block Count',
            '181': 'Program Fail Count',
            '182': 'Erase Fail Count',
            '183': 'Runtime Bad Block Count',
            '184': 'End-to-End Error',
            '187': 'Reported Uncorrectable Errors',
            '188': 'Command Timeout',
            '189': 'High Fly Writes',
            '190': 'Airflow Temperature',
            '191': 'G-Sense Error Rate',
            '192': 'Power-off Retract Count',
            '193': 'Load Cycle Count',
            '199': 'UDMA CRC Error Count',
            '200': 'Multi-Zone Error Rate',
            '240': 'Head Flying Hours',
            '242': 'Total LBAs Read',
            '245': 'Flash Write Error Rate',
            '246': 'Total GBs Written',
            '247': 'Total GBs Read'
        }
        
        # Parse the output
        health_data = {}
        lines = smart_output.strip().split('\n')
        
        for line in lines:
            parts = line.strip().split()
            if len(parts) >= 10 and parts[0].isdigit():
                attr_id = parts[0]
                if attr_id in relevant_attributes:
                    attr_name = relevant_attributes[attr_id]
                    raw_value = parts[-1] if parts[-1] != '-' else parts[-2]
                    
                    # Format the value nicely
                    try:
                        if 'Temperature' in attr_name:
                            value = f"{raw_value}°C"
                        elif 'Hours' in attr_name:
                            hours = int(raw_value)
                            days = hours // 24
                            value = f"{hours}h ({days}d)"
                        elif 'Count' in attr_name or 'Written' in attr_name or 'Read' in attr_name:
                            # Format large numbers
                            num = int(raw_value)
                            if num > 1000000:
                                value = f"{num/1000000:.1f}M"
                            elif num > 1000:
                                value = f"{num/1000:.1f}K"
                            else:
                                value = str(num)
                        else:
                            value = raw_value
                    except:
                        value = raw_value
                    
                    health_data[attr_name] = value
        
        # Display the health data
        if health_data:
            for attr_name, value in sorted(health_data.items()):
                hbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
                
                name_label = Gtk.Label(label=f"{attr_name}:")
                name_label.set_xalign(0)
                name_label.set_size_request(150, -1)
                
                value_label = Gtk.Label(label=value)
                value_label.set_xalign(0)
                
                hbox.pack_start(name_label, False, False, 0)
                hbox.pack_start(value_label, True, True, 0)
                
                self.health_data_box.pack_start(hbox, False, False, 2)
        else:
            no_data_label = Gtk.Label(label="No relevant health data found")
            self.health_data_box.pack_start(no_data_label, True, True, 0)
        
        # Calculate and display overall assessment
        self.calculate_ssd_assessment(health_data)
        
        self.show_all()
    
    def calculate_ssd_assessment(self, health_data):
        """Calculate overall SSD health assessment with 5-level system"""
        drive_type = self.drive_info.get('type', 'Unknown')
        
        if 'SSD' not in drive_type:
            self.assessment_label.set_markup("<b>Drive Type:</b> <span foreground='blue'>Non-SSD</span>")
            return
        
        # Initialize scoring factors
        life_remaining = None
        temperature = None
        error_count = 0
        reserved_space = None
        
        # Extract life remaining (most important factor)
        if 'Media Wearout Indicator' in health_data or 'SSD Life Left' in health_data:
            try:
                key = 'Media Wearout Indicator' if 'Media Wearout Indicator' in health_data else 'SSD Life Left'
                life_remaining = int(health_data[key].replace('%', ''))
            except:
                pass
        
        # Extract temperature
        if 'Temperature' in health_data:
            try:
                temp_str = health_data['Temperature'].replace('°C', '').strip()
                temperature = int(temp_str)
            except:
                pass
        
        # Count errors
        error_indicators = ['Reallocated Sector Count', 'Current Pending Sector Count',
                           'Reported Uncorrectable Errors', 'Command Timeout']
        for indicator in error_indicators:
            if indicator in health_data:
                try:
                    value = int(health_data[indicator])
                    if value > 0:
                        error_count += value
                except:
                    pass
        
        # Check reserved space
        if 'Available Reserved Space' in health_data:
            try:
                reserved = health_data['Available Reserved Space']
                if '%' in reserved:
                    reserved_space = int(reserved.replace('%', ''))
            except:
                pass
        
        # Determine health level based on factors (prioritize life remaining)
        if life_remaining is None:
            # No life data available
            status_text = "❓ Unknown"
            color = "gray"
            message = "Unable to determine SSD health"
        elif life_remaining >= 80:
            # Excellent: Brand new or lightly used
            if temperature and temperature > 60:
                status_text = "🟢 Excellent (but warm)"
                color = "green"
                message = f"Drive is in excellent condition. Temp: {temperature}°C"
            else:
                status_text = "🟢 Excellent"
                color = "green"
                message = "Drive is in excellent condition. Safe for wiping."
        elif life_remaining >= 50:
            # Good: Healthy drive
            if temperature and temperature > 70:
                status_text = "🟢 Good (hot)"
                color = "green"
                message = f"Drive is healthy but hot ({temperature}°C). Monitor temperature."
            elif error_count > 5:
                status_text = "🟢 Good (some errors)"
                color = "green"
                message = f"Drive is healthy but has {error_count} errors. Safe for wiping."
            else:
                status_text = "🟢 Good"
                color = "green"
                message = "Drive is healthy. Safe for wiping."
        elif life_remaining >= 30:
            # Fair: Aging but usable
            if temperature and temperature > 70:
                status_text = "🟡 Fair (hot)"
                color = "orange"
                message = f"Drive is aging and hot ({temperature}°C). Wiping will add wear."
            elif error_count > 10:
                status_text = "🟡 Fair (errors)"
                color = "orange"
                message = f"Drive is aging with {error_count} errors. Wiping will add wear."
            else:
                status_text = "🟡 Fair"
                color = "orange"
                message = f"Drive is aging ({life_remaining}% life left). Wiping will add wear."
        elif life_remaining >= 15:
            # Warning: Worn drive, not recommended
            status_text = "🟠 Warning"
            color = "#ff6600"  # Dark orange
            message = f"⚠️ Drive is worn ({life_remaining}% life left). Wiping NOT recommended."
        else:
            # Critical: Very worn, DO NOT WIPE
            status_text = "🔴 Critical"
            color = "red"
            message = f"🛑 Critical: Don't wipe this drive! Only {life_remaining}% life left. Risk of failure."
        
        # Add temperature warning for critical temps regardless of life
        if temperature and temperature > 80:
            status_text = "🔴 Critical"
            color = "red"
            message = f"🛑 Critical temperature: {temperature}°C! Don't wipe this drive."
        
        # Display the assessment
        self.assessment_label.set_markup(
            f"<b>SSD Status:</b> <span foreground='{color}'>{status_text}</span>\n"
            f"<span foreground='{color}'><small>{message}</small></span>"
        )
    
    def show_error(self, error_msg):
        """Show error message in health panel"""
        self.health_data_box.remove(self.loading_label)
        error_label = Gtk.Label(label=f"Error: {error_msg}")
        error_label.set_markup(f"<span foreground='red'>Error: {error_msg}</span>")
        self.health_data_box.pack_start(error_label, True, True, 0)
        self.show_all()


class MFTScanProgressDialog(Gtk.Window):
    """Progress dialog for MFT scanning operations"""
    def __init__(self, parent_window, device_path):
        super().__init__(type=Gtk.WindowType.TOPLEVEL)
        self.set_transient_for(parent_window)
        self.set_modal(True)
        self.set_keep_above(True)
        self.set_default_size(450, 200)
        self.set_border_width(15)
        self.set_resizable(False)
        self.set_title("MFT Analysis in Progress")

        # Connect close signal
        self.connect("delete-event", self.on_cancel_clicked)

        # Main container
        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=15)
        self.add(vbox)

        # Title
        title_label = Gtk.Label()
        title_label.set_markup("<b>Analyzing MFT Metadata...</b>")
        title_label.set_halign(Gtk.Align.START)
        vbox.pack_start(title_label, False, False, 0)

        # Status label
        self.status_label = Gtk.Label()
        self.status_label.set_markup(f"<b>Device:</b> {device_path}")
        self.status_label.set_halign(Gtk.Align.START)
        self.status_label.set_line_wrap(True)
        vbox.pack_start(self.status_label, False, False, 0)

        # Progress indicator (spinner)
        spinner_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        self.spinner = Gtk.Spinner()
        self.spinner.start()
        spinner_box.pack_start(self.spinner, False, False, 0)

        self.progress_label = Gtk.Label()
        self.progress_label.set_markup("<i>This may take several minutes for large drives...</i>")
        self.progress_label.set_halign(Gtk.Align.START)
        spinner_box.pack_start(self.progress_label, False, False, 0)
        vbox.pack_start(spinner_box, False, False, 0)

        # Spacer
        vbox.pack_start(Gtk.Label(), True, True, 0)

        # Cancel button
        button_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        cancel_button = Gtk.Button(label="Cancel Scan")
        cancel_button.connect("clicked", self.on_cancel_clicked)
        button_box.pack_end(cancel_button, False, False, 0)
        vbox.pack_start(button_box, False, False, 0)

        self.show_all()

    def update_status(self, message):
        """Update the status message"""
        GLib.idle_add(lambda: self.status_label.set_markup(message) if self.status_label else False)

    def update_progress(self, message):
        """Update the progress message"""
        GLib.idle_add(lambda: self.progress_label.set_markup(message) if self.progress_label else False)

    def on_cancel_clicked(self, widget, event=None):
        """Handle cancel button or window close"""
        self.destroy()
        return True


class FreeSpaceWipeWindow(Gtk.Window):
    def __init__(self):
        super().__init__(title="Barones Free Space Cleaner")
        self.set_default_size(340, 300)  # Reduced width from 450 to 340
        self.set_border_width(10)
        self.set_resizable(False)
        
        # Connect destroy signal to cleanup
        self.connect("destroy", self.on_window_close)
        
        # Store drive info
        self.drives = []
        self.wiping = False
        self.paused = False
        self.cancelled = False
        self.wipe_thread = None
        self.current_drive_index = -1
        self.health_panel = None  # Track health panel window

        # MFT scanning background thread infrastructure
        self.mft_scan_thread = None
        self.mft_scan_cancel = False
        self.mft_scan_progress_dialog = None
        self.mft_scan_cache = {}  # Cache MFT scan results by device path
        self.mft_scan_cancel_button = None
        
        # Main vertical box
        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        self.add(vbox)
        
        # Drives section
        drives_label = Gtk.Label(label="Drives:", xalign=0)
        vbox.pack_start(drives_label, False, False, 0)
        
        # Drives dropdown with health button
        drives_hbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=5)
        self.drives_combo = Gtk.ComboBoxText()
        self.drives_combo.connect("changed", self.on_drive_selection_changed)
        self.populate_drives()
        drives_hbox.pack_start(self.drives_combo, True, True, 0)
        
        self.health_button = Gtk.Button(label="Drive Health")
        self.health_button.connect("clicked", self.on_health_clicked)
        drives_hbox.pack_start(self.health_button, False, False, 0)
        
        vbox.pack_start(drives_hbox, False, False, 0)
        
        # Rate and time info
        self.info_label = Gtk.Label(label="Rate: 0 MB/sec  Est Time Remaining: --", xalign=0)
        vbox.pack_start(self.info_label, False, False, 5)
        
        # Progress bar
        self.progress_bar = Gtk.ProgressBar()
        vbox.pack_start(self.progress_bar, False, False, 0)
        
        # Wipe Type section
        wipe_type_label = Gtk.Label(label="Wipe Type", xalign=0)
        vbox.pack_start(wipe_type_label, False, False, 10)
        
        # Wipe Type section with integrated MFT button - positioned to stand out
        wipe_type_container = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=20)
        
        # Radio buttons for wipe type in two columns
        radio_hbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=15)
        radio_col1 = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)
        radio_col2 = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)
        
        self.radio_zeros = Gtk.RadioButton.new_with_label_from_widget(None, "All 0's (zeros)")
        self.radio_random = Gtk.RadioButton.new_with_label_from_widget(self.radio_zeros, "Random data")
        self.radio_ones = Gtk.RadioButton.new_with_label_from_widget(self.radio_zeros, "All 1's")
        self.radio_3487 = Gtk.RadioButton.new_with_label_from_widget(self.radio_zeros, "3487 pattern")
        
        radio_col1.pack_start(self.radio_zeros, False, False, 0)
        radio_col1.pack_start(self.radio_random, False, False, 0)
        radio_col2.pack_start(self.radio_ones, False, False, 0)
        radio_col2.pack_start(self.radio_3487, False, False, 0)
        
        radio_hbox.pack_start(radio_col1, False, False, 0)
        radio_hbox.pack_start(radio_col2, False, False, 0)
        wipe_type_container.pack_start(radio_hbox, False, False, 0)
        
        # MFT Clean button - positioned directly to the right of radio buttons (like a third column)
        self.mft_clean_button = Gtk.Button(label="MFT Clean")
        self.mft_clean_button.set_size_request(130, 35)  # Make it prominent
        
        # Style it to stand out with orange color
        self.mft_clean_button.get_style_context().add_class("suggested-action")
        
        # Create custom tooltip window for hover effect
        self.mft_tooltip_window = None
        self.mft_tooltip_label = None
        self.setup_mft_tooltip()
        
        self.mft_clean_button.connect("enter-notify-event", self.on_mft_button_hover)
        self.mft_clean_button.connect("leave-notify-event", self.on_mft_button_leave)
        self.mft_clean_button.connect("clicked", self.on_mft_clean_clicked)
        
        # Pack it directly after the radio buttons (like a third column)
        radio_hbox.pack_start(self.mft_clean_button, False, False, 25)
        
        vbox.pack_start(wipe_type_container, False, False, 10)
        
        # Checkboxes
        hbox_checks = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=20)
        self.check_start_again = Gtk.CheckButton(label="Start again when finished")
        self.check_cycle_wipe = Gtk.CheckButton(label="Cycle wipe type on start again")
        self.check_start_again.connect("toggled", self.on_start_again_toggled)
        hbox_checks.pack_start(self.check_start_again, False, False, 0)
        hbox_checks.pack_start(self.check_cycle_wipe, False, False, 0)
        vbox.pack_start(hbox_checks, False, False, 10)
        
        # Buttons at bottom
        hbox_buttons = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        hbox_buttons.set_homogeneous(True)
        
        self.start_button = Gtk.Button(label="Start")
        self.pause_button = Gtk.Button(label="Pause")
        self.cancel_button = Gtk.Button(label="Cancel")
        
        self.start_button.connect("clicked", self.on_start_clicked)
        self.pause_button.connect("clicked", self.on_pause_clicked)
        self.cancel_button.connect("clicked", self.on_cancel_clicked)
        
        self.pause_button.set_sensitive(False)
        
        hbox_buttons.pack_start(self.start_button, True, True, 0)
        hbox_buttons.pack_start(self.pause_button, True, True, 0)
        hbox_buttons.pack_start(self.cancel_button, True, True, 0)
        hbox_buttons.pack_start(self.mft_clean_button, True, True, 0)
        
        vbox.pack_end(hbox_buttons, False, False, 0)
    
    def on_window_close(self, widget):
        """Stop wiping when window closes"""
        if self.wiping:
            self.cancelled = True
            self.wiping = False
            # Give thread a moment to finish cleanup
            if self.wipe_thread and self.wipe_thread.is_alive():
                self.wipe_thread.join(timeout=2.0)
        
        # Close health panel if open
        if self.health_panel:
            self.health_panel.destroy()
            self.health_panel = None
    
    def on_health_clicked(self, button):
        """Show focused drive health panel instead of full smartctl output"""
        active = self.drives_combo.get_active()
        if active < 0 or active >= len(self.drives):
            return
        
        drive_info = self.drives[active]
        
        # Close existing health panel if open
        if self.health_panel:
            self.health_panel.destroy()
            self.health_panel = None
        
        # Create and show new health panel
        self.health_panel = HealthPanelWindow(self, drive_info)
        self.health_panel.show_all()
    
    def _get_physical_device(self, device_name):
        """Get the physical disk device, tracing through LUKS/dm and removing partition numbers"""
        # Get the base device
        base_device = self._get_base_device(device_name)
        
        # Handle dm-X (device mapper, including LUKS)
        if base_device.startswith('dm-') or device_name.startswith('luks-'):
            try:
                if base_device.startswith('dm-'):
                    dm_path = f"/sys/block/{base_device}/slaves"
                else:
                    # For luks- names, find the dm device
                    for dm in os.listdir('/sys/block'):
                        if dm.startswith('dm-'):
                            dm_name_path = f"/sys/block/{dm}/dm/name"
                            if os.path.exists(dm_name_path):
                                with open(dm_name_path, 'r') as f:
                                    dm_name = f.read().strip()
                                    if device_name in dm_name:
                                        dm_path = f"/sys/block/{dm}/slaves"
                                        break
                    else:
                        dm_path = None
                
                if dm_path and os.path.exists(dm_path):
                    # Get the first (usually only) slave device
                    slaves = os.listdir(dm_path)
                    if slaves:
                        underlying_device = slaves[0]
                        # Recursively trace and get base device
                        result = self._get_physical_device(underlying_device)
                        base_device = self._get_base_device(result)
            except (IOError, OSError):
                pass
        
        # Return the base device (disk, not partition)
        return base_device
    
    def _show_health_dialog(self, drive_info, smart_output):
        """Display drive health information in a dialog"""
        dialog = Gtk.Dialog(
            title=f"Drive Health - {drive_info['name']}",
            transient_for=self,
            flags=0
        )
        dialog.set_default_size(600, 400)
        
        # Add close button
        dialog.add_button("Close", Gtk.ResponseType.CLOSE)
        
        # Create scrolled window for text
        scrolled = Gtk.ScrolledWindow()
        scrolled.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        
        # Create text view
        textview = Gtk.TextView()
        textview.set_editable(False)
        textview.set_monospace(True)
        textview.get_buffer().set_text(smart_output)
        
        scrolled.add(textview)
        
        box = dialog.get_content_area()
        box.pack_start(scrolled, True, True, 0)
        
        dialog.show_all()
        dialog.run()
        dialog.destroy()
    
    def on_start_again_toggled(self, checkbox):
        if checkbox.get_active():
            dialog = Gtk.MessageDialog(
                transient_for=self,
                flags=0,
                message_type=Gtk.MessageType.WARNING,
                buttons=Gtk.ButtonsType.OK,
                text="SSD Wear Warning"
            )
            dialog.format_secondary_text(
                "Repeatedly wiping free space will add wear to SSDs. "
                "One pass is safe, but continuous wiping may reduce drive lifespan. "
                "Use this feature sparingly on SSDs."
            )
            dialog.run()
            dialog.destroy()
    
    def populate_drives(self):
        """Scan for mounted filesystems and populate the dropdown"""
        self.drives.clear()
        self.drives_combo.remove_all()
        
        # Use lsblk to get block devices with mount points and filesystem type
        try:
            result = subprocess.run(
                ['lsblk', '-J', '-o', 'NAME,MOUNTPOINT,SIZE,FSTYPE'],
                capture_output=True,
                text=True
            )
            data = json.loads(result.stdout)
        except:
            self.drives_combo.append_text("Error detecting drives")
            self.drives_combo.set_active(0)
            return
        
        # Find root device for /home lookup
        root_device = None
        for device in data.get('blockdevices', []):
            root_device = self._find_root_device(device)
            if root_device:
                break
        
        # Parse block devices
        for device in data.get('blockdevices', []):
            self._scan_device(device)
        
        # Add /home if it's not separately mounted but exists
        if os.path.exists('/home') and not any(d['mount_point'] == '/home' for d in self.drives):
            try:
                usage = shutil.disk_usage('/home')
                free_gb = usage.free / (1024**3)
                device_name = root_device if root_device else 'unknown'
                drive_type = self._get_drive_type(device_name) if root_device else 'Unknown'
                display_name = f"/home ({device_name} - {drive_type}) - {free_gb:.1f} GB free"
                
                self.drives.append({
                    'mount_point': '/home',
                    'free': usage.free,
                    'total': usage.total,
                    'name': device_name,
                    'type': drive_type
                })
                self.drives_combo.append_text(display_name)
            except (PermissionError, OSError):
                pass
        
        if len(self.drives) > 0:
            self.drives_combo.set_active(0)
        else:
            self.drives_combo.append_text("No drives detected")
            self.drives_combo.set_active(0)
    
    def _find_root_device(self, device):
        """Find the device name that has / mounted and trace to physical device"""
        # Check if this device has root mountpoint
        if device.get('mountpoint') == '/':
            device_name = device.get('name', 'unknown')
            # Trace through LUKS/dm to get physical device
            physical_device = self._get_physical_device(device_name)
            return physical_device
        
        # Special handling for LUKS devices - check if this is a LUKS container that might contain root
        if device.get('fstype') == 'crypto_LUKS':
            device_name = device.get('name', 'unknown')
            # Check if any of its children have root or if it's the main system LUKS
            for child in device.get('children', []):
                if child.get('mountpoint') and child.get('mountpoint') != '[SWAP]':
                    # This LUKS device has mounted children, likely the root filesystem
                    physical_device = self._get_physical_device(device_name)
                    return physical_device
        
        # Recursively check children
        for child in device.get('children', []):
            result = self._find_root_device(child)
            if result:
                return result
        return None
    
    def _scan_device(self, device):
        """Recursively scan device and its children for mountpoints"""
        mount_point = device.get('mountpoint')
        fstype = device.get('fstype', 'unknown')
        
        # Only include /home, /mnt, /media, and /run/media mount points
        if mount_point and (mount_point.startswith('/home') or
                           mount_point.startswith('/mnt') or
                           mount_point.startswith('/media') or
                           mount_point.startswith('/run/media')):
            # Get free space
            try:
                usage = shutil.disk_usage(mount_point)
                free_gb = usage.free / (1024**3)
                total_gb = usage.total / (1024**3)
                
                # Determine drive type
                device_name = device.get('name', 'unknown')
                drive_type = self._get_drive_type(device_name)
                
                # Create display string with drive type and filesystem
                fs_display = f"NTFS" if fstype and 'ntfs' in fstype.lower() else fstype.upper() if fstype else "Unknown"
                display_name = f"{mount_point} ({device_name} - {drive_type} - {fs_display}) - {free_gb:.1f} GB free"
                
                self.drives.append({
                    'mount_point': mount_point,
                    'free': usage.free,
                    'total': usage.total,
                    'name': device_name,
                    'type': drive_type,
                    'fstype': fstype
                })
                self.drives_combo.append_text(display_name)
            except (PermissionError, OSError):
                pass
        
        # Check children (partitions)
        for child in device.get('children', []):
            self._scan_device(child)
    
    def _get_base_device(self, device_name):
        """Get base device name, handling NVMe and regular drives differently"""
        # Don't modify dm-X or luks- devices
        if device_name.startswith('dm-') or device_name.startswith('luks-'):
            return device_name
        
        # NVMe devices: nvme0n1p2 -> nvme0n1, or nvme0n1 -> nvme0n1 (already base)
        if 'nvme' in device_name:
            if 'p' in device_name:
                # This is a partition: nvme0n1p2 -> nvme0n1
                parts = device_name.split('p')
                if len(parts) > 1 and parts[-1].isdigit():
                    return 'p'.join(parts[:-1])
            else:
                # This is already the base device: nvme0n1 -> nvme0n1
                return device_name
        
        # Regular devices: sda1 -> sda
        base = ''.join(c for c in device_name if not c.isdigit())
        return base.rstrip('p') if not base.endswith('p') else base[:-1]
    
    def _get_drive_type(self, device_name):
        """Determine if drive is SSD, HDD, or USB"""
        # Get the base device
        base_device = self._get_base_device(device_name)
        
        # Check if NVMe (always SSD)
        if 'nvme' in base_device:
            return 'SSD'
        
        # Handle dm-X (device mapper, including LUKS)
        if base_device.startswith('dm-') or device_name.startswith('luks-'):
            # Try to find the underlying device
            try:
                dm_path = None
                if base_device.startswith('dm-'):
                    dm_path = f"/sys/block/{base_device}/slaves"
                else:
                    # For luks- names, find the dm device
                    for dm in os.listdir('/sys/block'):
                        if dm.startswith('dm-'):
                            dm_name_path = f"/sys/block/{dm}/dm/name"
                            if os.path.exists(dm_name_path):
                                with open(dm_name_path, 'r') as f:
                                    dm_name = f.read().strip()
                                    if dm_name == device_name:
                                        dm_path = f"/sys/block/{dm}/slaves"
                                        break
                
                if dm_path and os.path.exists(dm_path):
                    # Get the first (usually only) slave device
                    slaves = os.listdir(dm_path)
                    if slaves:
                        underlying_device = slaves[0]
                        # Recursively check the underlying device
                        return self._get_drive_type(underlying_device)
            except (IOError, OSError) as e:
                print(f"Error tracing device {device_name}: {e}")
                pass
        
        # Check if USB
        try:
            device_path = f"/sys/block/{base_device}"
            if os.path.exists(device_path):
                # Check if USB by looking at the device path
                real_path = os.path.realpath(device_path)
                if 'usb' in real_path.lower():
                    # Check if rotational for USB HDD vs USB SSD
                    rotational_path = f"{device_path}/queue/rotational"
                    if os.path.exists(rotational_path):
                        with open(rotational_path, 'r') as f:
                            is_rotational = f.read().strip() == '1'
                            return 'USB HDD' if is_rotational else 'USB SSD'
                    return 'USB'
                
                # Check if rotational (HDD vs SSD)
                rotational_path = f"{device_path}/queue/rotational"
                if os.path.exists(rotational_path):
                    with open(rotational_path, 'r') as f:
                        is_rotational = f.read().strip() == '1'
                        return 'HDD' if is_rotational else 'SSD'
        except (IOError, OSError):
            pass
        
        return 'Unknown'
    
    def on_start_clicked(self, button):
        if self.wiping:
            return
        
        # Get selected drive
        active = self.drives_combo.get_active()
        if active < 0 or active >= len(self.drives):
            return
        
        self.current_drive_index = active
        drive_info = self.drives[active]
        
        # Get selected wipe method
        if self.radio_zeros.get_active():
            wipe_method = "zeros"
        elif self.radio_random.get_active():
            wipe_method = "random"
        elif self.radio_ones.get_active():
            wipe_method = "ones"
        elif self.radio_3487.get_active():
            wipe_method = "3487"
        else:
            # MFT Clean Only - handle separately
            self._start_mft_clean_only(drive_info)
            return
        
        # Start wiping in a thread
        self.wiping = True
        self.paused = False
        self.cancelled = False
        self.start_button.set_sensitive(False)
        self.pause_button.set_sensitive(True)
        
        # Disable drive selection and wipe methods during operation
        self.drives_combo.set_sensitive(False)
        self.radio_zeros.set_sensitive(False)
        self.radio_random.set_sensitive(False)
        self.radio_ones.set_sensitive(False)
        self.radio_3487.set_sensitive(False)
        
        self.wipe_thread = threading.Thread(
            target=self._wipe_free_space,
            args=(drive_info, wipe_method)
        )
        self.wipe_thread.start()
    
    def on_pause_clicked(self, button):
        if self.paused:
            self.paused = False
            self.pause_button.set_label("Pause")
        else:
            self.paused = True
            self.pause_button.set_label("Resume")
    
    def setup_mft_tooltip(self):
        """Setup the custom tooltip window for MFT button"""
        self.mft_tooltip_window = Gtk.Window(type=Gtk.WindowType.POPUP)
        self.mft_tooltip_window.set_decorated(False)
        self.mft_tooltip_window.set_resizable(False)
        self.mft_tooltip_window.set_default_size(350, 120)
        
        # Create tooltip content
        tooltip_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)
        tooltip_box.set_border_width(10)
        
        title_label = Gtk.Label()
        title_label.set_markup("<b>MFT Metadata Cleaning</b>")
        title_label.set_xalign(0)
        
        # Store reference to status label for dynamic updates
        self.mft_status_label = Gtk.Label()
        self.mft_status_label.set_xalign(0)
        self.mft_status_label.set_line_wrap(True)
        self.mft_status_label.set_max_width_chars(45)
        
        desc_label = Gtk.Label(label="Clean filesystem metadata (MFT for NTFS, directory entries for exFAT) without wiping free space. This overwrites file system metadata that may contain names and other info of deleted files.")
        desc_label.set_xalign(0)
        desc_label.set_line_wrap(True)
        desc_label.set_max_width_chars(45)
        
        tooltip_box.pack_start(title_label, False, False, 0)
        tooltip_box.pack_start(self.mft_status_label, False, False, 0)
        tooltip_box.pack_start(desc_label, False, False, 0)
        
        self.mft_tooltip_window.add(tooltip_box)
        self.mft_tooltip_window.show_all()
        self.mft_tooltip_window.hide()
        
        # Initialize with default status
        self._update_mft_tooltip_status()

    def _update_mft_tooltip_status(self):
        """Update MFT tooltip with current drive's MFT status (background scan)"""
        if hasattr(self, 'mft_status_label') and self.mft_status_label:
            active = self.drives_combo.get_active()
            if active >= 0 and active < len(self.drives):
                drive_info = self.drives[active]
                mount_point = drive_info['mount_point']
                fstype = drive_info.get('fstype', '').upper()

                if 'NTFS' in fstype:
                    # Check cache first
                    if mount_point in self.mft_scan_cache:
                        self._update_tooltip_with_mft_info(self.mft_scan_cache[mount_point])
                    else:
                        # Start background scan with progress dialog
                        self._start_background_mft_scan(drive_info)
                elif 'EXFAT' in fstype:
                    self.mft_status_label.set_markup("<span foreground='blue'>exFAT directory cleaning</span>")
                else:
                    self.mft_status_label.set_markup("<span foreground='gray'>Metadata cleaning not supported</span>")
            else:
                self.mft_status_label.set_markup("<span foreground='gray'>No drive selected</span>")

    def _start_background_mft_scan(self, drive_info):
        """Start MFT scanning in background thread with progress dialog"""
        # Show initial scanning message
        if hasattr(self, 'mft_status_label') and self.mft_status_label:
            self.mft_status_label.set_markup("<span foreground='blue'><i>Scanning MFT...</i></span>")
        print(f"🔍 Starting MFT background scan for: {drive_info['mount_point']}")

        # Create and show progress dialog
        self.mft_scan_progress_dialog = MFTScanProgressDialog(self, drive_info['mount_point'])

        # Start background thread
        self.mft_scan_cancel = False
        self.mft_scan_thread = threading.Thread(
            target=self._mft_scan_thread_worker,
            args=(drive_info,)
        )
        self.mft_scan_thread.daemon = True
        self.mft_scan_thread.start()

    def _mft_scan_thread_worker(self, drive_info):
        """Worker thread for MFT scanning"""
        try:
            mount_point = drive_info['mount_point']

            # Update progress dialog
            if self.mft_scan_progress_dialog:
                self.mft_scan_progress_dialog.update_progress("<b>Reading basic MFT info...</b>")

            # Perform the actual MFT scan
            enhanced_mft_info = self._get_enhanced_mft_info(mount_point)

            # Cache the result
            self.mft_scan_cache[mount_point] = enhanced_mft_info

            # Update UI in main thread
            GLib.idle_add(self._finish_mft_scan, enhanced_mft_info)

        except Exception as e:
            print(f"MFT scan error: {e}")
            GLib.idle_add(self._finish_mft_scan_error)

    def _finish_mft_scan(self, enhanced_mft_info):
        """Called when MFT scan completes - update UI in main thread"""
        print(f"✅ MFT scan completed, received info: {enhanced_mft_info}")

        # Close progress dialog if still open
        if self.mft_scan_progress_dialog:
            try:
                self.mft_scan_progress_dialog.destroy()
            except:
                pass
            self.mft_scan_progress_dialog = None

        # Update tooltip with results
        if enhanced_mft_info and hasattr(self, 'mft_status_label') and self.mft_status_label:
            self._update_tooltip_with_mft_info(enhanced_mft_info)
            print(f"✅ Updated tooltip with MFT info")
        else:
            if hasattr(self, 'mft_status_label') and self.mft_status_label:
                self.mft_status_label.set_markup("<span foreground='gray'>MFT info unavailable</span>")
                print(f"⚠️ No MFT info available")
        return False  # Don't repeat this callback

    def _finish_mft_scan_error(self):
        """Called when MFT scan errors - update UI"""
        if self.mft_scan_progress_dialog:
            try:
                self.mft_scan_progress_dialog.destroy()
            except:
                pass
            self.mft_scan_progress_dialog = None

        if hasattr(self, 'mft_status_label') and self.mft_status_label:
            self.mft_status_label.set_markup("<span foreground='red'>Scan failed</span>")
            print(f"❌ MFT scan failed")
        return False

    def _update_tooltip_with_mft_info(self, mft_info):
        """Update tooltip label with MFT information"""
        if not hasattr(self, 'mft_status_label') or not self.mft_status_label:
            print("⚠️ mft_status_label not found")
            return False

        if not mft_info or mft_info['total_entries'] == 0:
            markup = "<span foreground='gray'>MFT info unavailable</span>"
            self.mft_status_label.set_markup(markup)
            print(f"📝 Set label: MFT info unavailable")
            return False

        # Get counts
        total = mft_info['total_entries']
        free_entries = mft_info.get('used_entries', 0)  # Free MFT entries (IN_USE flag cleared)

        # Calculate free entry percentage
        free_percentage = (free_entries / total * 100) if total > 0 else 0

        # Color coding based on free entries needing cleanup
        if free_entries == 0:
            color = "green"
            status = "Clean"
        elif free_percentage < 0.5:  # Less than 0.5% free entries
            color = "green"
            status = "Good"
        elif free_percentage < 1.0:  # Less than 1% free entries
            color = "yellow"
            status = "Fair"
        elif free_percentage < 2.0:  # Less than 2% free entries
            color = "orange"
            status = "Needs Cleanup"
        else:
            color = "red"
            status = "Heavily Fragmented"

        status_text = f"<span foreground='{color}'><b>MFT Status: {status}</b></span>\n"
        status_text += f"<span foreground='{color}'>Free MFT entries: {free_entries:,} ({free_percentage:.2f}%) ← Wipe target</span>"

        self.mft_status_label.set_markup(status_text)
        print(f"📝 MFT Status: {status}")
        print(f"   Total MFT slots: {total:,}")
        print(f"   Free entries (cleared IN_USE flag): {free_entries:,} ({free_percentage:.2f}%) ← These need wiping")
        return False
    
    def on_mft_button_hover(self, widget, event):
        """Show tooltip when mouse hovers over MFT button"""
        if self.mft_tooltip_window:
            # Get button position
            button_x, button_y = widget.get_window().get_origin()[1:]
            button_alloc = widget.get_allocation()
            
            # Position tooltip above button
            tooltip_x = button_x + button_alloc.x + 10
            tooltip_y = button_y + button_alloc.y - 90  # 90px above button
            
            self.mft_tooltip_window.move(tooltip_x, tooltip_y)
            self.mft_tooltip_window.show()
    
    def on_mft_button_leave(self, widget, event):
        """Hide tooltip when mouse leaves MFT button"""
        if self.mft_tooltip_window:
            self.mft_tooltip_window.hide()
    
    def _start_mft_clean_only(self, drive_info):
        """Start MFT cleaning only (called from Start button when MFT option selected)"""
        # Start MFT cleaning in a thread (no free space wipe)
        self.wiping = True
        self.paused = False
        self.cancelled = False
        self.start_button.set_sensitive(False)
        self.mft_clean_button.set_sensitive(False)
        self.pause_button.set_sensitive(True)
        
        # Disable drive selection and wipe methods during operation
        self.drives_combo.set_sensitive(False)
        self.radio_zeros.set_sensitive(False)
        self.radio_random.set_sensitive(False)
        self.radio_ones.set_sensitive(False)
        self.radio_3487.set_sensitive(False)
        
        self.wipe_thread = threading.Thread(
            target=self._clean_metadata_only,
            args=(drive_info,)
        )
        self.wipe_thread.start()
    
    def on_cancel_clicked(self, button):
        if self.wiping:
            self.cancelled = True
            self.wiping = False
    
    def on_mft_clean_clicked(self, button):
        """Handle MFT clean only button - clean metadata without free space wipe"""
        if self.wiping:
            return
        
        # Get selected drive
        active = self.drives_combo.get_active()
        if active < 0 or active >= len(self.drives):
            return
        
        drive_info = self.drives[active]
        
        # Start MFT cleaning in a thread (no free space wipe)
        self.wiping = True
        self.paused = False
        self.cancelled = False
        self.start_button.set_sensitive(False)
        self.mft_clean_button.set_sensitive(False)
        self.pause_button.set_sensitive(True)
        
        # Disable drive selection during operation
        self.drives_combo.set_sensitive(False)
        
        self.wipe_thread = threading.Thread(
            target=self._clean_metadata_only,
            args=(drive_info,)
        )
        self.wipe_thread.start()
    
    def _get_mft_info_sleuthkit(self, device_path):
        """Get MFT information using Sleuth Kit if available"""
        try:
            # Try to get device path from mount point
            result = subprocess.run(['df', device_path], capture_output=True, text=True)
            if result.returncode == 0:
                lines = result.stdout.strip().split('\n')
                if len(lines) >= 2:
                    device_line = lines[1].split()
                    if len(device_line) >= 1:
                        raw_device = device_line[0]
                        print(f"📍 Found device: {raw_device}")

                        # Use fsstat to get MFT information (assumes script runs with sudo)
                        try:
                            print(f"🔍 Running: fsstat -f ntfs {raw_device}")
                            fsstat_result = subprocess.run(
                                ['fsstat', '-f', 'ntfs', raw_device],
                                capture_output=True, text=True, timeout=30
                            )

                            if fsstat_result.returncode == 0:
                                # Parse fsstat output for MFT info
                                mft_info = {}
                                print(f"📊 fsstat output (first 2000 chars):\n{fsstat_result.stdout[:2000]}")

                                for line in fsstat_result.stdout.split('\n'):
                                    if 'Size of MFT Entries' in line:
                                        try:
                                            # Parse "Size of MFT Entries: 1024 bytes"
                                            size_str = line.split(':')[1].strip().split()[0]
                                            mft_info['entry_size'] = int(size_str)
                                            print(f"   ✓ MFT Entry size: {mft_info['entry_size']} bytes")
                                        except Exception as e:
                                            print(f"   ✗ Error parsing entry size: {e}")
                                    elif line.strip().startswith('Range:') and 'Total' not in line:
                                        try:
                                            # Parse "Range: 0 - 453444" to get total MFT entries
                                            # Only matches "Range:" lines, NOT "Total Cluster Range" or "Total Sector Range"
                                            parts = line.split('-')
                                            if len(parts) >= 2:
                                                max_entry = int(parts[-1].strip())
                                                mft_info['total_entries'] = max_entry + 1  # Range is 0-indexed, so add 1
                                                print(f"   ✓ Total MFT entries: {mft_info['total_entries']:,} (range 0-{max_entry})")
                                        except Exception as e:
                                            print(f"   ✗ Error parsing MFT range: {line} - {e}")

                                if 'total_entries' not in mft_info or mft_info['total_entries'] == 0:
                                    print(f"⚠️ fsstat did not provide total_entries. Full output:\n{fsstat_result.stdout}")

                                return mft_info
                            else:
                                print(f"❌ fsstat failed with code {fsstat_result.returncode}: {fsstat_result.stderr}")
                        except subprocess.TimeoutExpired:
                            print("⏱️ fsstat timed out")
                        except Exception as e:
                            print(f"❌ fsstat error: {e}")
        except Exception as e:
            print(f"❌ Sleuth Kit detection error: {e}")
        return {}

    def _get_enhanced_mft_info(self, device_path):
        """Get comprehensive MFT information including free entries"""
        mft_info = {
            'total_entries': 0,
            'used_entries': 0,  # This is now "deleted_entries"
            'allocated_entries': 0,  # Active files in MFT
            'free_entries': 0,
            'mft_zone_size': 0,
            'entry_size': 1024,
            'used_percentage': 0,
            'fragmentation_level': 'Unknown'
        }
        
        # 1. Get basic MFT info (existing method)
        basic_info = self._get_mft_info_sleuthkit(device_path)
        if basic_info and 'total_entries' in basic_info:
            mft_info['total_entries'] = basic_info['total_entries']
            mft_info['entry_size'] = basic_info.get('entry_size', 1024)
        
        # 2. Count used entries via fls (file listing)
        try:
            # Try to get device path from mount point
            result = subprocess.run(['df', device_path], capture_output=True, text=True)
            if result.returncode == 0:
                lines = result.stdout.strip().split('\n')
                if len(lines) >= 2:
                    device_line = lines[1].split()
                    if len(device_line) >= 1:
                        raw_device = device_line[0]
                        
                        # Use fls to count used MFT entries (assumes script runs with sudo)
                        # INCREASED TIMEOUT: 30s → 120s (2 min) for large/external drives
                        try:
                            # Update progress dialog
                            if self.mft_scan_progress_dialog:
                                self.mft_scan_progress_dialog.update_progress("<b>Scanning file entries...</b>\n<i>This may take several minutes...</i>")

                            print(f"📊 Scanning FREE MFT entries on {raw_device}... (timeout: 2 minutes)")
                            print(f"   Using: fls -f ntfs -d -r (finds unallocated/free MFT entries only)")

                            # Use -d flag to find ONLY deleted/free MFT entries
                            # These are entries with IN_USE flag CLEARED but still contain deleted file metadata
                            # This is what needs to be wiped to remove traces of deleted files
                            fls_result = subprocess.run(
                                ['fls', '-f', 'ntfs', '-d', '-r', raw_device],
                                capture_output=True, text=True, timeout=120
                            )
                            if fls_result.returncode == 0:
                                # Count free MFT entries
                                free_mft_entries = 0

                                for line in fls_result.stdout.split('\n'):
                                    if line.strip():
                                        free_mft_entries += 1

                                # Free MFT entries = targets for wiping
                                mft_info['used_entries'] = free_mft_entries

                                print(f"📊 Free MFT Entries Found (IN_USE flag cleared):")
                                print(f"   Free/reusable entries: {free_mft_entries:,}")
                                print(f"   These entries still contain deleted file metadata that should be wiped")

                                # Update progress
                                if self.mft_scan_progress_dialog:
                                    self.mft_scan_progress_dialog.update_progress(f"<b>Found {free_mft_entries:,} free MFT entries</b>\n<i>Finalizing...</i>")
                            else:
                                print(f"fls failed: {fls_result.stderr}")
                                if self.mft_scan_progress_dialog:
                                    self.mft_scan_progress_dialog.update_progress("<b>fls command failed</b>")
                        except subprocess.TimeoutExpired:
                            print("⚠️ fls timed out after 2 minutes - skipping used entry detection")
                            print("   This usually happens with very large or slow drives (external/USB)")
                            if self.mft_scan_progress_dialog:
                                self.mft_scan_progress_dialog.update_progress("<b>⚠️ Scan timed out (2 min)</b>\n<i>Very large drive detected</i>")
                        except Exception as e:
                            print(f"fls error: {e}")
                            if self.mft_scan_progress_dialog:
                                self.mft_scan_progress_dialog.update_progress(f"<b>Error during scan:</b> {str(e)[:50]}")
        except Exception as e:
            print(f"Enhanced MFT detection error: {e}")
        
        # 3. Calculate percentages and meaningful "free_entries" for cleaning
        if mft_info['total_entries'] > 0:
            # With fls -d approach:
            # used_entries = FREE MFT entries (IN_USE flag cleared) = CLEANUP TARGETS
            # free_entries = same as used_entries (the entries that need wiping)
            free_mft_entries = mft_info['used_entries']
            mft_info['free_entries'] = free_mft_entries  # The entries that need wiping

            # Calculate percentages
            if free_mft_entries > 0:
                mft_info['used_percentage'] = (free_mft_entries / mft_info['total_entries']) * 100
            else:
                # Estimate if fls failed
                mft_info['used_entries'] = int(mft_info['total_entries'] * 0.3)
                mft_info['free_entries'] = mft_info['used_entries']
                mft_info['used_percentage'] = 30.0

        # 4. Determine fragmentation level based on deleted entries
        total = mft_info['total_entries']
        deleted = mft_info['used_entries']
        deleted_pct = (deleted / total * 100) if total > 0 else 0

        if deleted_pct < 5:
            mft_info['fragmentation_level'] = 'Low'
        elif deleted_pct < 15:
            mft_info['fragmentation_level'] = 'Moderate'
        elif deleted_pct < 30:
            mft_info['fragmentation_level'] = 'High'
        else:
            mft_info['fragmentation_level'] = 'Severe'
        
        # Log comprehensive MFT analysis
        if mft_info['total_entries'] > 0:
            total = mft_info['total_entries']
            free_entries = mft_info['used_entries']  # Free MFT entries (IN_USE flag cleared)
            free_pct = (free_entries / total * 100) if total > 0 else 0

            print(f"📋 MFT Analysis Summary:")
            print(f"   Total MFT slots: {total:,}")
            print(f"   Free entries found: {free_entries:,} ({free_pct:.2f}%)")
            print(f"   └─ These entries have IN_USE flag cleared")
            print(f"   └─ Still contain deleted file metadata that should be wiped")
            print(f"   Fragmentation Level: {mft_info['fragmentation_level']}")
        
        return mft_info
    
    def _clean_mft_metadata(self, mount_point, drive_info):
        """Clean MFT metadata by creating/deleting many files (Professional CCleaner method)"""
        import time
        start_time = time.time()
        print(f"Starting PROFESSIONAL MFT metadata cleaning at {time.strftime('%H:%M:%S')}...")
        
        # LIMITED RETRY: 5 attempts with random folder names, then popup
        import random
        import string
        
        temp_dir = None
        max_attempts = 5  # Exactly 5 attempts as requested
        attempt = 0
        
        while attempt < max_attempts and not self.cancelled:
            # Generate random folder name
            random_suffix = ''.join(random.choices(string.ascii_lowercase + string.digits, k=8))
            temp_dir = os.path.join(mount_point, f"MFT_{random_suffix}")
            
            try:
                os.makedirs(temp_dir, exist_ok=True)
                
                # CRITICAL: Verify the folder actually exists and is writable
                if os.path.exists(temp_dir) and os.path.isdir(temp_dir):
                    # Test write access by creating a small test file
                    test_file = os.path.join(temp_dir, "test_write.tmp")
                    try:
                        with open(test_file, 'w') as f:
                            f.write("test")
                        os.remove(test_file)  # Clean up
                        print(f"✅ SUCCESS: Created MFT cleaning folder on target drive: {temp_dir}")
                        print(f"✅ VERIFIED: Write access confirmed - folder is real and writable")
                        break  # Real success! Exit retry loop
                    except OSError as write_error:
                        print(f"❌ WRITE ACCESS FAILED: Cannot write to {temp_dir} - {write_error}")
                        print(f"❌ This means the folder exists but is not writable")
                        # Continue to next attempt
                        continue
                else:
                    print(f"❌ PHANTOM FOLDER BUG: {temp_dir} reported as created but doesn't exist!")
                    print(f"❌ This is a serious issue - the folder creation succeeded but folder is not real")
                    # Continue to next attempt - this is the bug you found
                    continue
                
            except OSError as e:
                attempt += 1
                print(f"⚠️ Attempt {attempt}/{max_attempts}: Cannot create {temp_dir} - {e}")
                
                # Brief pause between attempts
                time.sleep(0.2)
                
                if self.cancelled:
                    print("🛑 User cancelled - stopping MFT cleaning attempts")
                    return False
        
        # Check if we succeeded or need to show popup
        if temp_dir is None or not os.path.exists(temp_dir):
            print("❌ FAILED: Could not create MFT cleaning folder on target drive after 5 attempts")
            print("📋 This is expected for read-only or failing external drives")
            
            # Show popup dialog to user
            self._show_mft_failure_popup(mount_point)
            
            # Return False to skip MFT cleaning but continue with free space wipe
            return False
        
        try:
            # Get enhanced MFT info including free entries
            enhanced_mft_info = self._get_enhanced_mft_info(mount_point)
            target_files = None

            # FIRST CHOICE: Use enhanced MFT analysis with free entry detection
            if enhanced_mft_info and enhanced_mft_info['free_entries'] > 0:
                free_entries = enhanced_mft_info['free_entries']
                total_entries = enhanced_mft_info['total_entries']
                free_percentage = (free_entries / total_entries * 100) if total_entries > 0 else 0
                drive_type = drive_info.get('type', 'Unknown')

                # Simple: wipe 80% of free MFT entries, no safety factors
                target_percentage = 0.80
                target_files = int(free_entries * target_percentage)

                print(f"🎯 MFT Cleaning Target: 80% of free entries")
                print(f"   Free MFT entries found: {free_entries:,} ({free_percentage:.2f}% of total)")
                print(f"   Target to clean: {target_files:,} files (80% × {free_entries:,})")
                print(f"   Drive type: {drive_type}")

            # FALLBACK: Use basic MFT info if enhanced detection fails
            elif enhanced_mft_info and enhanced_mft_info['total_entries'] > 0:
                # Fallback to original method but with reduced limits
                total_mft_entries = enhanced_mft_info['total_entries']
                mft_based_count = int(total_mft_entries * 0.20)  # Reduced from 25%
                target_files = min(200000, max(50000, mft_based_count))  # Reduced limits
                print(f"⚠️ Enhanced MFT detection failed - using basic fallback: {total_mft_entries:,} total → {target_files:,} files (20%)")

            # FINAL FALLBACK: Use drive size if MFT info unavailable
            if target_files is None:
                try:
                    usage = shutil.disk_usage(mount_point)
                    drive_size_gb = usage.total / (1024**3)

                    # Conservative scaling based on drive size
                    if drive_size_gb < 100:  # Small drives (< 100GB)
                        target_files = 50000
                    elif drive_size_gb < 500:  # Medium drives (100-500GB)
                        target_files = 100000
                    elif drive_size_gb < 2000:  # Large drives (500GB-2TB)
                        target_files = 150000
                    else:  # Huge drives (2TB+)
                        target_files = 200000  # Fixed cap for safety

                    print(f"📏 Drive-size fallback: {drive_size_gb:.0f}GB → {target_files:,} files")

                except:
                    target_files = 75000  # Reduced absolute fallback
                    print(f"⚠️ Cannot calculate MFT files - using safe default: {target_files:,} files")
                
            # Phase 1: Create MFT-pressure files
            GLib.idle_add(self._update_info_label, f"MFT Cleaning: Creating {target_files:,} metadata files...")
            print(f"Phase 1: Creating {target_files:,} files...")
            
            files_created = []
            phase1_start = time.time()
            mft_entry_size = enhanced_mft_info.get('entry_size', 1024) if enhanced_mft_info else 1024  # Default 1KB
            last_update_time = phase1_start
            
            # CCLEANER-STYLE RATE LIMITING: Much slower like CCleaner does
            # Target: ~10-50 files/second (CCleaner approach) instead of 500+ files/second
            
            for i in range(target_files):
                # Check for cancellation
                if self.cancelled:
                    print("🛑 MFT cleaning cancelled by user - cleaning up files...")
                    break
                
                # Update progress bar every file for smooth animation - NOW WITH SPEED AND TIME!
                if i % 50 == 0:  # Update every 50 files for smoother progress
                    progress = i / target_files
                    elapsed = time.time() - phase1_start
                    rate = i / elapsed if elapsed > 0 else 0
                    
                    # Calculate estimated time remaining
                    remaining_files = target_files - i
                    time_remaining = remaining_files / rate if rate > 0 else 0
                    
                    # Format time remaining
                    hours = int(time_remaining / 3600)
                    mins = int((time_remaining % 3600) / 60)
                    secs = int(time_remaining % 60)
                    
                    if hours > 0:
                        time_str = f"{hours}h {mins}m {secs}s"
                    elif mins > 0:
                        time_str = f"{mins}m {secs}s"
                    else:
                        time_str = f"{secs}s"
                    
                    # Update both progress bar and label with speed and time info
                    GLib.idle_add(self.progress_bar.set_fraction, progress)
                    GLib.idle_add(self._update_info_label, f"MFT Cleaning: {i:,} files at {rate:.0f} files/sec  Est: {time_str}")
                
                # Create filename that maximizes MFT usage
                filename = f"ZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZ_MFT_CLEAN_PRO_{i:08d}_MAXIMUM_MFT_ENTRY_USAGE_FOR_BIG_DRIVES.ZZZ"
                filepath = os.path.join(temp_dir, filename)
                
                try:
                    # CCLEANER-STYLE RATE LIMITING: Much slower for all external drives
                    device_name = drive_info.get('name', 'unknown')
                    drive_type = self._get_drive_type(device_name)
                    is_external = 'USB' in drive_type.upper() or 'HDD' in drive_type.upper()
                    
                    if is_external:
                        # Target: 75 files/sec on USB drives
                        # Calculation: 50 files should take 50/75 = 0.667 seconds
                        if i % 50 == 0:  # Every 50 files
                            time.sleep(0.667)  # ~75 files/sec
                    
                    # Create content that matches MFT entry size
                    base_content = f"PRO_MFT_ENTRY_{i:08d}_PROFESSIONAL_CLEANING_"
                    padding_size = mft_entry_size - len(base_content) - 50
                    content = base_content + "X" * max(100, padding_size)
                    
                    with open(filepath, 'w') as f:
                        f.write(content)
                    files_created.append(filepath)
                    
                    # Progress update every 10k files with speed and time monitoring
                    if i % 10000 == 0 and i > 0:
                        elapsed = time.time() - phase1_start
                        rate = i / elapsed if elapsed > 0 else 0
                        target_rate = 600  # Target ~600 files/second (middle of 500-700 range)
                        
                        # Calculate estimated time remaining
                        remaining_files = target_files - i
                        time_remaining = remaining_files / rate if rate > 0 else 0
                        
                        # Format time remaining
                        hours = int(time_remaining / 3600)
                        mins = int((time_remaining % 3600) / 60)
                        secs = int(time_remaining % 60)
                        
                        if hours > 0:
                            time_str = f"{hours}h {mins}m {secs}s"
                        elif mins > 0:
                            time_str = f"{mins}m {secs}s"
                        else:
                            time_str = f"{secs}s"
                        
                        # Console output (for debugging)
                        print(f"PRO Created {i:,} files... ({rate:.0f} files/sec)")
                        
                        # UI Progress Bar Update - NOW INCLUDES FILES/SEC AND TIME!
                        progress = i / target_files
                        GLib.idle_add(self.progress_bar.set_fraction, progress)
                        GLib.idle_add(self._update_info_label, f"MFT Cleaning: {i:,} files at {rate:.0f} files/sec  Est: {time_str}")
                        
                        # Speed feedback in console
                        if rate > 1000:  # If going way too fast
                            print(f"⚠️ Speed too high: {rate:.0f} files/sec - target is ~{target_rate} files/sec")
                        elif rate < 400:  # If going too slow
                            print(f"⚠️ Speed too low: {rate:.0f} files/sec - target is ~{target_rate} files/sec")
                        else:
                            print(f"✅ Good speed: {rate:.0f} files/sec - target is ~{target_rate} files/sec")
                        
                except OSError as e:
                    if e.errno == 28:  # Disk full - this is actually good
                        print(f"PRO MFT pressure achieved after {i:,} files in {time.time() - phase1_start:.1f} seconds")
                        break
                    elif e.errno == 5:  # I/O error - external drive failing
                        print(f"❌ I/O error at file {i:,} - external drive cannot handle operations")
                        print("🚨 STOPPING MFT cleaning - drive is failing")
                        break  # Stop completely - drive is failing
                    else:
                        print(f"❌ File creation error: {e}")
                        # Try to continue with next file instead of crashing
                        continue
            
            phase1_time = time.time() - phase1_start
            print(f"✅ Phase 1 completed: {len(files_created):,} files created in {phase1_time:.1f} seconds")
            
        except Exception as e:
            print(f"MFT cleaning error: {e}")
            # Clean up files on error
            self._cleanup_mft_files(temp_dir, files_created)
            return False
        
        # CRITICAL: Always clean up files, especially if cancelled
        finally:
            if self.cancelled:
                print("🧹 MFT cleaning was cancelled - performing cleanup...")
                self._cleanup_mft_files(temp_dir, files_created)
            else:
                # Normal cleanup - use shutil.rmtree to handle any remaining content
                try:
                    if os.path.exists(temp_dir):
                        print(f"🧹 Cleaning up MFT cleaning directory: {temp_dir}")
                        shutil.rmtree(temp_dir)
                except Exception as e:
                    print(f"⚠️ Error removing MFT temp directory: {e}")
    
    def _show_mft_failure_popup(self, mount_point):
        """Show popup dialog when MFT cleaning fails"""
        dialog = Gtk.MessageDialog(
            transient_for=self,
            flags=0,
            message_type=Gtk.MessageType.INFO,
            buttons=Gtk.ButtonsType.OK,
            text="MFT Metadata Cleaning Unavailable"
        )
        dialog.format_secondary_text(
            f"Could not create MFT cleaning folder on {mount_point} after 5 attempts.\n\n"
            "This is normal for read-only or failing external drives.\n\n"
            "The tool will now proceed with regular free space wiping only.\n"
            "MFT metadata cleaning will be skipped for this drive."
        )
        
        dialog.set_default_size(400, 200)
        dialog.run()
        dialog.destroy()
    
    def _create_mft_file_with_usb_limiting(self, i, filepath, mft_entry_size, drive_info):
        """Create individual MFT file with rate limiting for external drives"""
        try:
            # Rate limiting for external HDDs: ~70 files/second
            device_name = drive_info.get('name', 'unknown')
            drive_type = self._get_drive_type(device_name)
            is_external = 'USB' in drive_type.upper() or 'HDD' in drive_type.upper()

            if is_external:
                # Target: 70 files/second for external HDDs
                # Sleep duration: 1 second / 70 files = ~0.0143 seconds per file
                target_rate = 70
                sleep_time = 1.0 / target_rate
                time.sleep(sleep_time)

                if i % 1000 == 0 and i > 0:  # Print every 1000 files
                    print(f"🐌 Rate-limited mode: ~{target_rate} files/sec for external drive at {i:,} files")
            
            # Create content that matches MFT entry size
            base_content = f"PRO_MFT_ENTRY_{i:08d}_PROFESSIONAL_CLEANING_"
            padding_size = mft_entry_size - len(base_content) - 50
            content = base_content + "X" * max(100, padding_size)
            
            # DEBUG: Verify file creation with more detail
            if i % 1000 == 0:  # Debug every 1000 files
                print(f"DEBUG: Creating file {i:,} at {filepath}")
            
            with open(filepath, 'w') as f:
                f.write(content)
            
            # DEBUG: Verify file was actually written
            if os.path.exists(filepath):
                file_size = os.path.getsize(filepath)
                if i % 1000 == 0:  # Debug every 1000 files
                    print(f"DEBUG: Successfully created file {i:,} - size: {file_size} bytes")
                return True
            else:
                print(f"❌ DEBUG: File {i,:} was not created despite no exception!")
                return False
                
        except OSError as e:
            if e.errno == 28:  # Disk full - this is actually good
                print(f"PRO MFT pressure achieved after {i:,} files")
                return False  # Signal to stop
            elif e.errno == 5:  # I/O error - external drive failing
                print(f"❌ I/O error at file {i:,} - external drive cannot handle operations")
                print("🚨 STOPPING MFT cleaning - drive is failing")
                return False  # Signal to stop
            else:
                print(f"❌ File creation error: {e}")
                return False  # Signal failure
            
        except Exception as e:
            print(f"MFT cleaning error: {e}")
            return False
    
    def _cleanup_mft_files(self, temp_dir, files_created):
        """Comprehensive cleanup of MFT cleaning files when cancelled or errored"""
        print(f"🧹 Starting MFT file cleanup in {temp_dir}...")
        
        # First, remove all the individual files we created
        files_removed = 0
        for filepath in files_created:
            try:
                if os.path.exists(filepath):
                    os.remove(filepath)
                    files_removed += 1
            except Exception as e:
                print(f"⚠️ Error removing file {filepath}: {e}")
        
        print(f"🧹 Removed {files_removed:,} MFT cleaning files")
        
        # Then remove any remaining files in the temp directory
        try:
            if os.path.exists(temp_dir):
                remaining_files = os.listdir(temp_dir)
                if remaining_files:
                    print(f"🧹 Found {len(remaining_files)} additional files to clean up")
                    for filename in remaining_files:
                        file_path = os.path.join(temp_dir, filename)
                        try:
                            if os.path.isfile(file_path):
                                os.remove(file_path)
                                files_removed += 1
                        except Exception as e:
                            print(f"⚠️ Error removing remaining file {filename}: {e}")
                
                # Finally, remove the temp directory itself
                try:
                    os.rmdir(temp_dir)
                    print(f"✅ Successfully removed MFT cleaning directory: {temp_dir}")
                except Exception as e:
                    print(f"⚠️ Error removing MFT temp directory: {e}")
        except Exception as e:
            print(f"⚠️ Error during MFT cleanup: {e}")
        
        print(f"✅ MFT cleanup completed - total files removed: {files_removed:,}")
    
    def _cleanup_exfat_files(self, temp_dir, files_to_remove):
        """Comprehensive cleanup of exFAT cleaning files when cancelled or errored"""
        print(f"🧹 Starting exFAT file cleanup in {temp_dir}...")
        
        # First, remove all the files we know we created
        files_removed = 0
        for filepath in files_to_remove:
            try:
                if os.path.exists(filepath):
                    os.remove(filepath)
                    files_removed += 1
            except Exception as e:
                print(f"⚠️ Error removing file {filepath}: {e}")
        
        print(f"🧹 Removed {files_removed:,} exFAT cleaning files")
        
        # Then remove any remaining files in the temp directory
        try:
            if os.path.exists(temp_dir):
                remaining_files = os.listdir(temp_dir)
                if remaining_files:
                    print(f"🧹 Found {len(remaining_files)} additional files to clean up")
                    for filename in remaining_files:
                        file_path = os.path.join(temp_dir, filename)
                        try:
                            if os.path.isfile(file_path):
                                os.remove(file_path)
                                files_removed += 1
                        except Exception as e:
                            print(f"⚠️ Error removing remaining file {filename}: {e}")
                
                # Finally, remove the temp directory itself
                try:
                    os.rmdir(temp_dir)
                    print(f"✅ Successfully removed exFAT cleaning directory: {temp_dir}")
                except Exception as e:
                    print(f"⚠️ Error removing exFAT temp directory: {e}")
        except Exception as e:
            print(f"⚠️ Error during exFAT cleanup: {e}")
        
        print(f"✅ exFAT cleanup completed - total files removed: {files_removed:,}")
    
    def _clean_exfat_metadata(self, mount_point):
        """Clean exFAT directory metadata by creating/deleting files with specific patterns"""
        import time
        start_time = time.time()
        print(f"Starting exFAT metadata cleaning at {time.strftime('%H:%M:%S')}...")
        
        temp_dir = os.path.join(mount_point, "EXFAT_Clean_Temp")
        os.makedirs(temp_dir, exist_ok=True)
        
        try:
            # exFAT uses different directory structure than NTFS
            # We'll create fewer files but with patterns that stress the directory entries
            
            print("exFAT Phase 1: Creating directory entry pressure...")
            GLib.idle_add(self._update_info_label, "exFAT Cleaning: Creating directory entries...")
            
            files_created = []
            phase1_start = time.time()
            
            # exFAT directory entries are more limited, so we use fewer files
            # but with longer names and different patterns to maximize directory space usage
            for i in range(10000):  # Fewer than NTFS but still effective
                # Check for cancellation
                if self.cancelled:
                    print("🛑 exFAT cleaning cancelled by user - cleaning up files...")
                    break
                
                # Use longer names to consume more directory entry space
                filename = f"ZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZ_EXFAT_DIR_{i:06d}_LONGNAME.ZZZ"
                filepath = os.path.join(temp_dir, filename)
                
                try:
                    # Create with some content to allocate clusters
                    with open(filepath, 'w') as f:
                        f.write("EXFAT" * 100)  # 500 bytes - enough to allocate a cluster
                    files_created.append(filepath)
                    
                    if i % 2000 == 0 and i > 0:
                        elapsed = time.time() - phase1_start
                        rate = i / elapsed if elapsed > 0 else 0
                        GLib.idle_add(self._update_info_label, f"exFAT Cleaning: Created {i} entries... ({rate:.0f} entries/sec)")
                        print(f"exFAT entries {i}... ({rate:.0f} entries/sec)")
                        
                except OSError as e:
                    if e.errno == 28:  # Disk full
                        print(f"exFAT directory pressure achieved after {i} entries")
                        break
                    else:
                        raise
            
            phase1_time = time.time() - phase1_start
            print(f"exFAT Phase 1 completed: {len(files_created)} entries in {phase1_time:.1f} seconds")
            
            # Phase 2: Delete to free directory entries
            phase2_start = time.time()
            GLib.idle_add(self._update_info_label, f"exFAT Cleaning: Deleting {len(files_created)} entries...")
            print(f"exFAT Phase 2: Deleting {len(files_created)} entries...")
            
            for i, filepath in enumerate(files_created):
                try:
                    os.remove(filepath)
                    if i % 2000 == 0 and i > 0:
                        elapsed = time.time() - phase2_start
                        rate = i / elapsed if elapsed > 0 else 0
                        GLib.idle_add(self._update_info_label, f"exFAT Cleaning: Deleted {i} entries... ({rate:.0f} entries/sec)")
                        print(f"exFAT deleted {i}... ({rate:.0f} entries/sec)")
                except OSError:
                    pass
            
            phase2_time = time.time() - phase2_start
            print(f"exFAT Phase 2 completed: {len(files_created)} entries deleted in {phase2_time:.1f} seconds")
            
            # Phase 3: Create final entries to overwrite freed directory space
            phase3_start = time.time()
            GLib.idle_add(self._update_info_label, "exFAT Cleaning: Final directory overwrite...")
            print("exFAT Phase 3: Creating final directory entries...")
            
            final_files = []
            for i in range(5000):  # Fewer final files for exFAT
                filename = f"ZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZ_EXFAT_FINAL_{i:05d}.ZZZ"
                filepath = os.path.join(temp_dir, filename)
                
                try:
                    with open(filepath, 'w') as f:
                        f.write("EXFAT_CLEAN" * 50)  # Different pattern
                    final_files.append(filepath)
                    
                    if i % 1000 == 0 and i > 0:
                        elapsed = time.time() - phase3_start
                        rate = i / elapsed if elapsed > 0 else 0
                        GLib.idle_add(self._update_info_label, f"exFAT Cleaning: Final entries {i}... ({rate:.0f} entries/sec)")
                        print(f"exFAT final {i}... ({rate:.0f} entries/sec)")
                except OSError:
                    break
            
            phase3_time = time.time() - phase3_start
            print(f"exFAT Phase 3 completed: {len(final_files)} entries in {phase3_time:.1f} seconds")
            
            # Phase 4: Clean up
            cleanup_start = time.time()
            
            # CRITICAL: Always clean up files, especially if cancelled
            if self.cancelled:
                print("🧹 exFAT cleaning was cancelled - performing comprehensive cleanup...")
                # Clean up all files we created
                all_files = files_created + final_files
                self._cleanup_exfat_files(temp_dir, all_files)
            else:
                # Normal cleanup - use shutil.rmtree to handle all remaining content
                try:
                    if os.path.exists(temp_dir):
                        print(f"🧹 Cleaning up exFAT temp directory: {temp_dir}")
                        shutil.rmtree(temp_dir)
                except Exception as e:
                    print(f"⚠️ Error removing exFAT temp directory: {e}")
                
            total_time = time.time() - start_time
            print(f"exFAT metadata cleaning completed in {total_time:.1f} seconds total!")
            print(f"  Phase 1 (create): {phase1_time:.1f}s")
            print(f"  Phase 2 (delete): {phase2_time:.1f}s")
            print(f"  Phase 3 (final): {phase3_time:.1f}s")
            print(f"  Cleanup: {time.time() - cleanup_start:.1f}s")
            return True
            
        except Exception as e:
            print(f"exFAT cleaning error: {e}")
            # Clean up files on error
            all_files = files_created + final_files
            self._cleanup_exfat_files(temp_dir, all_files)
            return False
    
    def _update_info_label(self, text):
        """Update the info label text"""
        self.info_label.set_text(text)
        return False
    
    def _clean_metadata_only(self, drive_info):
        """Clean metadata only (MFT for NTFS, directory entries for exFAT) without free space wipe"""
        mount_point = drive_info['mount_point']
        
        # Check filesystem type and clean metadata
        fstype = drive_info.get('fstype', '').upper()
        if 'NTFS' in fstype:
            print("NTFS drive detected - cleaning MFT metadata only...")
            GLib.idle_add(self._update_info_label, "Cleaning MFT metadata only...")
            success = self._clean_mft_metadata(mount_point, drive_info)
            if success:
                GLib.idle_add(self._update_info_label, "MFT metadata cleaning completed!")
            else:
                GLib.idle_add(self._update_info_label, "MFT metadata cleaning failed or skipped")
        elif 'EXFAT' in fstype:
            print("exFAT drive detected - cleaning directory metadata only...")
            GLib.idle_add(self._update_info_label, "Cleaning exFAT metadata only...")
            success = self._clean_exfat_metadata(mount_point)
            if success:
                GLib.idle_add(self._update_info_label, "exFAT metadata cleaning completed!")
            else:
                GLib.idle_add(self._update_info_label, "exFAT metadata cleaning failed or skipped")
        else:
            GLib.idle_add(self._update_info_label, "Metadata cleaning not supported for this filesystem")
        
        # Reset UI after metadata cleaning
        GLib.idle_add(self._metadata_clean_complete)
    
    def _metadata_clean_complete(self):
        """Reset UI after metadata-only cleaning"""
        self.wiping = False
        self.paused = False
        
        # Re-enable all controls
        self.start_button.set_sensitive(True)
        self.mft_clean_button.set_sensitive(True)
        self.pause_button.set_sensitive(False)
        self.pause_button.set_label("Pause")
        self.progress_bar.set_fraction(0)
        
        # Re-enable drive selection
        self.drives_combo.set_sensitive(True)
        
        return False
    
    def _wipe_free_space(self, drive_info, method):
        mount_point = drive_info['mount_point']
        
        # Check filesystem type and clean metadata accordingly
        fstype = drive_info.get('fstype', '').upper()
        if 'NTFS' in fstype:
            print("NTFS drive detected - cleaning MFT metadata first...")
            GLib.idle_add(self._update_info_label, "Cleaning MFT metadata...")
            if not self._clean_mft_metadata(mount_point, drive_info):
                print("MFT cleaning failed, continuing with free space wipe...")
        elif 'EXFAT' in fstype:
            print("exFAT drive detected - cleaning directory metadata first...")
            GLib.idle_add(self._update_info_label, "Cleaning exFAT metadata...")
            if not self._clean_exfat_metadata(mount_point):
                print("exFAT cleaning failed, continuing with free space wipe...")
        
        wipe_folder = os.path.join(mount_point, "Free Space Cleaner")
        
        try:
            # Create the wipe folder
            os.makedirs(wipe_folder, exist_ok=True)
            
            # Get initial free space
            total_free = drive_info['free']
            
            # CCLEANER-STYLE: Random long filenames and 1GB files
            chunk_size = 64 * 1024 * 1024  # 64MB chunks - balance between speed and update frequency
            max_file_size = 1024 * 1024 * 1024  # 1GB per file (CCleaner style)
            
            if method == "zeros":
                data_chunk = b'\x00' * chunk_size
            elif method == "ones":
                data_chunk = b'\xFF' * chunk_size
            elif method == "3487":
                pattern = b"3487"
                data_chunk = pattern * (chunk_size // len(pattern))
            else:  # random
                data_chunk = None  # Generate on the fly
            
            file_count = 0
            bytes_written = 0
            start_time = time.time()
            last_update_time = start_time
            last_update_bytes = 0
            last_space_update_time = start_time
            
            # CCLEANER-STYLE: Generate random long filenames
            def generate_random_filename():
                """Generate random long filename like CCleaner does"""
                # Random prefix (10-20 characters)
                prefix_length = random.randint(10, 20)
                prefix = ''.join(random.choices(string.ascii_letters + string.digits, k=prefix_length))
                
                # Random middle part (15-25 characters)
                middle_length = random.randint(15, 25)
                middle = ''.join(random.choices(string.ascii_letters + string.digits, k=middle_length))
                
                # Random suffix (5-10 characters)
                suffix_length = random.randint(5, 10)
                suffix = ''.join(random.choices(string.ascii_letters + string.digits, k=suffix_length))
                
                # Random extension (3-4 characters)
                ext_length = random.randint(3, 4)
                extension = ''.join(random.choices(string.ascii_lowercase, k=ext_length))
                
                return f"{prefix}_{middle}_{suffix}.{extension}"
            
            # Keep writing files until disk is full
            while self.wiping:
                file_path = os.path.join(wipe_folder, generate_random_filename())
                current_file_size = 0
                
                try:
                    with open(file_path, 'wb', buffering=chunk_size) as f:
                        while self.wiping and current_file_size < max_file_size:
                            # Check if paused
                            while self.paused and self.wiping:
                                time.sleep(0.1)
                            
                            if not self.wiping:
                                break
                            
                            if method == "random":
                                chunk = os.urandom(chunk_size)
                            else:
                                chunk = data_chunk
                            
                            f.write(chunk)
                            bytes_written += len(chunk)
                            current_file_size += len(chunk)
                            
                            # Update progress - CCLEANER-STYLE: Show current random filename
                            current_time = time.time()
                            if current_time - last_update_time >= 0.5:
                                time_diff = current_time - last_update_time
                                bytes_diff = bytes_written - last_update_bytes
                                rate = bytes_diff / time_diff / (1024 * 1024) if time_diff > 0 else 0
                                
                                progress = bytes_written / total_free
                                remaining_bytes = total_free - bytes_written
                                time_remaining = remaining_bytes / (bytes_diff / time_diff) if bytes_diff > 0 else 0
                                
                                # Check if we should update free space display
                                update_free_space = (current_time - last_space_update_time) >= 3.0
                                
                                GLib.idle_add(
                                    self._update_progress,
                                    progress,
                                    rate,
                                    time_remaining,
                                    update_free_space
                                )
                                
                                last_update_time = current_time
                                last_update_bytes = bytes_written
                                
                                if update_free_space:
                                    last_space_update_time = current_time
                    
                    file_count += 1
                    
                except OSError as e:
                    # Disk is full
                    if e.errno == 28:
                        break
                    else:
                        raise
                
        except Exception as e:
            print(f"Error during wipe: {e}")
        finally:
            # Clean up - Remove wipe folder and all contents recursively
            try:
                if os.path.exists(wipe_folder):
                    print(f"Cleaning up wipe folder {wipe_folder}...")
                    shutil.rmtree(wipe_folder)
            except Exception as e:
                print(f"Error removing wipe folder: {e}")
            
            # Reset UI
            GLib.idle_add(self._wipe_complete)
    
        
        # Update free space display for current drive (only every 3 seconds)
        if update_free_space and self.current_drive_index >= 0 and self.current_drive_index < len(self.drives):
            drive_info = self.drives[self.current_drive_index]
            try:
                usage = shutil.disk_usage(drive_info['mount_point'])
                free_gb = usage.free / (1024**3)
                device_name = drive_info['name']
                drive_type = drive_info.get('type', 'Unknown')
                mount_point = drive_info['mount_point']
                display_name = f"{mount_point} ({device_name} - {drive_type}) - {free_gb:.1f} GB free"
                self.drives_combo.remove(self.current_drive_index)
                self.drives_combo.insert_text(self.current_drive_index, display_name)
                self.drives_combo.set_active(self.current_drive_index)
                # Update stored info
                drive_info['free'] = usage.free
            except:
                pass
        
        return False
    
    def _update_progress(self, progress, rate, time_remaining, update_free_space=False):
        self.progress_bar.set_fraction(min(progress, 1.0))
        
        # Format time remaining
        hours = int(time_remaining / 3600)
        mins = int((time_remaining % 3600) / 60)
        secs = int(time_remaining % 60)
        
        if hours > 0:
            time_str = f"{hours} hour{'s' if hours != 1 else ''}, {mins} min., {secs} sec."
        else:
            time_str = f"{mins} min., {secs} sec."
        
        self.info_label.set_text(f"Rate: {rate:.1f} MB/sec  Est Time Remaining: {time_str}")
        
        # Update free space display for current drive (only every 3 seconds)
        if update_free_space and self.current_drive_index >= 0 and self.current_drive_index < len(self.drives):
            drive_info = self.drives[self.current_drive_index]
            try:
                usage = shutil.disk_usage(drive_info['mount_point'])
                free_gb = usage.free / (1024**3)
                device_name = drive_info['name']
                drive_type = drive_info.get('type', 'Unknown')
                mount_point = drive_info['mount_point']
                display_name = f"{mount_point} ({device_name} - {drive_type}) - {free_gb:.1f} GB free"
                self.drives_combo.remove(self.current_drive_index)
                self.drives_combo.insert_text(self.current_drive_index, display_name)
                self.drives_combo.set_active(self.current_drive_index)
                # Update stored info
                drive_info['free'] = usage.free
            except:
                pass
        
        return False
    
    def _wipe_complete(self):
        self.wiping = False
        self.paused = False
        
        # Update free space display one final time
        if self.current_drive_index >= 0 and self.current_drive_index < len(self.drives):
            drive_info = self.drives[self.current_drive_index]
            try:
                usage = shutil.disk_usage(drive_info['mount_point'])
                free_gb = usage.free / (1024**3)
                device_name = drive_info['name']
                drive_type = drive_info.get('type', 'Unknown')
                mount_point = drive_info['mount_point']
                display_name = f"{mount_point} ({device_name} - {drive_type}) - {free_gb:.1f} GB free"
                self.drives_combo.remove(self.current_drive_index)
                self.drives_combo.insert_text(self.current_drive_index, display_name)
                self.drives_combo.set_active(self.current_drive_index)
                drive_info['free'] = usage.free
            except:
                pass
        
        # Check if we should start again (only if not cancelled)
        if not self.cancelled and self.check_start_again.get_active():
            # Cycle wipe type if enabled (skip MFT clean option)
            if self.check_cycle_wipe.get_active():
                if self.radio_zeros.get_active():
                    self.radio_random.set_active(True)
                elif self.radio_random.get_active():
                    self.radio_ones.set_active(True)
                elif self.radio_ones.get_active():
                    self.radio_3487.set_active(True)
                elif self.radio_3487.get_active():
                    self.radio_zeros.set_active(True)
                # MFT clean option is skipped in cycling - it doesn't make sense to cycle it
            
            # Only restart if not MFT clean mode
            if not self.radio_mft_clean.get_active():
                # Restart the wipe
                GLib.timeout_add(500, self._restart_wipe)
        else:
            # Normal completion or cancelled - reset UI
            self.current_drive_index = -1
            self.start_button.set_sensitive(True)
            self.mft_clean_button.set_sensitive(True)  # Re-enable MFT clean button
            self.pause_button.set_sensitive(False)
            self.pause_button.set_label("Pause")
            self.progress_bar.set_fraction(0)
            self.info_label.set_text("Rate: 0 MB/sec  Est Time Remaining: --")
            
            # Re-enable drive selection and wipe methods
            self.drives_combo.set_sensitive(True)
            self.radio_zeros.set_sensitive(True)
            self.radio_random.set_sensitive(True)
            self.radio_ones.set_sensitive(True)
            self.radio_3487.set_sensitive(True)
        
        return False
    
    def _restart_wipe(self):
        # Trigger start button click to restart
        self.on_start_clicked(None)
        return False
    
    def on_drive_selection_changed(self, combo):
        """Handle drive selection changes - update MFT tooltip status"""
        self._update_mft_tooltip_status()

def main():
    win = FreeSpaceWipeWindow()
    win.connect("destroy", Gtk.main_quit)
    win.show_all()
    Gtk.main()

if __name__ == "__main__":
    main()
