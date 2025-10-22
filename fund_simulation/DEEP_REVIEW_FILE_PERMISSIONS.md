# DEEP REVIEW: File Permissions and Installation Strategy

## Date
2025-10-21

## Critical Issue
**PermissionError: [Errno 13] Permission denied: 'temp_upload.csv'**

This error occurs because the application is installed to `C:\Program Files (x86)\Monte Carlo Fund Simulation\`, which requires administrator privileges to write files. The application attempts to write temporary files to its working directory (the installation directory), which fails for non-admin users.

---

## Complete File I/O Analysis

### All File Write Operations in Codebase

#### 1. **app.py** - Main Application
**Location:** Lines 116-118
```python
temp_path = "temp_upload.csv"
with open(temp_path, "wb") as f:
    f.write(uploaded_file.getbuffer())
```
**Issue:** Writes to working directory (Program Files) ❌
**Usage:** CSV file upload parsing
**Frequency:** Every time user uploads investment data

**Location:** Lines 179-181
```python
beta_temp_path = "temp_beta_upload.csv"
with open(beta_temp_path, "wb") as f:
    f.write(beta_uploaded_file.getbuffer())
```
**Issue:** Writes to working directory (Program Files) ❌
**Usage:** Beta price data upload parsing
**Frequency:** Every time user uploads beta data

**Location:** Line 565
```python
output_path = "investment_details.csv"
rows = export_investment_details(alpha_results, output_path)
```
**Issue:** Writes to working directory (Program Files) ❌
**Usage:** Detailed CSV export feature
**Frequency:** When user clicks "Generate Investment Details CSV"

**Location:** Line 581
```python
output_path = "cash_flow_schedule.csv"
rows = export_cash_flow_schedules(alpha_results, output_path)
```
**Issue:** Writes to working directory (Program Files) ❌
**Usage:** Cash flow CSV export feature
**Frequency:** When user clicks "Generate Cash Flow Schedule CSV"

#### 2. **fund_simulation/csv_export.py**
**Location:** Lines 33, 91
```python
with open(output_path, 'w', newline='', encoding='utf-8') as csvfile:
```
**Issue:** Uses path passed from app.py (Program Files) ❌
**Usage:** Called by app.py for CSV exports
**Frequency:** User-initiated

#### 3. **fund_simulation/excel_export.py**
**Returns BytesIO object** ✓
**No file writes to disk** ✓
**Good practice** - Returns in-memory buffer for download

### Summary of File Operations

**Total write operations identified:** 4 direct writes + 2 indirect (csv_export.py)
**All fail with current setup:** YES ❌
**Excel export works:** YES ✓ (uses BytesIO, no disk write)

---

## Root Cause Analysis

### Problem 1: Installation Location
**Current:** `C:\Program Files (x86)\Monte Carlo Fund Simulation\`
**Issue:** Requires admin privileges to write files
**Windows Security:** User Account Control (UAC) blocks non-admin writes to Program Files

### Problem 2: Working Directory Assumption
**Assumption:** Working directory is writable
**Reality:** Working directory is the installation directory (read-only for non-admin)
**Impact:** All file uploads and exports fail

### Problem 3: No Temp File Strategy
**Current:** Writes files directly to current directory
**Problem:** No use of system temp directories or user-writable locations

---

## Solution Options

### Option 1: Use System Temp Directory (RECOMMENDED)
**Implementation:**
- Use Python's `tempfile` module
- Files written to `C:\Users\<username>\AppData\Local\Temp\`
- Automatically writable by current user
- System cleans up old temp files

**Pros:**
- Minimal code changes
- Works with current installation location (Program Files)
- Standard Windows practice
- No user-visible temp files

**Cons:**
- Temp files may accumulate (though system eventually cleans)

### Option 2: Use User AppData\Local
**Implementation:**
- Create app-specific directory: `C:\Users\<username>\AppData\Local\MonteCarloFundSimulation\`
- Write all files there
- More permanent storage

**Pros:**
- Clean separation of code (Program Files) and data (AppData)
- User has full write permissions
- Files persist across sessions

**Cons:**
- More code changes required
- Need to create directory on first run

### Option 3: Install to User Directory (NOT RECOMMENDED)
**Implementation:**
- Change installer to install to `C:\Users\<username>\AppData\Local\Programs\MonteCarloFundSimulation\`
- No admin privileges required for installation
- Working directory is writable

**Pros:**
- Simplest for file permissions
- No admin rights needed

**Cons:**
- Non-standard for Windows applications
- Not a "professional" install location
- Each user needs separate installation
- Larger disk usage if multiple users on same machine

### Option 4: Eliminate Temp Files (HYBRID)
**Implementation:**
- For CSV uploads: Parse directly from Streamlit's buffer (no temp file)
- For CSV exports: Use in-memory buffers like Excel export does
- Combine with Option 1 for any unavoidable temp files

**Pros:**
- Best practice - no unnecessary disk I/O
- Fastest performance
- Most secure (no files on disk)

**Cons:**
- Requires code refactoring
- Some libraries may require file paths

---

## Recommended Solution

**HYBRID APPROACH: Option 4 (eliminate temp files) + Option 1 (tempfile for unavoidable cases)**

### Implementation Plan

#### Phase 1: Fix CSV Upload (Eliminate temp files)
**Current:**
```python
temp_path = "temp_upload.csv"
with open(temp_path, "wb") as f:
    f.write(uploaded_file.getbuffer())
