# Build Instructions - Creating the Windows Installer

This guide explains how to build the Windows installer for distribution to your team.

## Prerequisites

### 1. Install Inno Setup 6

**Download:** https://jrsoftware.org/isinfo.php

**Install:**
1. Run the installer
2. Use default installation path: `C:\Program Files (x86)\Inno Setup 6\`
3. Complete installation

**Verify installation:**
```cmd
"C:\Program Files (x86)\Inno Setup 6\ISCC.exe" /?
```

### 2. Verify Project Files

Ensure all required files are present:

```
fund_simulation/
├── app.py                          ✓ Main application
├── requirements.txt                ✓ Dependencies list
├── launch_fund_simulation.bat      ✓ Launcher script
├── installer.iss                   ✓ Inno Setup script
├── build_installer.bat             ✓ Build automation
├── USER_GUIDE.md                   ✓ User documentation
├── README.md                       ✓ Project documentation
├── icon.ico                        ○ Optional app icon
└── fund_simulation/                ✓ Python package
    ├── __init__.py
    ├── models.py
    ├── calculators.py
    ├── data_import.py
    ├── beta_import.py
    ├── simulation.py
    ├── statistics.py
    ├── beta_simulation.py
    ├── reconstruction.py
    ├── csv_export.py
    └── excel_export.py
```

---

## Building the Installer

### Quick Build (Automated)

1. **Navigate to project directory:**
   ```cmd
   cd "C:\Users\ZacharyMatula\Code Projects\Private Fund Simulation\fund_simulation"
   ```

2. **Run build script:**
   ```cmd
   build_installer.bat
   ```

3. **Wait for completion** (~30 seconds)

4. **Find installer in:**
   ```
   installer_output\FundSimulation_Setup_v1.0.0.exe
   ```

### Manual Build (If needed)

1. **Open Inno Setup Compiler**
2. **File → Open → Select `installer.iss`**
3. **Build → Compile** (or press F9)
4. **Check output:** `installer_output\FundSimulation_Setup_v1.0.0.exe`

---

## Testing the Installer

### Pre-Distribution Testing

**Test on a clean Windows machine** (or VM) that:
- Has NO Python installed (to test Python detection)
- Has NO development tools
- Represents typical end-user environment

### Testing Steps

1. **Run installer:**
   ```
   FundSimulation_Setup_v1.0.0.exe
   ```

2. **Verify installation:**
   - Check installation completed without errors
   - Verify desktop shortcut created (if selected)
   - Verify Start Menu entry exists

3. **First launch:**
   - Double-click desktop shortcut
   - Verify virtual environment creation (first time only)
   - Verify dependencies install correctly
   - Verify browser opens to `http://localhost:8501`
   - Verify app loads without errors

4. **Test workflow:**
   - Import sample investment data
   - Import sample beta data
   - Configure simulation parameters
   - Run simulation
   - Export results to Excel
   - Open Excel file and verify formatting

5. **Second launch:**
   - Close app (close command window)
   - Launch again
   - Verify startup is faster (~5-10 seconds vs 2-3 minutes)

---

## Customization

### Update Version Number

**Edit `installer.iss`:**
```iss
#define MyAppVersion "1.0.0"  ← Change this
```

**Output filename changes to:**
```
FundSimulation_Setup_v{version}.exe
```

### Add Company Logo/Icon

1. **Create icon:** `icon.ico` (256x256 recommended)
2. **Place in:** `fund_simulation/icon.ico`
3. **Rebuild installer**

Icon appears:
- During installation
- On desktop shortcut
- In Start Menu

### Customize Company Info

**Edit `installer.iss`:**
```iss
#define MyAppPublisher "Your Company Name"  ← Change
#define MyAppURL "https://yourcompany.com"  ← Change
```

### Modify Installation Path

**Edit `installer.iss`:**
```iss
DefaultDirName={autopf}\{#MyAppName}  ← Default: Program Files
DefaultDirName={userdocs}\{#MyAppName}  ← Alternative: My Documents
```

---

## Distribution

### Recommended Approach

1. **Upload to company network share:**
   ```
   \\company-server\software\FundSimulation_Setup_v1.0.0.exe
   ```

2. **Send email to team:**
   ```
   Subject: Monte Carlo Fund Simulation - Installation

   Hi team,

   The Monte Carlo Fund Simulation tool is now available.

   Installation:
   1. Download: \\company-server\software\FundSimulation_Setup_v1.0.0.exe
   2. Run installer
   3. Launch from desktop shortcut

   Requirements:
   - Python 3.8+ (installer will prompt if not installed)
   - Internet connection (first launch only)

   User Guide: [Attach USER_GUIDE.md]

   Questions? Contact [support email]
   ```

### Alternative: Cloud Distribution

**Upload to:**
- SharePoint
- Google Drive (company)
- OneDrive for Business

**Share link with team**

### File Size

**Typical installer size:** ~500 KB (just application files)

**Note:** Actual dependencies (Python packages) download during first launch. This keeps installer small and ensures latest package versions.

---

## Updating the Application

### For Code Changes

1. **Make code changes** in `app.py` or `fund_simulation/*.py`
2. **Test locally:**
   ```cmd
   streamlit run app.py
   ```
3. **Update version number** in `installer.iss`
4. **Rebuild installer:**
   ```cmd
   build_installer.bat
   ```
5. **Distribute new installer**

### For Dependency Changes

1. **Update `requirements.txt`**
2. **Test installation in clean environment:**
   ```cmd
   python -m venv test_env
   test_env\Scripts\activate
   pip install -r requirements.txt
   streamlit run app.py
   ```
3. **Rebuild installer**
4. **Distribute**

**Note:** Users with existing installations will auto-upgrade dependencies on next launch.

---

## Troubleshooting Build Issues

### "Inno Setup not found"

**Solution:**
- Install Inno Setup 6
- Verify installation path: `C:\Program Files (x86)\Inno Setup 6\`
- If installed elsewhere, edit `build_installer.bat`:
  ```batch
  set "INNO_PATH=C:\Your\Custom\Path\ISCC.exe"
  ```

### "Missing required files"

**Solution:**
- Verify all files listed in "Project Files" section exist
- Check you're in correct directory
- Verify `fund_simulation/` folder contains all Python modules

### Build succeeds but installer fails

**Check:**
1. **Test on clean machine** (not development environment)
2. **Check Windows Event Viewer** for errors
3. **Run installer from command prompt** to see errors:
   ```cmd
   FundSimulation_Setup_v1.0.0.exe /LOG="install.log"
   ```
4. **Review `install.log`**

---

## Support

### For build issues:
- Check this document
- Review Inno Setup documentation: https://jrsoftware.org/ishelp/

### For application issues:
- See `USER_GUIDE.md`
- Test in development environment first

---

## Changelog

### Version 1.0.0
- Initial release
- Basic installer with Python detection
- Auto-setup of virtual environment
- Desktop shortcut creation
- User guide included
