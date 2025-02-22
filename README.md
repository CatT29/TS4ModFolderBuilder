Sims 4 Mod Folder Builder is a user-friendly, Python-based application designed to streamline the creation of mod folders for The Sims 4. With an intuitive Tkinter GUI, the tool enables modders to generate a well-organized folder structure complete with essential files, such as modinfo.py, init.py, script, tuning, and package files. Built with robust error handling, dynamic logging, and customizable settings, this application simplifies the mod creation process while ensuring backups and user-defined naming rules are seamlessly applied.

Key Features:

Intuitive Graphical Interface:
Easily manage mod folder and file creation with a clean and accessible Tkinter-based GUI.

Automated Folder & File Generation:
Generate a structured mod folder with essential files, including modinfo.py, init.py, and additional script, tuning, and package files based on user selections.

Customizable Naming Rules:
Apply user-defined naming rules—such as removing spaces or converting them to underscores—for both folders and files, ensuring consistency across mods.

Robust Logging & Error Handling:
Automatically create a logs directory and generate timestamped log files to capture both normal operations and error events, helping with troubleshooting.

Configurable Settings:
Load and save settings via a JSON file with defaults provided. The settings include mod folder paths, backup options, and display prompts, with an easy-to-use settings window for quick adjustments.

Backup Functionality:
Automatically create backups of generated mod files to prevent data loss and provide a safety net during development.

Dynamic Syncing:
Option to synchronize folder and file names automatically to ensure consistency when the "Match file name to folder name" feature is enabled.

Advanced Options Window:
A placeholder for future advanced settings, making the tool extensible and adaptable to additional mod-building requirements.

This description and features list should give visitors a clear and detailed overview of your project while highlighting its key benefits and capabilities.

Installation
Clone the Repository:

bash
Copy
git clone https://github.com/YourUsername/Sims4ModFolderBuilder.git
cd Sims4ModFolderBuilder
Ensure Python 3 is Installed:
This application requires Python 3.6+ (Tkinter is included with most Python distributions).

Install Dependencies (if needed):
Most dependencies are part of the standard library. If you require additional libraries, you can install them via pip:

bash
Copy
pip install -r requirements.txt
Usage
Run the Application:

From the project directory, run:

bash
Copy
python mod_builder.py
Using the GUI:

Folder Name & File Name: Input your desired names. Optionally, check "Match file name to folder name" to keep both names in sync.
File Type Options: Choose the file types you wish to generate (Script, Tuning, Package, or All).
Settings: Click the "Settings" button to configure advanced options like mod folder location, naming rules, backup settings, and more.
Generate Mod: Click the "Generate Mod" button to create the mod folder structure. A prompt will appear asking if you'd like to open the mod folder location.
Logs & Settings:

Log files are automatically saved in the logs directory with timestamps.
Settings are stored in a settings.json file, and backups are created as needed.
Configuration
Settings File:
The application uses a settings.json file to store user preferences. If this file does not exist or is corrupted, the application will revert to default settings.

Logs Directory:
A logs directory is created (if not already present) in the same directory as the script to store detailed log files.

Troubleshooting
Application Fails to Start:
Check the log file in the logs directory for error details.

Settings Issues:
If the settings file is corrupted, the application will reset to default settings. You can delete the settings.json file to force a fresh start.

Contributing
Contributions are welcome! Please fork this repository and submit a pull request with your changes. For major changes, please open an issue first to discuss what you would like to change.
