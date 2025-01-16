def patch_tkinter():
    """Patch Tkinter for macOS compatibility"""
    import os
    import sys
    
    if sys.platform == "darwin":
        # Set required environment variables
        os.environ['TK_SILENCE_DEPRECATION'] = '1'
        os.environ['SYSTEM_VERSION_COMPAT'] = '0'
        
        # Import and configure Tk
        import tkinter
        
        # Monkey patch the _tkinter module
        def _tk_color(*args, **kwargs):
            try:
                return original_wantobjects(*args, **kwargs)
            except Exception:
                return 0  # Return default system color
                
        original_wantobjects = tkinter._tkinter.wantobjects
        tkinter._tkinter.wantobjects = _tk_color
