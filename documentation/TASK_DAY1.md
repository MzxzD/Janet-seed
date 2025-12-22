# Day 1 Task: Implement Janet Bootstrap

## Files to Create/Modify
1. `src/main.py` (provided above — implement TODOs)
2. `src/hardware_detector.py` (enhance detection)
3. `src/installer.py` (actual installation logic)
4. `constitution/personality.json` (already exists)

## Implementation Steps

### Step 1: Hardware Detection
- Complete `detect_hardware()` function in `main.py`
- Add GPU detection (optional)
- Add network capability detection (should show "offline only")
- Create capability report: `hardware_report.json`

### Step 2: Constitution Verification
- Ensure `Constitution.verify()` runs on startup
- Add daily automatic verification
- Log verification results to encrypted log

### Step 3: Consent Dialog
- Make briefing more interactive
- Add "show all axioms" option
- Store consent with timestamp and hardware fingerprint
- Consent must be explicit (default is NO)

### Step 4: Seed Installation
**Minimal installation includes:**
- Python virtual environment with dependencies
- Ollama + `tinyllama:1.1b` (smallest viable model)
- Janet Core files
- Launch script: `janet-start`

**Rules:**
- No internet access after install
- All dependencies bundled or cached
- Installation reversible via `janet-uninstall`

### Step 5: Red Thread Implementation
- Must work immediately after install
- Stops all processes, not just conversation
- Cannot be overridden by any command
- Requires explicit reset

## Success Criteria
1. User runs `./install.sh`
2. Sees hardware report
3. Reads constitutional briefing
4. Explicitly consents
5. Installation completes
6. Running `janet-start` launches Janet Seed
7. "red thread" command stops everything immediately
8. "quit" exits cleanly

## Testing Commands
```bash
# Test hardware detection
python src/main.py --detect-only

# Test constitution verification
python src/main.py --verify

# Full installation test
./install.sh
