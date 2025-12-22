# Entrypoint Review & Potential Runtime Issues

## Issues Found

### 1. Unused Dependencies in requirements.txt
- `fastapi>=0.104.0` - Not used anywhere in codebase
- `uvicorn>=0.24.0` - Not used anywhere in codebase  
- `pydantic>=2.5.0` - Not used anywhere in codebase
- **Impact**: Unnecessary installs, confusion about what's actually needed
- **Recommendation**: Remove or add comment explaining future use

### 2. Duplicate Dependency
- `numpy>=1.24.0` appears twice (lines 10 and 17)
- **Impact**: Redundant but harmless
- **Recommendation**: Remove duplicate

### 3. Voice Module Runtime Dependencies

#### sounddevice requires PortAudio
- `sounddevice` Python package requires PortAudio system library
- On macOS: Usually pre-installed or via Homebrew (`brew install portaudio`)
- On Linux: May need `sudo apt-get install portaudio19-dev` or equivalent
- **Impact**: Import may succeed but `sd.rec()` will fail at runtime if PortAudio missing
- **Current handling**: Has try/except for import, but runtime failures in `record_audio()` are caught

#### Whisper Model Download
- First Whisper usage downloads model (~150MB-1.5GB depending on size)
- Happens in `_initialize_model()` - blocks until download completes
- **Impact**: First run will hang during model download, no progress indicator
- **Current handling**: Print statement shows "Loading Whisper model..." but no progress

#### Microphone Permissions (macOS)
- macOS will prompt for microphone access on first audio recording attempt
- If denied, `sd.rec()` will fail silently
- **Impact**: Voice mode appears to work but recording fails
- **Current handling**: Exception caught but error message may not be clear

### 4. Import Path Issues
- All imports use relative imports (no `src.` prefix)
- **Impact**: Must run from `src/` directory or have `src/` in PYTHONPATH
- **Current**: `python3 src/main.py` should work if run from project root
- **Risk**: If run from `src/` directory, relative imports may fail for sibling modules

### 5. ChromaDB System Dependencies
- ChromaDB may require additional system libraries (SQLite, etc.)
- **Impact**: Import may succeed but runtime operations may fail
- **Current handling**: Optional import with try/except

### 6. Missing Error Context
- Voice initialization failures are caught but error messages may be unclear
- No distinction between "missing dependency" vs "permission denied" vs "hardware unavailable"
- **Recommendation**: Add more specific error messages

## Recommendations

1. **Clean up requirements.txt**: Remove unused deps, fix duplicate numpy
2. **Add runtime checks**: Verify PortAudio availability before using sounddevice
3. **Improve Whisper loading**: Add progress indicator or async loading
4. **Better permission handling**: Detect and explain microphone permission issues
5. **Documentation**: Add setup guide for system dependencies (PortAudio, etc.)

