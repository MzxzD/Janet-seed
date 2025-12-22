# Entrypoint Review Round 3 - Sanity Check & Edge Cases

## Issues Found

### 1. SQLite Connection Resource Leak Risk ⚠️
**Location**: `src/memory/encrypted_sqlite.py:store_memory()`

**Problem**:
- SQLite connection is opened with `sqlite3.connect()` but only closed if no exception occurs
- If an exception occurs after connection is opened but before `conn.close()`, connection leaks
- Should use context manager (`with sqlite3.connect(...) as conn:`) for automatic cleanup

**Impact**: Resource leak under error conditions, could eventually exhaust connection pool

**Current Code**:
```python
conn = sqlite3.connect(str(self.db_path))
cursor = conn.cursor()
# ... operations ...
conn.commit()
conn.close()  # Only called if no exception
```

### 2. SQLite Connection in _init_database - Same Issue
**Location**: `src/memory/encrypted_sqlite.py:_init_database()`

**Problem**:
- Same issue - connection opened but may not close on exception
- Though less critical (only called once at init), still best practice to use context manager

### 3. Error Handling in _generate_response - Missing Try/Except
**Location**: `src/core/janet_core.py:_generate_response()`

**Problem**:
- Method calls `delegation_manager.delegate_to_model()` without try/except
- If delegation raises exception, it propagates up
- Currently caught in conversation_loop, but better to handle at source

**Impact**: Exception bubbles up unnecessarily, less clear error messages

**Note**: This is partially mitigated by error handling in conversation_loop, but could be improved.

### 4. Conversation Loop Return Value Logic Issue
**Location**: `src/core/conversation_loop.py:run_conversation_loop()`

**Problem**:
- Line 314 in main.py has: `else: continue` - this should never happen
- If `result` is False, loop would continue indefinitely in conversation_loop
- But conversation_loop always returns True or "quit", never False

**Impact**: Dead code, but no actual bug (code path unreachable)

**Current Code**:
```python
elif result:
    continue
else:
    continue  # Should never happen - result is always Truthy or "quit"
```

### 5. Optional Return Type Not Checked After Memory Search
**Location**: `src/core/context_builder.py:build_context()`

**Problem**:
- `memory_manager.search()` can return empty list (handled) but also could return None if it fails
- Currently returns [] on error, so this is OK, but worth noting

**Status**: ✅ Already handled correctly - search() returns [] on error

### 6. Voice Mode Detection - Potential Race Condition
**Location**: `src/core/conversation_loop.py:82-89`

**Problem**:
- When switching to voice mode, `_initialize_voice()` is called
- But `janet.voice_mode` is set to True before checking if initialization succeeds
- If initialization fails, voice_mode is True but voice isn't available

**Impact**: Inconsistent state

**Current Code**:
```python
janet.voice_mode = True  # Set before checking
janet._initialize_voice()  # May fail
```

### 7. Error Handling in process_input - Missing Try/Except
**Location**: `src/core/janet_core.py:process_input()`

**Problem**:
- Method calls `_generate_response()` without try/except
- However, this method is not currently called from conversation_loop (converse is used instead)
- Still worth adding error handling for robustness

**Status**: ⚠️ Low priority - method exists but may not be actively used

### 8. SQLite Database Operations - Missing Error Handling in Some Methods
**Location**: `src/memory/encrypted_sqlite.py`

**Problem**:
- `get_recent_memories()`, `get_weekly_summaries()`, `delete_memory()` may not have comprehensive error handling
- Need to verify all database operations handle errors properly

**Status**: ⚠️ Need to verify

### 9. Main Loop Exception Handling - Potential Issue
**Location**: `src/main.py:298-325`

**Problem**:
- Exception caught in main loop, but if exception occurs, it continues the loop
- If the same error keeps occurring, loop becomes infinite
- Should maybe break or limit retries

**Impact**: Could get stuck in error loop

**Current Code**:
```python
except Exception as e:
    print(f"\n❌ Error: {e}")
    traceback.print_exc()
    if not janet.red_thread_active:
        print("Type 'red thread' if you need to stop everything.")
    # Loop continues - could be infinite if error persists
```

## Recommendations

### High Priority
1. **Fix SQLite connection resource leaks** - Use context managers for all SQLite connections
2. **Fix voice mode state consistency** - Only set voice_mode to True after successful initialization

### Medium Priority
3. **Add error handling to _generate_response** - Catch delegation errors at source
4. **Improve main loop error handling** - Add retry limit or break on persistent errors
5. **Verify all SQLite operations have error handling** - Review all database methods

### Low Priority
6. **Remove dead code** - The `else: continue` in main.py line 314
7. **Add error handling to process_input** - Even if not actively used

## Summary

Most issues are minor and relate to resource management and error handling robustness. The system should work correctly as-is, but these improvements would make it more resilient.

Key findings:
- ✅ Syntax is correct (all files compile)
- ✅ Core error handling is in place
- ✅ Resource leaks fixed in SQLite operations (now using context managers)
- ✅ Voice mode state consistency fixed
- ✅ Error handling improved in _generate_response

## Fixes Applied

### 1. SQLite Connection Resource Leaks ✅ FIXED
- All SQLite connections now use context managers (`with sqlite3.connect(...) as conn:`)
- Automatic cleanup on exceptions
- Applied to: `store_memory()`, `_init_database()`, `get_recent_memories()`, `delete_memory()`, `delete_all_memories()`, `store_weekly_summary()`, `get_weekly_summaries()`

### 2. Voice Mode State Consistency ✅ FIXED
- Now only sets `voice_mode = True` after successful initialization
- Checks if STT is available before switching modes
- Proper error handling with user feedback

### 3. Error Handling in _generate_response ✅ FIXED
- Added try/except around delegation calls
- Falls back gracefully to default response on delegation failures
- Clear error messages

### 4. SQLite Error Handling ✅ ENHANCED
- All SQLite operations now have comprehensive error handling
- Returns appropriate defaults (empty lists, False, 0) on errors
- Clear error messages for debugging

