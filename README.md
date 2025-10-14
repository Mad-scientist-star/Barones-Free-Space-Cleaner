# Barones Free Space Cleaner

**Secure data deletion for Linux - Actually delete files from your drive**

![Barones Free Space Cleaner](https://private-us-east-1.manuscdn.com/sessionFile/L9TH4FGQLINJ3zHGYhh6Pd/sandbox/PaG7PgdltH8qJm9ulDgWaI-images_1760388290199_na1fn_L2hvbWUvdWJ1bnR1L0Jhcm9uZXMtRnJlZS1TcGFjZS1DbGVhbmVyL2Fzc2V0cy9sb2dvcy9sb2dvX2NvbmNlcHRfMQ.png?Policy=eyJTdGF0ZW1lbnQiOlt7IlJlc291cmNlIjoiaHR0cHM6Ly9wcml2YXRlLXVzLWVhc3QtMS5tYW51c2Nkbi5jb20vc2Vzc2lvbkZpbGUvTDlUSDRGR1FMSU5KM3pIR1loaDZQZC9zYW5kYm94L1BhRzdQZ2RsdEg4cUptOXVsRGdXYUktaW1hZ2VzXzE3NjAzODgyOTAxOTlfbmExZm5fTDJodmJXVXZkV0oxYm5SMUwwSmhjbTl1WlhNdFJuSmxaUzFUY0dGalpTMURiR1ZoYm1WeUwyRnpjMlYwY3k5c2IyZHZjeTlzYjJkdlgyTnZibU5sY0hSZk1RLnBuZyIsIkNvbmRpdGlvbiI6eyJEYXRlTGVzc1RoYW4iOnsiQVdTOkVwb2NoVGltZSI6MTc5ODc2MTYwMH19fV19&Key-Pair-Id=K2HSFNDJXOU9YS&Signature=V2YAGY37op~usao05LheKTolzh3JsPwgcVq4R8ys1OXhk45T9XPCX7XPm69bmIEik7wIKeSVoH-r6JmJu3sy~GMOyEq4FFkIy~RpJ02mWJSwESHmKmZiKhU5ZRC6I-Znar~u-fLpB4glXkMHnYvMO-6eOw~Yde0B7iuErqf8rmeiv8teToyKipM~lXg4FB~02jvs2W2vSpNToR9EaUjSMUrVZNXUijDbKsPlz2coq~dqYeroo7W-Whk2-jp0dATssef-88JzJRvCjva9DY57-TCvbn64L~3eoqFZRQSbP0Vm~P99wexR7ic0EwFHHC-4ADs7Ki4iQomeUfLdcB8lcA__)

## What is this?

When you "delete" a file, it's not really gone. The operating system just removes the reference to it, but the actual data remains on your drive until it gets overwritten. Anyone with recovery tools can potentially access your "deleted" files.

**Barones Free Space Cleaner** writes different patterns to all the free space on your drives, then deletes it. This makes data recovery impossible. Your data is truly gone.

## Why Barones?

The philosophy behind this program is **simplicity**. No complicated settings, no feature bloat, no extra bullshit. Just easy-to-understand buttons that do what they say.

### Key Features

- **Multiple Wipe Patterns**: Choose from zeros, ones, random data, or the 3487 pattern
- **Drive Health Monitoring**: Built-in SMART data monitoring for both SATA/SSD and NVMe drives
- **Progress Tracking**: Real-time write speed and estimated time remaining
- **Simple Controls**: Start, Pause, Cancel - that's it
- **Auto-Repeat**: Optionally restart when finished and cycle through wipe patterns
- **Clean GTK3 Interface**: Native Linux desktop application

## Installation

Barones Free Space Cleaner is available as professional distribution packages for all major Linux distributions.

### Debian/Ubuntu (and derivatives)

Download the `.deb` package from the [releases page](https://github.com/Mad-scientist-star/Barones-Free-Space-Cleaner/releases) and install:

```bash
sudo dpkg -i barones-free-space-cleaner_1.0.0_all.deb
```

Supported distributions: Debian 10+, Ubuntu 20.04+, Linux Mint 20+, Pop!_OS 20.04+, Elementary OS 6+

### Fedora/RHEL (and derivatives)

Download the `.rpm` package from the [releases page](https://github.com/Mad-scientist-star/Barones-Free-Space-Cleaner/releases) and install:

```bash
sudo rpm -i barones-free-space-cleaner-1.0.0-1.noarch.rpm
```

Or with dnf:
```bash
sudo dnf install barones-free-space-cleaner-1.0.0-1.noarch.rpm
```

Supported distributions: Fedora 35+, RHEL 8+, CentOS Stream 8+, Rocky Linux 8+, AlmaLinux 8+

### Arch Linux (and derivatives)

Clone the repository and use the AUR package:

```bash
git clone https://github.com/Mad-scientist-star/Barones-Free-Space-Cleaner.git
cd Barones-Free-Space-Cleaner/packaging/aur
makepkg -si
```

Supported distributions: Arch Linux, Manjaro, EndeavourOS, Garuda Linux

### After Installation

The application will appear in your Applications menu under System/Utilities as **"Barones Free Space Cleaner"** with a custom icon.

You can also launch it from the terminal:
```bash
barones-free-space-cleaner
```

### Requirements

All packages automatically install dependencies:
- Python 3 with GTK 3.0 (PyGObject)
- Optional: `smartctl` for drive health monitoring

## Usage

1. **Launch the application** from your desktop or application menu
2. **Select a drive** from the dropdown menu
3. **Choose a wipe pattern**:
   - All 0's (zeros)
   - All 1's
   - Random data
   - 3487 pattern
4. **Click Start** to begin wiping free space
5. **Monitor progress** with the real-time progress bar and speed indicator
6. **Check drive health** by clicking the "Drive Health" button (requires `smartctl`)

### Optional Settings

- **Start again when finished**: Automatically restart the wipe process when complete
- **Cycle wipe type on start again**: Change to the next wipe pattern on each restart

## How It Works

The program fills all available free space on your selected drive with the chosen pattern (zeros, ones, random data, or a specific pattern). Once the free space is filled, it deletes the temporary files, leaving your drive clean but with all previously "deleted" data now truly unrecoverable.

This is particularly useful when:
- Selling or donating a computer or drive
- Returning a leased computer
- Ensuring sensitive data cannot be recovered
- Maintaining privacy and security

## Drive Health Monitoring

The built-in health monitor displays critical SMART attributes including:
- Temperature
- SSD Life Left / Media Wearout Indicator
- Power-On Hours
- Total Data Written/Read
- Available Reserved Space
- Error counts and other health metrics

Works with both traditional SATA/SSD drives and modern NVMe drives.

## Screenshots

![Main Interface](https://private-us-east-1.manuscdn.com/sessionFile/L9TH4FGQLINJ3zHGYhh6Pd/sandbox/PaG7PgdltH8qJm9ulDgWaI-images_1760388290200_na1fn_L2hvbWUvdWJ1bnR1L0Jhcm9uZXMtRnJlZS1TcGFjZS1DbGVhbmVyL2Fzc2V0cy9zY3JlZW5zaG90cy9tYWluLWludGVyZmFjZQ.jpg?Policy=eyJTdGF0ZW1lbnQiOlt7IlJlc291cmNlIjoiaHR0cHM6Ly9wcml2YXRlLXVzLWVhc3QtMS5tYW51c2Nkbi5jb20vc2Vzc2lvbkZpbGUvTDlUSDRGR1FMSU5KM3pIR1loaDZQZC9zYW5kYm94L1BhRzdQZ2RsdEg4cUptOXVsRGdXYUktaW1hZ2VzXzE3NjAzODgyOTAyMDBfbmExZm5fTDJodmJXVXZkV0oxYm5SMUwwSmhjbTl1WlhNdFJuSmxaUzFUY0dGalpTMURiR1ZoYm1WeUwyRnpjMlYwY3k5elkzSmxaVzV6YUc5MGN5OXRZV2x1TFdsdWRHVnlabUZqWlEuanBnIiwiQ29uZGl0aW9uIjp7IkRhdGVMZXNzVGhhbiI6eyJBV1M6RXBvY2hUaW1lIjoxNzk4NzYxNjAwfX19XX0_&Key-Pair-Id=K2HSFNDJXOU9YS&Signature=fg-dOvysGPG29ftrXMR10162t9P4XohZnevqHpoiVcQEn52QmV74XwQT4U-z26Mhmh-dD73BTZPT7hqjZAm9fBsjzbJg4jmM7DRDA~uTzMy7Rs75ZUhfjelYqvtH6dXlrDC2NogZ4iWcd~dF7oLFhdHJxz-IR-m9lOSDRWfIyMSkF9T6MYEFtj~PRBhdxcEyNR2N2Van~k~gIiJvBliaqqzWhCmWje9cg1OM7dA2oZck5M70gB0VVUJelqyayWlu5rVwiQnxmR-0Rwi757pDnjYOwqEOP~mJgmenH3~zNKPSy7ujwez3zIZDtzYRB0rzmAwF93gjabtPFRfSBzNObw__)
*Simple, clean interface with all controls visible*

## Technical Details

- **Language**: Python 3
- **GUI Framework**: GTK 3.0 (PyGObject)
- **Threading**: Non-blocking operations using Python threading
- **Privileges**: Uses `pkexec` for elevated privileges when needed (for SMART data)

## Security Note

This tool overwrites free space only. It does not touch your existing files. However, the wiping process is irreversible - data that has been overwritten cannot be recovered.

## License

This project is open source. See LICENSE file for details.

## Contributing

Contributions are welcome! The goal is to keep this program simple and focused. If you have ideas for improvements that maintain the simplicity philosophy, feel free to open an issue or pull request.

## Credits

Inspired by similar Windows utilities, built for Linux with simplicity in mind.

---

**For more information and downloads, visit the [project website](https://barones-free-space-cleaner.manus.app)**

