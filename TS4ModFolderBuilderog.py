import os
import json
import shutil
import logging
import traceback
import tkinter as tk
from tkinter import messagebox, filedialog, Menu
import sys
from pathlib import Path
from datetime import datetime

# ---------------------------------------------------------------------
# GLOBAL CONFIG / CONSTANTS
# ---------------------------------------------------------------------

# Function to create the logs directory
def create_logs_directory():
    """Creates a 'logs' directory in the script's directory if it doesn't exist."""
    try:
        script_dir = Path(__file__).parent  # Get the directory of the script
        logs_dir = script_dir / "logs"
        logs_dir.mkdir(exist_ok=True)  # Create the directory if it doesn't exist
        return logs_dir
    except OSError as e:
        print(f"Error creating logs directory: {e}")
        return Path(".")  # defaults to the working directory

# Create logs directory and get its path
logs_directory = create_logs_directory()

# Set up logging with both file and console handlers, saving to the logs directory
log_filename = f"mod_builder_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
log_filepath = logs_directory / log_filename  # Use the logs directory

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(log_filepath),  # Log to the file in the logs directory
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

SETTINGS_FILE = "settings.json"
DEFAULT_MAIN_MOD_FOLDER = str(Path.home() / "Documents/Electronic Arts/The Sims 4/Mods")

DEFAULT_SETTINGS = {
    "main_mods_folder": DEFAULT_MAIN_MOD_FOLDER,
    "generated_mods_enabled": False,
    "temp_mod_timer": "Disabled",
    "naming_rules": {
        "no_spaces_folders": False,
        "no_spaces_files": False,
        "convert_spaces_underscores": False
    },
    "show_open_location_prompt": True,
    "show_save_success": True,
    "backup_options": {
        "always_backup": True  # Always backup is True by default
    },
    "init_py_in_scripts": True
}

settings_data = DEFAULT_SETTINGS.copy()

# ---------------------------------------------------------------------
# ERROR HANDLING
# ---------------------------------------------------------------------
def handle_exception(exc_type, exc_value, exc_traceback):
    """Global exception handler to log unhandled exceptions"""
    logger.error("Uncaught exception:", exc_info=(exc_type, exc_value, exc_traceback))
    error_msg = f"An unexpected error occurred:\n{exc_type.__name__}: {exc_value}"
    messagebox.showerror("Error", error_msg)

def safe_operation(func):
    """Decorator for safe operation execution with error handling"""
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            logger.error(f"Error in {func.__name__}:", exc_info=True)
            error_msg = f"Operation failed: {str(e)}"
            messagebox.showerror("Error", error_msg)
            return None
    return wrapper

# ---------------------------------------------------------------------
# HELPER FUNCTIONS
# ---------------------------------------------------------------------
@safe_operation
def load_settings():
    """Load settings from file or return defaults if file is missing/corrupted."""
    global settings_data
    logger.debug("Loading settings...")

    if Path(SETTINGS_FILE).exists():
        try:
            with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
                loaded_settings = json.load(f)
                # Deep merge with defaults to ensure all keys exist
                settings_data = DEFAULT_SETTINGS.copy()
                # Use a loop for better handling of nested dictionaries.
                for key, value in loaded_settings.items():
                    if key in settings_data and isinstance(settings_data[key], dict) and isinstance(value, dict):
                        settings_data[key].update(value)  # Merge nested dictionaries
                    else:
                        settings_data[key] = value # Update top-level keys

                logger.info("Settings loaded successfully")
        except (json.JSONDecodeError, OSError) as e:
            logger.error(f"Failed to load settings: {e}")
            messagebox.showerror("Error", "Settings file is corrupted. Resetting to defaults.")
            settings_data = DEFAULT_SETTINGS.copy()
    else:
        logger.info("No settings file found. Using defaults.")
        settings_data = DEFAULT_SETTINGS.copy()

@safe_operation
def save_settings():
    """Save current settings_data to disk."""
    logger.debug("Saving settings...")
    try:
        # Create backup of current settings file if it exists
        if Path(SETTINGS_FILE).exists():
            backup_file = f"{SETTINGS_FILE}.bak"
            shutil.copy2(SETTINGS_FILE, backup_file)
            logger.debug(f"Created settings backup: {backup_file}")

        with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
            json.dump(settings_data, f, indent=4)
        logger.info("Settings saved successfully")
    except Exception as e:
        logger.error(f"Failed to save settings: {e}")
        raise

