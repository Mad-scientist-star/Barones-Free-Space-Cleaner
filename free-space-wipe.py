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
        
        # Always use sudo for SMART data access
        try:
            result = subprocess.run(
                ['pkexec', 'smartctl', '-A', device_path],
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
        """Calculate overall SSD health assessment"""
        drive_type = self.drive_info.get('type', 'Unknown')
        
        if 'SSD' not in drive_type:
            self.assessment_label.set_markup("<b>Drive Type:</b> <span foreground='blue'>Non-SSD</span>")
            return
        
        # Look for key SSD health indicators
        warning_signs = []
        good_signs = []
        
        # Check wear indicators
        if 'Media Wearout Indicator' in health_data:
            try:
                wear_value = int(health_data['Media Wearout Indicator'].replace('%', ''))
                if wear_value < 50:
                    warning_signs.append(f"High wear: {wear_value}%")
                else:
                    good_signs.append(f"Good wear level: {wear_value}%")
            except:
                pass
        
        # Check available reserved space
        if 'Available Reserved Space' in health_data:
            try:
                reserved = health_data['Available Reserved Space']
                if '%' in reserved:
                    reserved_value = int(reserved.replace('%', ''))
                    if reserved_value < 10:
                        warning_signs.append("Low reserved space")
                    else:
                        good_signs.append("Good reserved space")
            except:
                pass
        
        # Check temperature
        if 'Temperature' in health_data:
            try:
                temp_str = health_data['Temperature'].replace('°C', '')
                temp = int(temp_str)
                if temp > 70:
                    warning_signs.append(f"High temp: {temp}°C")
                elif temp > 60:
                    good_signs.append(f"Warm: {temp}°C")
                else:
                    good_signs.append(f"Good temp: {temp}°C")
            except:
                pass
        
        # Check for errors
        error_indicators = ['Reallocated Sector Count', 'Current Pending Sector Count',
                           'Reported Uncorrectable Errors', 'Command Timeout']
        for indicator in error_indicators:
            if indicator in health_data:
                try:
                    value = int(health_data[indicator])
                    if value > 0:
                        warning_signs.append(f"{indicator}: {value}")
                    else:
                        good_signs.append(f"No {indicator.lower()}")
                except:
                    pass
        
        # Determine overall status
        if warning_signs:
            status_text = "⚠️ SSD needs attention"
            color = "red"
            details = f" ({len(warning_signs)} warnings)"
        elif good_signs:
            status_text = "✅ SSD good shape"
            color = "green"
            details = ""
        else:
            status_text = "❓ SSD status unknown"
            color = "orange"
            details = ""
        
        self.assessment_label.set_markup(f"<b>SSD Status:</b> <span foreground='{color}'>{status_text}{details}</span>")
    
    def show_error(self, error_msg):
        """Show error message in health panel"""
        self.health_data_box.remove(self.loading_label)
        error_label = Gtk.Label(label=f"Error: {error_msg}")
        error_label.set_markup(f"<span foreground='red'>Error: {error_msg}</span>")
        self.health_data_box.pack_start(error_label, True, True, 0)
        self.show_all()


class FreeSpaceWipeWindow(Gtk.Window):
    def __init__(self):
        super().__init__(title="Barones Free Space Cleaner")
        self.set_default_size(450, 300)
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
        
        # Main vertical box
        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        self.add(vbox)
        
        # Drives section
        drives_label = Gtk.Label(label="Drives:", xalign=0)
        vbox.pack_start(drives_label, False, False, 0)
        
        # Drives dropdown with health button
        drives_hbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=5)
        self.drives_combo = Gtk.ComboBoxText()
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
        
        # Radio buttons for wipe type in two columns
        radio_hbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=20)
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
        vbox.pack_start(radio_hbox, False, False, 0)
        
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
        
        # Use lsblk to get block devices with mount points
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
                
                # Create display string with drive type
                display_name = f"{mount_point} ({device_name} - {drive_type}) - {free_gb:.1f} GB free"
                
                self.drives.append({
                    'mount_point': mount_point,
                    'free': usage.free,
                    'total': usage.total,
                    'name': device_name,
                    'type': drive_type
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
        else:
            wipe_method = "3487"
        
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
    
    def on_cancel_clicked(self, button):
        if self.wiping:
            self.cancelled = True
            self.wiping = False
    
    def _wipe_free_space(self, drive_info, method):
        mount_point = drive_info['mount_point']
        wipe_folder = os.path.join(mount_point, "Free Space Cleaner")
        
        try:
            # Create the wipe folder
            os.makedirs(wipe_folder, exist_ok=True)
            
            # Get initial free space
            total_free = drive_info['free']
            
            # Prepare data chunks (need chunks for efficiency - writing byte by byte would be extremely slow)
            chunk_size = 64 * 1024 * 1024  # 64MB chunks - balance between speed and update frequency
            max_file_size = 2 * 1024 * 1024 * 1024  # 2GB per file
            
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
            
            # Keep writing files until disk is full
            while self.wiping:
                file_path = os.path.join(wipe_folder, f"wipe_{file_count}.dat")
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
                            
                            # Update progress
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
            # Clean up
            try:
                if os.path.exists(wipe_folder):
                    shutil.rmtree(wipe_folder)
            except Exception as e:
                print(f"Error cleaning up: {e}")
            
            # Reset UI
            GLib.idle_add(self._wipe_complete)
    
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
            # Cycle wipe type if enabled
            if self.check_cycle_wipe.get_active():
                if self.radio_zeros.get_active():
                    self.radio_random.set_active(True)
                elif self.radio_random.get_active():
                    self.radio_ones.set_active(True)
                elif self.radio_ones.get_active():
                    self.radio_3487.set_active(True)
                else:  # 3487
                    self.radio_zeros.set_active(True)
            
            # Restart the wipe
            GLib.timeout_add(500, self._restart_wipe)
        else:
            # Normal completion or cancelled - reset UI
            self.current_drive_index = -1
            self.start_button.set_sensitive(True)
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

def main():
    win = FreeSpaceWipeWindow()
    win.connect("destroy", Gtk.main_quit)
    win.show_all()
    Gtk.main()

if __name__ == "__main__":
    main()
