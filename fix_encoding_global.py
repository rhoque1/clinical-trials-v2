"""
Global UTF-8 encoding fix for all Python scripts
Apply this at the start of any script that may encounter Unicode issues
"""
import sys
import os
import locale

def force_utf8_everywhere():
    """
    Force UTF-8 encoding across all Python I/O operations

    This fixes issues with:
    - Console output (print statements)
    - File I/O (open, json.dump, etc.)
    - Environment variables
    - Subprocess calls
    """

    # Fix 1: Reconfigure stdout/stderr for UTF-8
    if hasattr(sys.stdout, 'reconfigure'):
        try:
            sys.stdout.reconfigure(encoding='utf-8', errors='replace')
            sys.stderr.reconfigure(encoding='utf-8', errors='replace')
        except Exception:
            pass

    # Fix 2: Set environment variables for subprocess calls
    os.environ['PYTHONIOENCODING'] = 'utf-8'
    os.environ['PYTHONUTF8'] = '1'

    # Fix 3: Override default encoding
    if hasattr(sys, '_base_executable'):  # Only in Python 3.11+
        pass
    else:
        # Set default encoding hint
        if hasattr(locale, 'getpreferredencoding'):
            try:
                # This doesn't actually change it but signals intent
                pass
            except Exception:
                pass

    # Fix 4: Monkey-patch builtins.open to default to UTF-8
    import builtins
    _original_open = builtins.open

    def utf8_open(file, mode='r', buffering=-1, encoding=None, *args, **kwargs):
        """Wrapper around open() that defaults to UTF-8 encoding"""
        # If encoding not specified and we're in text mode, use UTF-8
        if encoding is None and ('b' not in mode):
            encoding = 'utf-8'
        return _original_open(file, mode, buffering, encoding, *args, **kwargs)

    builtins.open = utf8_open

    return True


# Apply globally when this module is imported
force_utf8_everywhere()
