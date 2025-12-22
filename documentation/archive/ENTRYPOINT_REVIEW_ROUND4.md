# Entrypoint Review Round 4 - Thread Safety & Edge Cases

## Issues Found

### 1. Thread Safety - Race Condition in WakeWordDetector ⚠️
**Location**: `src/voice/wake_word.py`

**Problem**:
- `self.listening` flag is accessed from multiple threads without locks
- Main thread sets `self.listening = False` in `stop_listening()`
- Worker thread checks `while self.listening:` in `_listen_loop()`
- No synchronization mechanism - race condition possible
- `thread.join(timeout=1.0)` may not be sufficient if thread is in long operation

**Impact**: Wake word detection thread might not stop immediately, or could continue running after stop

**Current Code**:
```python
def stop_listening(self):
    self.listening = False  # Set by main thread
    if self.thread:
        self.thread.join(timeout=1.0)  # Wait, but thread might be in sleep/recording

def _listen_loop(self, ...):
    while self.listening:  # Checked by worker thread - no lock
        # Long operations (sleep, recording) - flag might change during
```

### 2. Thread Safety - Wake Word Flag Race Condition ⚠️
**Location**: `src/core/janet_core.py`, `src/core/presence_loop.py`

**Problem**:
- `janet._wake_word_detected_flag` is set by callback from wake word thread
- Flag is checked and reset in presence loop (main thread)
- No synchronization - race condition possible

**Impact**: Wake word detection might be missed or double-triggered

**Current Code**:
```python
# In wake_word.py callback (worker thread):
janet._wake_word_detected_flag = True

# In presence_loop.py (main thread):
if janet._wake_word_detected_flag:
    janet._wake_word_detected_flag = False  # Reset
```

### 3. Cleanup - Wake Detector Not Stopped on Exception
**Location**: `src/main.py:298-329`

**Problem**:
- Wake detector cleanup only happens at end of main loop
- If exception occurs in loop and program exits, wake detector thread continues
- Thread is daemon=True so will terminate with program, but not cleanly

**Impact**: Thread might be in middle of operation when program exits (less critical but unclean)

**Current Code**:
```python
while True:
    try:
        # ... operations ...
    except Exception as e:
        # ... error handling ...
        # Wake detector not stopped here!

# Cleanup only at end
if voice_mode and janet.wake_detector:
    janet.wake_detector.stop_listening()
```

### 4. Path Handling - Directory Creation Errors Not Handled
**Location**: Multiple files using `mkdir(parents=True, exist_ok=True)`

**Problem**:
- Directory creation can fail (permissions, disk full, read-only filesystem)
- Errors not caught in most places
- Operations proceed assuming directory exists

**Impact**: File operations fail later with unclear error messages

**Current Code**:
```python
self.memory_dir.mkdir(parents=True, exist_ok=True)  # No error handling
# Later operations assume directory exists
```

### 5. Path Handling - Path.home() Could Fail
**Location**: `src/main.py:get_janet_home()`

**Problem**:
- `Path.home()` can fail in some environments (no home directory, unusual setups)
- Error not handled

**Impact**: Program crashes on initialization in edge case environments

**Current Code**:
```python
return Path(os.environ.get("JANET_HOME", Path.home() / ".janet")).expanduser().resolve()
```

### 6. Wake Word Thread - Potential Blocking in Cleanup
**Location**: `src/voice/wake_word.py:stop_listening()`

**Problem**:
- `thread.join(timeout=1.0)` might not be enough if thread is in long recording operation
- Thread might continue briefly after `self.listening = False`
- No way to interrupt long-running operations

**Impact**: Cleanup might not be immediate, thread might continue briefly

### 7. Error Loop in Main Loop - No Retry Limit
**Location**: `src/main.py:298-325`

**Problem**:
- If same exception keeps occurring, loop becomes infinite
- No retry limit or break condition
- Could consume resources indefinitely

**Impact**: Program could get stuck in error loop (though less likely with current error handling)

## Recommendations

### High Priority
1. **Add thread synchronization** - Use threading.Lock or threading.Event for wake word detection
2. **Handle directory creation errors** - Wrap mkdir in try/except, fail gracefully
3. **Handle Path.home() failures** - Add fallback or clear error message

### Medium Priority
4. **Improve cleanup** - Add cleanup in exception handler
5. **Improve thread stopping** - Better mechanism to stop wake word thread cleanly

### Low Priority
6. **Add retry limit** - Prevent infinite error loops (though current error handling makes this unlikely)

## Summary

Key findings:
- ✅ Thread safety issues fixed - added locks for wake word detection
- ✅ Directory creation errors now handled properly
- ✅ Path.home() failures now handled with fallback
- ✅ Cleanup improved in exception handler

## Fixes Applied

### 1. Thread Safety in WakeWordDetector ✅ FIXED
- Added `threading.Lock` for thread-safe access to `listening` flag
- Converted `listening` to property with lock-protected getter/setter
- Improved thread stopping with periodic flag checks during long operations
- Increased join timeout for cleaner shutdown

### 2. Thread Safety for Wake Word Flag ✅ FIXED
- Added `threading.Lock` for `_wake_word_detected_flag` in JanetCore
- Created `_check_and_reset_wake_flag()` method for thread-safe check-and-reset
- All flag access now goes through synchronized methods

### 3. Directory Creation Error Handling ✅ FIXED
- Added error handling in `MemoryManager.__init__()` - raises RuntimeError on failure
- Added error handling in `EncryptedSQLite.__init__()` - raises RuntimeError on failure
- Added error handling in `ChromaDBStore.__init__()` - prints warning (non-critical)
- Clear error messages for debugging

### 4. Path.home() Error Handling ✅ FIXED
- Added try/except for `Path.home()` in `get_janet_home()`
- Provides clear error message if home directory cannot be determined
- Suggests setting JANET_HOME environment variable as fallback

### 5. Cleanup in Exception Handler ✅ FIXED
- Added wake detector cleanup attempt in main loop exception handler
- Continues loop after cleanup attempt (non-fatal)
- Prevents wake detector from running indefinitely on errors

### 6. Improved Thread Shutdown ✅ ENHANCED
- Wake word thread now checks flag periodically during long operations
- Allows faster shutdown when stop_listening() is called
- Thread will exit more quickly even if in middle of recording/transcription

All critical thread safety and edge case issues have been addressed. The system is now more robust and production-ready.