investments, errors = parse_csv_file(temp_path)
```

**Fixed:**
```python
# Parse directly from buffer - no temp file needed
from io import StringIO
csv_content = StringIO(uploaded_file.getvalue().decode('utf-8'))
investments, errors = parse_csv_file_from_buffer(csv_content)
```

**Requires:** Modify `parse_csv_file()` to accept file-like object instead of path

#### Phase 2: Fix CSV Exports (Use tempfile)
**Current:**
```python
output_path = "investment_details.csv"
rows = export_investment_details(alpha_results, output_path)
with open(output_path, 'r', encoding='utf-8') as f:
    csv_data = f.read()
st.download_button(data=csv_data, ...)
```

**Fixed:**
```python
import tempfile
with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.csv', newline='') as f:
    rows = export_investment_details(alpha_results, f.name)
    temp_path = f.name

with open(temp_path, 'r', encoding='utf-8') as f:
    csv_data = f.read()
os.unlink(temp_path)  # Clean up
st.download_button(data=csv_data, ...)
```

**OR Better:** Return BytesIO like excel_export does:
```python
from io import StringIO
buffer = StringIO()
rows = export_investment_details_to_buffer(alpha_results, buffer)
csv_data = buffer.getvalue()
st.download_button(data=csv_data, ...)
```

#### Phase 3: Fix Beta Upload (Eliminate temp file)
Same approach as Phase 1

#### Phase 4: Update csv_export.py
Modify to accept file-like objects OR return StringIO buffers

---

## Additional Findings

### Cache Clearing in Launcher
**Location:** launch_with_embedded_python.bat line 61
```batch
for /d /r . %%d in (__pycache__) do @if exist "%%d" rd /s /q "%%d"
```
**Issue:** Tries to delete __pycache__ directories in installation folder
**Impact:** May fail silently if no write permissions
**Fix:** Not critical (Python can run with cached files), but could move to AppData if needed

### Streamlit State Files
**Streamlit may write:**
- Session state to temp
- Upload buffers to temp
- Cache files

**Status:** Streamlit handles this internally, uses system temp directory ✓

---

## Testing Checklist

After implementing fixes, test:
- [ ] Upload investment CSV without admin privileges
- [ ] Upload beta price CSV without admin privileges
- [ ] Generate investment details CSV
- [ ] Generate cash flow schedule CSV
- [ ] Export to Excel (should still work)
- [ ] Run simulation end-to-end
- [ ] Verify no files written to Program Files
- [ ] Verify no permission errors

---

## Code Changes Required

### Files to Modify:
1. **app.py**
   - Lines 114-121: Investment CSV upload (eliminate temp file)
   - Lines 177-184: Beta CSV upload (eliminate temp file)
   - Lines 564-577: Investment details export (use tempfile or BytesIO)
   - Lines 580-593: Cash flow export (use tempfile or BytesIO)

2. **fund_simulation/data_import.py**
   - `parse_csv_file()` - Accept file-like object or add new function

3. **fund_simulation/beta_import.py**
   - `parse_beta_csv()` - Accept file-like object or add new function

4. **fund_simulation/csv_export.py**
   - `export_investment_details()` - Accept file handle or return StringIO
   - `export_cash_flow_schedules()` - Accept file handle or return StringIO

---

## Implementation Priority

**P0 (Critical - Blocks all usage):**
- [ ] Fix CSV upload temp files (app.py lines 116, 179)
- [ ] Modify parse_csv_file() to accept buffers
- [ ] Modify parse_beta_csv() to accept buffers

**P1 (High - Breaks export features):**
- [ ] Fix CSV export temp files (app.py lines 565, 581)
- [ ] Modify csv_export.py to use buffers

**P2 (Low - Nice to have):**
- [ ] Remove __pycache__ cleanup from launcher (or move to AppData)

---

## Installer Configuration Review

### Current Setup
```iss
DefaultDirName={autopf}\{#MyAppName}
```
**{autopf}** = `C:\Program Files (x86)\` on 32-bit or `C:\Program Files\` on 64-bit

### Recommendation
**KEEP current installation location** (Program Files is correct for applications)
**FIX the code** to handle read-only installation directories properly

This is the professional approach:
- Application code in Program Files (read-only, protected)
- User data in AppData or Temp (writable)
- Follows Windows best practices
- Works correctly with UAC

---

## Prevention for Future

### Design Principles:
1. **Never write to installation directory**
2. **Always use tempfile module for temporary files**
3. **Use in-memory buffers (BytesIO, StringIO) when possible**
4. **Separate code (Program Files) from data (AppData/Temp)**
5. **Test as non-admin user**

### Code Review Checklist:
- [ ] No `open(filename, 'w')` with relative paths
- [ ] All temp files use `tempfile` module
- [ ] All exports return buffers or use tempfile
- [ ] No assumptions about current directory being writable
- [ ] Tested without administrator privileges

---

## Estimated Work

**Time to implement:** 1-2 hours
**Files to change:** 4 files
**Lines to change:** ~30-40 lines
**Testing required:** Full end-to-end test
**Risk:** Low (localized changes, well-defined interfaces)

---

## Next Steps

1. Implement P0 fixes (CSV upload temp files)
2. Test CSV upload works without admin
3. Implement P1 fixes (CSV export)
4. Test full workflow
5. Rebuild installer
6. Test installed version as non-admin user
7. Document changes in CLAUDE.md