def center_window(window, width=500, height=450):
    """Center a Tk window on the screen."""
    try:
        window.update_idletasks()
        screen_width = window.winfo_screenwidth()
        screen_height = window.winfo_screenheight()
        x = (screen_width // 2) - (width // 2)
        y = (screen_height // 2) - (height // 2)
        window.geometry(f"{width}x{height}+{x}+{y}")
    except Exception as e:
        logger.error(f"Failed to center window: {e}")
        window.geometry(f"{width}x{height}")

# ---------------------------------------------------------------------
# ADVANCED SETTINGS WINDOW
# ---------------------------------------------------------------------
@safe_operation
def open_advanced_settings_window(parent):
    """Opens a separate window for advanced settings."""
    logger.debug("Opening advanced settings window")
    try:
        adv_window = tk.Toplevel(parent)
        adv_window.title("Advanced Settings")
        adv_window.protocol("WM_DELETE_WINDOW", lambda: adv_window.destroy())
        center_window(adv_window, 300, 150)

        adv_window.transient(parent)
        adv_window.grab_set()

        lbl_info = tk.Label(
            adv_window,
            text="No advanced settings are available at this time.",
            font=("Arial", 10),
            justify="center"
        )
        lbl_info.pack(pady=20)

        btn_close = tk.Button(
            adv_window,
            text="Close",
            font=("Arial", 10),
            command=lambda: adv_window.destroy()
        )
        btn_close.pack(pady=10)

    except Exception as e:
        logger.error(f"Error creating advanced settings window: {e}")
        raise

# ---------------------------------------------------------------------
# SETTINGS WINDOW
# ---------------------------------------------------------------------
class SettingsWindow:
    def __init__(self, parent):
        self.parent = parent
        self.window = None
        # Add state tracking
        self.is_open = False  # Initialize is_open to False
        self.setup_window()

    def setup_window(self):
        """Create and setup the settings window"""
        # Prevent multiple windows
        if self.is_open:
            self.window.lift()  # Bring existing window to front
            return

        try:
            self.window = tk.Toplevel(self.parent)
            self.is_open = True  # Set is_open to True when window is created

            # Make it modal
            self.window.transient(self.parent)
            self.window.grab_set()

            # Disable parent window while settings is open
            self.parent.wm_attributes("-disabled", True)

            self.window.title("Settings")
            self.window.protocol("WM_DELETE_WINDOW", self.on_closing)
            center_window(self.window, 600, 400)

            self.create_variables()
            self.create_widgets()

            # Wait for this window to close before continuing.  VERY IMPORTANT for modal behavior.
            self.window.wait_window()

            logger.info("Settings window created successfully")
        except Exception as e:
            logger.error(f"Error setting up settings window: {e}")
            self.on_closing() # call on close to reset everything
            raise

    def on_closing(self):
        """Handle window closing"""
        try:
            # Re-enable parent window
            self.parent.wm_attributes("-disabled", False)

            # Restore parent window focus - VERY important for usability
            self.parent.lift()
            self.parent.focus_force()

            # Release modal state and close
            if self.window:
                self.window.grab_release()
                self.window.destroy()

            self.is_open = False  # Reset is_open to False
            self.window = None   # Clear the window reference
        except Exception as e:
            logger.error(f"Error in window closing: {e}")


    def create_variables(self):
        """Create all Tkinter variables for settings"""
        try:
            self.generated_mods_var = tk.BooleanVar(value=settings_data["generated_mods_enabled"])
            self.temp_mod_timer_var = tk.StringVar(value=settings_data["temp_mod_timer"])
            # Main Mods folder is now a string variable
            self.main_mods_folder_var = tk.StringVar(value=settings_data["main_mods_folder"])

            self.no_spaces_folders_var = tk.BooleanVar(value=settings_data["naming_rules"]["no_spaces_folders"])
            self.no_spaces_files_var = tk.BooleanVar(value=settings_data["naming_rules"]["no_spaces_files"])
            self.convert_spaces_underscores_var = tk.BooleanVar(value=settings_data["naming_rules"]["convert_spaces_underscores"])

            self.always_backup_var = tk.BooleanVar(value=settings_data["backup_options"]["always_backup"])
            self.init_py_in_scripts_var = tk.BooleanVar(value=settings_data["init_py_in_scripts"])
        except Exception as e:
            logger.error(f"Error creating settings variables: {e}")
            raise

    def create_widgets(self):
        """Create all widgets for the settings window"""
        try:
            self.create_mod_location_section()
            self.create_naming_rules_section()
            self.create_backup_options_section()
            self.create_init_py_section()
            self.create_buttons_section()

            logger.debug("All settings widgets created successfully")
        except Exception as e:
            logger.error(f"Error creating settings widgets: {e}")
            raise
    def browse_mods_folder(self):
        """Opens a directory selection dialog and updates the main_mods_folder_var."""
        directory = filedialog.askdirectory(initialdir=self.main_mods_folder_var.get())
        if directory:  # Check if the user selected a directory and didn't cancel
            self.main_mods_folder_var.set(directory)

    def create_mod_location_section(self):
        """Create the mod location section"""
        lbl_main_mod = tk.Label(self.window, text="Current Mod Location:", font=("Arial", 12))
        lbl_main_mod.pack(pady=(10, 2))

        # Frame for entry and browse button
        location_frame = tk.Frame(self.window)
        location_frame.pack(pady=(0, 10))

        # Entry (now editable)
        self.main_mod_entry = tk.Entry(location_frame, width=40, font=("Arial", 10), textvariable=self.main_mods_folder_var, justify="center") #added justify
        self.main_mod_entry.pack(side="left", padx=(0, 5))
        self.add_right_click_menu(self.main_mod_entry) # Add right-click menu

        # Browse button
        browse_button = tk.Button(location_frame, text="Browse", font=("Arial", 10), command=self.browse_mods_folder)
        browse_button.pack(side="left")


    def create_naming_rules_section(self):
        """Create the naming rules section"""
        lbl_naming_rules = tk.Label(self.window, text="Naming Rules:", font=("Arial", 10))
        lbl_naming_rules.pack(pady=(10, 2))

        rules_frame = tk.Frame(self.window)
        rules_frame.pack(pady=5)

        tk.Checkbutton(
            rules_frame,
            text="No Spaces in Folders",
            variable=self.no_spaces_folders_var,
            font=("Arial", 10)
        ).grid(row=0, column=0, padx=5, pady=5)

        tk.Checkbutton(
            rules_frame,
            text="No Spaces in Files",
            variable=self.no_spaces_files_var,
            font=("Arial", 10)
        ).grid(row=0, column=1, padx=5, pady=5)

        tk.Checkbutton(
            rules_frame,
            text="Convert Spaces to Underscores",
            variable=self.convert_spaces_underscores_var,
            font=("Arial", 10)
        ).grid(row=0, column=2, padx=5, pady=5)

    def create_backup_options_section(self):
        """Create the backup options section"""
        lbl_backup = tk.Label(self.window, text="Backup Options:", font=("Arial", 10))
        lbl_backup.pack(pady=(10, 2))

        backup_frame = tk.Frame(self.window)
        backup_frame.pack(pady=5)


        tk.Checkbutton(
            backup_frame,
            text="Always Create Backup Mod",
            variable=self.always_backup_var,
            font=("Arial", 10)
        ).pack(side="left", padx=5)

    def create_init_py_section(self):
        """Create the init.py location section"""
        lbl_init_py = tk.Label(self.window, text="File Location Settings:", font=("Arial", 10))
        lbl_init_py.pack(pady=(10, 2))

        init_py_frame = tk.Frame(self.window)
        init_py_frame.pack(pady=5)

        tk.Checkbutton(
            init_py_frame,
            text="Place __init__.py in Scripts folder (if unchecked, goes to main mod folder)",
            variable=self.init_py_in_scripts_var,
            font=("Arial", 10)
        ).pack(pady=5)

    def create_buttons_section(self):
        """Create the buttons section"""
        try:
            btn_frame = tk.Frame(self.window)
            btn_frame.pack(pady=10)

            save_back_frame = tk.Frame(btn_frame)
            save_back_frame.pack(pady=5)

            tk.Button(
                save_back_frame,
                text="Save Settings",
                font=("Arial", 10),
                command=self.save_settings_local,
                width=18
            ).pack(side="left", padx=5)

            tk.Button(
                save_back_frame,
                text="Back",
                font=("Arial", 10),
                command=self.on_closing,
                width=18
            ).pack(side="left", padx=5)

            tk.Button(
                btn_frame,
                text="Advanced Settings",
                font=("Arial", 10),
                command=lambda: open_advanced_settings_window(self.window),
                width=18
            ).pack(pady=5)

            logger.debug("Settings window buttons created successfully")
        except Exception as e:
            logger.error(f"Error creating settings buttons: {e}")
            raise
    def add_right_click_menu(self, widget):
        """Adds a right-click menu for copy and paste to a widget."""
        menu = Menu(widget, tearoff=0)
        menu.add_command(label="Copy", command=lambda: self.copy_text(widget))
        menu.add_command(label="Paste", command=lambda: self.paste_text(widget))

        def show_menu(event):
            """Displays the right-click menu."""
            try:
                menu.tk_popup(event.x_root, event.y_root)
            finally:
                menu.grab_release()

        widget.bind("<Button-3>", show_menu) # Bind to right-click

    def copy_text(self, widget):
        """Copies text from a widget to the clipboard."""
        try:
            self.window.clipboard_clear()
            self.window.clipboard_append(widget.get())
        except tk.TclError:
            pass  # Ignore if clipboard operations fail

    def paste_text(self, widget):
        """Pastes text from the clipboard into a widget."""
        try:
            widget.insert(tk.INSERT, self.window.clipboard_get())
        except tk.TclError:
            pass # Ignore if clipboard operation fails.

    @safe_operation
    def save_settings_local(self):
        """Save all settings and handle the success message."""
        logger.debug("Saving settings locally...")
        try:
            settings_data["generated_mods_enabled"] = self.generated_mods_var.get()
            settings_data["temp_mod_timer"] = self.temp_mod_timer_var.get()
            # save main mods folder setting
            settings_data["main_mods_folder"] = self.main_mods_folder_var.get()

            settings_data["naming_rules"]["no_spaces_folders"] = self.no_spaces_folders_var.get()
            settings_data["naming_rules"]["no_spaces_files"] = self.no_spaces_files_var.get()
            settings_data["naming_rules"]["convert_spaces_underscores"] = self.convert_spaces_underscores_var.get()

            settings_data["backup_options"]["always_backup"] = self.always_backup_var.get()

            settings_data["init_py_in_scripts"] = self.init_py_in_scripts_var.get()

            save_settings()

            if settings_data.get("show_save_success", True):
                # Create a new top-level window for the message box
                prompt_window = tk.Toplevel(self.window)
                prompt_window.title("Success")
                prompt_window.transient(self.window)
                prompt_window.grab_set()
                self.window.wm_attributes("-disabled", True)
                center_window(prompt_window, 250, 150)

                # Handle window close button
                prompt_window.protocol("WM_DELETE_WINDOW", lambda: self.close_save_prompt(prompt_window))

                tk.Label(prompt_window, text="Settings saved successfully.", font=("Arial", 10)).pack(pady=10)

                dont_show_again_var = tk.BooleanVar(value=False)
                tk.Checkbutton(prompt_window, text="Don't show again", variable=dont_show_again_var, font=("Arial", 10)).pack(pady=5)

                def on_ok():
                    self.close_save_prompt(prompt_window, dont_show_again_var.get())

                tk.Button(prompt_window, text="OK", font=("Arial", 10), command=on_ok).pack(pady=5)
                prompt_window.wait_window() # Waits for the window to close.
            self.on_closing()
            logger.info("Settings saved and window closed")
        except Exception as e:
            logger.error(f"Error saving settings: {e}")
            raise

    def close_save_prompt(self, window, save_setting=False):
        """Helper function to close save prompt"""
        try:
            if save_setting:
                settings_data["show_save_success"] = False
                save_settings()

            self.window.wm_attributes("-disabled", False)  # Re-enable parent
            self.window.lift()
            self.window.focus_force()
            window.grab_release()
            window.destroy()

        except Exception as e:
            logger.error(f"Error closing save prompt window: {e}")

# ---------------------------------------------------------------------
# MAIN APPLICATION WINDOW
# ---------------------------------------------------------------------
class ModBuilderApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Sims 4 Mod Folder Builder")
        center_window(self.root, 400, 350)

        # Add state tracking for settings window
        self.settings_window = None
        # Add state tracking for syncing
        self.syncing = False

        self.create_variables()
        self.create_widgets()
        self.setup_close_handling()  # Call the close handling setup

    def setup_close_handling(self):
        """Sets up the protocol for handling the main window's close button."""
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

    def on_closing(self):
        """Handles the main application window closing."""
        logger.info("Closing application...")
        try:
            # Destroy all windows and exit the application.
            self.root.destroy()
            logger.info("Application closed.")
            sys.exit(0)  # Ensure the process exits completely.
        except Exception as e:
            logger.error(f"Error during application closing: {e}")
            # Even if there's an error, still try to exit.
            sys.exit(1)


    @safe_operation
    def open_settings(self):
        """Open the settings window"""
        try:
            # Prevent multiple settings windows
            if self.settings_window and self.settings_window.is_open:
                self.settings_window.window.lift()
                return

            self.settings_window = SettingsWindow(self.root)
            logger.info("Settings window opened successfully")
        except Exception as e:
            logger.error(f"Failed to open settings window: {e}")
            # Ensure cleanup if error occurs
            if self.settings_window:
                self.settings_window.on_closing()
            self.settings_window = None
            raise

    @safe_operation
    def open_file_location_prompt(self, folder_path):
        """Show prompt to open file location"""
        # Check if the prompt is already open
        if hasattr(self, 'file_location_prompt_open') and self.file_location_prompt_open:
            return

        self.file_location_prompt_open = True  # Set the flag

        try:
            prompt_window = tk.Toplevel(self.root)
            prompt_window.title("Open File Location?")

            # Make it modal
            prompt_window.transient(self.root)
            prompt_window.grab_set()

            # Disable parent window
            self.root.wm_attributes("-disabled", True)

            center_window(prompt_window, 300, 150)

            # Handle window close button (X)
            prompt_window.protocol("WM_DELETE_WINDOW",
                lambda: self.close_prompt(prompt_window))

            tk.Label(
                prompt_window,
                text="Your mod has been generated.\nOpen file location now?",
                font=("Arial", 10),
                justify="center"
            ).pack(pady=10)

            dont_show_again_var = tk.BooleanVar(value=False)

            tk.Checkbutton(
                prompt_window,
                text="Don't show again",
                variable=dont_show_again_var,
                font=("Arial", 10)
            ).pack(pady=5)

            def on_yes():
                try:
                    os.startfile(folder_path)
                except Exception as e:
                    logger.error(f"Could not open file location: {e}")
                    messagebox.showerror("Error", f"Could not open folder: {str(e)}")
                finally:
                    self.close_prompt(prompt_window, dont_show_again_var.get())

            def on_no():
                self.close_prompt(prompt_window, dont_show_again_var.get())

            btn_frame = tk.Frame(prompt_window)
            btn_frame.pack(pady=5)

            tk.Button(
                btn_frame,
                text="Yes",
                font=("Arial", 10),
                command=on_yes,
                width=8
            ).pack(side="left", padx=5)

            tk.Button(
                btn_frame,
                text="No",
                font=("Arial", 10),
                command=on_no,
                width=8
            ).pack(side="left", padx=5)

            # Wait for this window to close before continuing
            prompt_window.wait_window()

            logger.debug("File location prompt created successfully")
        except Exception as e:
            logger.error(f"Error creating file location prompt: {e}")
            self.close_prompt(prompt_window)
            raise
        finally:
            self.file_location_prompt_open = False  # Reset the flag

    def close_prompt(self, window, save_setting=False):
        """Helper to properly close prompt windows"""
        try:
            if save_setting:
                settings_data["show_open_location_prompt"] = False
                save_settings()

            # Re-enable parent window
            self.root.wm_attributes("-disabled", False)

            # Restore parent window focus
            self.root.lift()
            self.root.focus_force()

            # Release modal state and close
            if window:
                window.grab_release()
                window.destroy()
        except Exception as e:
            logger.error(f"Error closing prompt: {e}")

    def create_variables(self):
        """Initialize all Tkinter variables"""
        self.folder_name_var = tk.StringVar()
        self.file_name_var = tk.StringVar()
        self.match_filename_var = tk.BooleanVar(value=False)

        self.script_var = tk.BooleanVar(value=False)
        self.tuning_var = tk.BooleanVar(value=False)
        self.package_var = tk.BooleanVar(value=False)
        self.all_var = tk.BooleanVar(value=False)

        # Use traces for dynamic updates
        self.folder_name_var.trace_add("write", self.on_folder_name_change)
        self.file_name_var.trace_add("write", self.on_file_name_change)
        self.match_filename_var.trace_add("write", self.on_match_filename_toggle)
        self.all_var.trace_add("write", self.on_all_toggle)

    def create_widgets(self):
        """Create all widgets for the main window"""
        # Mod Folder Section
        tk.Label(self.root, text="Folder Name:", font=("Arial", 10)).pack(pady=(10, 2))
        self.folder_entry = tk.Entry(
            self.root,
            width=40,
            font=("Arial", 10),
            justify="center",
            textvariable=self.folder_name_var
        )
        self.folder_entry.pack(pady=(0, 10))
        self.add_right_click_menu(self.folder_entry) # Add to folder entry

        # Mod Name Section
        tk.Label(self.root, text="File Name:", font=("Arial", 10)).pack(pady=(5, 2))
        self.file_entry = tk.Entry(
            self.root,
            width=40,
            font=("Arial", 10),
            justify="center",
            textvariable=self.file_name_var
        )
        self.file_entry.pack(pady=(0, 10))
        self.add_right_click_menu(self.file_entry)  # Add to file entry


        # Match Filename Checkbox
        tk.Checkbutton(
            self.root,
            text="Match file name to folder name",
            variable=self.match_filename_var,
            font=("Arial", 10)
        ).pack(pady=(5, 10))

        # File Types Section
        tk.Label(self.root, text="File Type(s):", font=("Arial", 10)).pack(pady=(5, 2))

        file_frame = tk.Frame(self.root)
        file_frame.pack(pady=5)

        tk.Checkbutton(
                       file_frame,
            text="Script",
            variable=self.script_var,
            font=("Arial", 10)
        ).pack(side="left", padx=5)

        tk.Checkbutton(
            file_frame,
            text="Tuning",
            variable=self.tuning_var,
            font=("Arial", 10)
        ).pack(side="left", padx=5)

        tk.Checkbutton(
            file_frame,
            text="Package",
            variable=self.package_var,
            font=("Arial", 10)
        ).pack(side="left", padx=5)

        tk.Checkbutton(
            file_frame,
            text="All",
            variable=self.all_var,
            font=("Arial", 10)
        ).pack(side="left", padx=5)

        # Buttons
        tk.Button(
            self.root,
            text="Generate Mod",
            font=("Arial", 10),
            command=self.generate_mod,
            width=20
        ).pack(pady=10)

        tk.Button(
            self.root,
            text="Settings",
            font=("Arial", 10),
            command=self.open_settings,
            width=20
        ).pack(pady=10)
    def add_right_click_menu(self, widget):
        """Adds a right-click menu for copy and paste to a widget."""
        menu = Menu(widget, tearoff=0)
        menu.add_command(label="Copy", command=lambda: self.copy_text(widget))
        menu.add_command(label="Paste", command=lambda: self.paste_text(widget))

        def show_menu(event):
            """Displays the right-click menu."""
            try:
                menu.tk_popup(event.x_root, event.y_root)
            finally:
                menu.grab_release()

        widget.bind("<Button-3>", show_menu) # Bind to right-click

    def copy_text(self, widget):
        """Copies text from a widget to the clipboard."""
        try:
            self.root.clipboard_clear()
            self.root.clipboard_append(widget.get())
        except tk.TclError:
            pass  # Ignore if clipboard operations fail

    def paste_text(self, widget):
        """Pastes text from the clipboard into a widget."""
        try:
            widget.insert(tk.INSERT, self.root.clipboard_get())
        except tk.TclError:
            pass # Ignore if clipboard operation fails.

    def on_folder_name_change(self, *args):
        """Sync folder name to file name if match is checked."""
        if self.syncing:
            return
        if self.match_filename_var.get():
            self.syncing = True
            self.file_name_var.set(self.folder_name_var.get())
            self.syncing = False

    def on_file_name_change(self, *args):
        """Sync file name to folder name if match is checked."""
        if self.syncing:
            return
        if self.match_filename_var.get():
            self.syncing = True
            self.folder_name_var.set(self.file_name_var.get())
            self.syncing = False

    def on_match_filename_toggle(self, *args):
        """Handle match filename checkbox toggle"""
        if self.match_filename_var.get():
            # Sync immediately
            self.syncing = True
            self.file_name_var.set(self.folder_name_var.get())
            self.syncing = False
        else:
                        # Only clear the file name when unchecked.
            self.file_name_var.set("")

    def on_all_toggle(self, *args):
        """Handle All checkbox toggle"""
        if self.all_var.get():
            self.script_var.set(True)
            self.tuning_var.set(True)
            self.package_var.set(True)
        else:
            self.script_var.set(False)
            self.tuning_var.set(False)
            self.package_var.set(False)

    def apply_naming_rules(self, name, is_folder):
        """Applies the naming rules based on the settings."""
        if settings_data["naming_rules"]["no_spaces_folders"] and is_folder:
            name = name.replace(" ", "")
        if settings_data["naming_rules"]["no_spaces_files"] and not is_folder:
            name = name.replace(" ", "")
        if settings_data["naming_rules"]["convert_spaces_underscores"]:
            name = name.replace(" ", "_")
        return name

    @safe_operation
    def generate_mod(self):
        """Generate mod files and structure"""
        try:
            # Get the raw user input (allowing spaces)
            folder_name = self.folder_name_var.get().strip()
            file_name = self.file_name_var.get().strip()

            if not folder_name:
                messagebox.showerror("Error", "No Folder Name specified.")
                return
            if not file_name:
                messagebox.showerror("Error", "No File Name specified.")
                return

            # Apply naming rules *here*, before creating files/folders
            cleaned_folder_name = self.apply_naming_rules(folder_name, is_folder=True)
            cleaned_file_name = self.apply_naming_rules(file_name, is_folder=False)

            # Use main_mods_folder from settings
            main_mods_folder = settings_data["main_mods_folder"]

            # Combine the main mods folder with the *cleaned* folder name
            full_folder_path = os.path.join(main_mods_folder, cleaned_folder_name)

            # Create the main mod folder if it doesn't exist
            os.makedirs(full_folder_path, exist_ok=True)
            logger.info(f"Creating mod in folder: {full_folder_path}")

            created_files = []

            def create_init_py():
                try:
                    if settings_data.get("init_py_in_scripts", True):
                        # Create in Scripts folder (use cleaned folder name)
                        scripts_subfolder = os.path.join(full_folder_path, "Scripts")
                        os.makedirs(scripts_subfolder, exist_ok=True)
                        init_file_path = os.path.join(scripts_subfolder, "__init__.py")
                    else:
                        # Create in main mod folder (use cleaned folder name)
                        init_file_path = os.path.join(full_folder_path, "__init__.py")

                    with open(init_file_path, "w", encoding="utf-8") as f:
                        f.write('# __init__.py - Marks this folder as a Python package.\n')
                    created_files.append(init_file_path)
                    logger.debug(f"Created __init__.py at: {init_file_path}")
                except Exception as e:
                    logger.error(f"Error creating __init__.py: {e}")
                    raise

            def create_modinfo_py():
                try:
                    # Use cleaned file name for modinfo content
                    modinfo_file_path = os.path.join(full_folder_path, "modinfo.py")
                    with open(modinfo_file_path, "w", encoding="utf-8") as f:
                        f.write('modinfo = {\n')
                        f.write(f'    "Name": "{cleaned_file_name}",\n')  # Use cleaned name
                        f.write('    "Author": "YourNameHere",\n')
                        f.write('    "Version": "1.0",\n')
                        f.write('}\n')
                    created_files.append(modinfo_file_path)
                    logger.debug(f"Created modinfo.py at: {modinfo_file_path}")
                except Exception as e:
                    logger.error(f"Error creating modinfo.py: {e}")
                    raise

            # Create subfolders for Scripts / Tuning if selected
            scripts_subfolder = os.path.join(full_folder_path, "Scripts")
            tuning_subfolder = os.path.join(full_folder_path, "Tuning")

            def create_script():
                try:
                    os.makedirs(scripts_subfolder, exist_ok=True)
                    # Apply naming rules to file name *before* creating the file
                    script_file_name = self.apply_naming_rules(file_name, is_folder=False)
                    script_file_path = os.path.join(scripts_subfolder, f"{script_file_name}.py")
                    with open(script_file_path, "w", encoding="utf-8") as f:
                        f.write("# Placeholder script file\n")
                    created_files.append(script_file_path)
                    logger.debug(f"Created script file at: {script_file_path}")
                except Exception as e:
                    logger.error(f"Error creating script file: {e}")
                    raise

            def create_tuning():
                try:
                    os.makedirs(tuning_subfolder, exist_ok=True)
                    # Apply naming rules to tuning file name
                    tuning_file_name = self.apply_naming_rules(file_name, is_folder=False)
                    tuning_file_path = os.path.join(tuning_subfolder, f"{tuning_file_name}.xml")
                    with open(tuning_file_path, "w", encoding="utf-8") as f:
                        f.write("<!-- Placeholder tuning file -->\n")
                    created_files.append(tuning_file_path)
                    logger.debug(f"Created tuning file at: {tuning_file_path}")
                except Exception as e:
                    logger.error(f"Error creating tuning file: {e}")
                    raise

            def create_package():
                try:
                    # Apply naming rules to package file name
                    package_file_name = self.apply_naming_rules(file_name, is_folder=False)
                    package_file_path = os.path.join(full_folder_path, f"{package_file_name}.package")
                    with open(package_file_path, "wb") as f:
                        f.write(b"")  # empty package
                    created_files.append(package_file_path)
                    logger.debug(f"Created package file at: {package_file_path}")
                except Exception as e:
                    logger.error(f"Error creating package file: {e}")
                    raise

            # Create the files based on settings and selections
            create_modinfo_py()

            if self.all_var.get() or self.script_var.get() or settings_data.get("init_py_in_scripts", True):
                create_init_py()

            if self.all_var.get():
                create_script()
                create_tuning()
                create_package()
            else:
                if self.script_var.get():
                    create_script()
                if self.tuning_var.get():
                    create_tuning()
                if self.package_var.get():
                    create_package()

            # Handle backup creation if enabled
            backup_always = settings_data["backup_options"].get("always_backup", True)  # Default to True now
            if backup_always:
                try:
                    backup_folder = full_folder_path + "_Backup"
                    os.makedirs(backup_folder, exist_ok=True)
                    for fpath in created_files:
                        fname = os.path.basename(fpath)
                        backup_path = os.path.join(backup_folder, fname)
                        shutil.copyfile(fpath, backup_path)
                    logger.info(f"Created backup in: {backup_folder}")
                except Exception as e:
                    logger.error(f"Error creating backup: {e}")
                    messagebox.showwarning("Warning", f"Could not create backup: {str(e)}")


            # Show success or no files message
            if not created_files:
                messagebox.showinfo("Generate Mod", "No file type selected. No files created.")
                logger.warning("No files were created - no file types selected")
                return

           # Show file location prompt if enabled
            if settings_data.get("show_open_location_prompt", True):
                self.open_file_location_prompt(full_folder_path)

        except Exception as e:
            logger.error(f"Error in generate_mod: {e}")
            raise

# ---------------------------------------------------------------------
# RUN APPLICATION
# ---------------------------------------------------------------------

if __name__ == "__main__":
    try:
        # Set up error handling
        sys.excepthook = handle_exception

        # Load settings before creating the application
        load_settings()

        # Start the application
        logger.info("Starting Sims 4 Mod Folder Builder")
        logger.info(f"Log file: {log_filepath}")

        root = tk.Tk()
        app = ModBuilderApp(root)
        root.mainloop()
    except Exception as e:
        logger.critical(f"Fatal error: {e}", exc_info=True)
        messagebox.showerror("Critical Error", f"Application failed to start: {str(e)}")
        sys.exit(1)