Name:           barones-free-space-cleaner
Version:        1.0.1
Release:        1%{?dist}
Summary:        Secure free space deletion tool for Linux

License:        MIT
URL:            https://github.com/Mad-scientist-star/Barones-Free-Space-Cleaner
Source0:        %{name}-%{version}.tar.gz

BuildArch:      noarch
Requires:       python3, python3-gobject, gtk3
Recommends:     smartmontools

%description
Barones Free Space Cleaner writes different patterns to all the free
space on your drives, then deletes it. This makes data recovery impossible.

Features:
- Multiple wipe patterns (zeros, ones, random data, 3487 pattern)
- Drive health monitoring via SMART data
- Progress tracking with real-time speed
- Simple GTK3 interface

%prep
%setup -q

%build
# Nothing to build

%install
rm -rf $RPM_BUILD_ROOT
mkdir -p $RPM_BUILD_ROOT%{_bindir}
mkdir -p $RPM_BUILD_ROOT%{_datadir}/applications
mkdir -p $RPM_BUILD_ROOT%{_datadir}/icons/hicolor/48x48/apps
mkdir -p $RPM_BUILD_ROOT%{_datadir}/icons/hicolor/64x64/apps
mkdir -p $RPM_BUILD_ROOT%{_datadir}/icons/hicolor/128x128/apps
mkdir -p $RPM_BUILD_ROOT%{_datadir}/icons/hicolor/256x256/apps
mkdir -p $RPM_BUILD_ROOT%{_datadir}/pixmaps

install -m 755 free-space-wipe.py $RPM_BUILD_ROOT%{_bindir}/barones-free-space-cleaner
install -m 644 barones-free-space-cleaner.desktop $RPM_BUILD_ROOT%{_datadir}/applications/
install -m 644 logo_48.png $RPM_BUILD_ROOT%{_datadir}/icons/hicolor/48x48/apps/barones-free-space-cleaner.png
install -m 644 logo_64.png $RPM_BUILD_ROOT%{_datadir}/icons/hicolor/64x64/apps/barones-free-space-cleaner.png
install -m 644 logo_128.png $RPM_BUILD_ROOT%{_datadir}/icons/hicolor/128x128/apps/barones-free-space-cleaner.png
install -m 644 logo_256.png $RPM_BUILD_ROOT%{_datadir}/icons/hicolor/256x256/apps/barones-free-space-cleaner.png
install -m 644 logo_48.png $RPM_BUILD_ROOT%{_datadir}/pixmaps/barones-free-space-cleaner.png

%post
/usr/bin/gtk-update-icon-cache -f -t %{_datadir}/icons/hicolor 2>/dev/null || :
/usr/bin/update-desktop-database %{_datadir}/applications 2>/dev/null || :

%postun
/usr/bin/gtk-update-icon-cache -f -t %{_datadir}/icons/hicolor 2>/dev/null || :
/usr/bin/update-desktop-database %{_datadir}/applications 2>/dev/null || :

%files
%{_bindir}/barones-free-space-cleaner
%{_datadir}/applications/barones-free-space-cleaner.desktop
%{_datadir}/icons/hicolor/48x48/apps/barones-free-space-cleaner.png
%{_datadir}/icons/hicolor/64x64/apps/barones-free-space-cleaner.png
%{_datadir}/icons/hicolor/128x128/apps/barones-free-space-cleaner.png
%{_datadir}/icons/hicolor/256x256/apps/barones-free-space-cleaner.png
%{_datadir}/pixmaps/barones-free-space-cleaner.png

%changelog
* Mon Oct 13 2025 Barones Project
- Initial release 1.0.0

