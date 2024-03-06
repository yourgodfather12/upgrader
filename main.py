import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import os
import subprocess
import threading
import shutil
import logging
import openai

# Configure logging
logging.basicConfig(filename='upgrade.log', level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')

# Define your OpenAI API key
openai.api_key = "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"


def read_scripts_in_folder(folder_path, backup_files=False):
    if not os.path.isdir(folder_path):
        messagebox.showerror("Error", f"{folder_path} is not a valid directory.")
        return

    logging.info(f"Reading scripts in folder: {folder_path}")

    # List to store all script files found
    script_files = []

    # Recursively search through the folder and its subfolders
    for root_dir, _, files in os.walk(folder_path):
        for file_name in files:
            if file_name.endswith(".py"):
                script_files.append(os.path.join(root_dir, file_name))

    logging.info(f"Found {len(script_files)} script files in folder and subfolders.")

    # Check if there are any script files
    if not script_files:
        messagebox.showinfo("Info", "No script files found in the selected folder and its subfolders.")
        return

    # Disable the select folder button
    select_button.config(state="disabled")

    # Clear the preview box
    preview_box.delete("1.0", tk.END)

    # Start a new thread for processing script files
    threading.Thread(target=process_scripts, args=(folder_path, script_files, backup_files)).start()


def process_scripts(folder_path, script_files, backup_files):
    # Initialize progress variables
    total_files = len(script_files)
    processed_files = 0

    for filename in script_files:
        file_path = os.path.join(folder_path, filename)
        # Backup the original file if requested
        if backup_files:
            backup_file(file_path)

        # Read the content of the file
        try:
            with open(file_path, "r", encoding="utf-8") as file:
                script_content = file.read()
                # Apply upgrades or fixes to the script content
                upgraded_content, upgrades_made = upgrade_script(script_content, filename)
                # Write the upgraded content back to the file
                with open(file_path, "w", encoding="utf-8") as file:
                    file.write(upgraded_content)
        except Exception as e:
            error_message = f"Failed to process {filename}: {str(e)}"
            logging.error(error_message)
            messagebox.showerror("Error", error_message)
            preview_box.insert(tk.END, error_message + "\n")
        else:
            status_message = f"Processed: {filename}"
            logging.info(status_message)
            preview_box.insert(tk.END, status_message + "\n")
            if upgrades_made:
                preview_box.insert(tk.END, f"Upgrades made: {', '.join(upgrades_made)}\n\n")
            else:
                preview_box.insert(tk.END, "No upgrades made.\n\n")

        processed_files += 1
        # Update progress
        update_progress(processed_files, total_files)

    # Enable the select folder button
    select_button.config(state="normal")
    messagebox.showinfo("Info", "Script upgrade process completed.")



def backup_file(file_path):
    backup_folder = os.path.join(os.path.dirname(file_path), "backup")
    os.makedirs(backup_folder, exist_ok=True)
    backup_path = os.path.join(backup_folder, os.path.basename(file_path) + ".bak")
    shutil.copy2(file_path, backup_path)


def upgrade_script(script_content, filename):
    upgrades_made = []

    # Apply code formatting using Black for Python scripts
    if filename.endswith(".py"):
        upgraded_content, format_upgrade = format_python_code(script_content)
        if format_upgrade:
            upgrades_made.append("Formatted Python code.")
    else:
        upgraded_content = script_content

    # Use GPT-3 to suggest improvements
    suggested_improvements = suggest_improvements(upgraded_content)
    if suggested_improvements:
        upgraded_content = suggested_improvements
        upgrades_made.append("Suggested improvements using GPT-3.")

    return upgraded_content, upgrades_made


def format_python_code(code):
    try:
        # Call black to format the Python code
        result = subprocess.run(["black", "--quiet", "-"], input=code.encode(), stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE)
        if result.returncode == 0:
            return result.stdout.decode(), True
        else:
            error_message = f"Failed to format Python code: {result.stderr.decode()}"
            logging.error(error_message)
            messagebox.showerror("Error", error_message)
            return code, False
    except FileNotFoundError:
        error_message = "Black is not installed. Please install Black (https://github.com/psf/black) to enable code formatting."
        logging.error(error_message)
        messagebox.showerror("Error", error_message)
        return code, False


def suggest_improvements(script_content):
    try:
        # Use OpenAI's GPT-3 to suggest improvements
        response = openai.Completion.create(
            model="text-davinci-002",
            prompt=f"Here are some improvements for the code:\n\n{script_content}",
            max_tokens=150,
            n=1,
            stop=["\n"]
        )
        return response.choices[0].text.strip()
    except Exception as e:
        error_message = f"Failed to suggest improvements: {str(e)}"
        logging.error(error_message)
        messagebox.showerror("Error", error_message)
        return None



def update_progress(processed_files, total_files):
    progress_value = int(processed_files / total_files * 100)
    progress_bar["value"] = progress_value
    root.update_idletasks()


def select_folder():
    folder_path = filedialog.askdirectory()
    if folder_path:
        backup_var = backup_checkbox_var.get()
        read_scripts_in_folder(folder_path, backup_files=backup_var)


# Create the main application window
root = tk.Tk()
root.title("Script Upgrader")
root.configure(background="#282828")  # Set background color to dark gray

# Configure row and column weights for resizing
root.grid_rowconfigure(0, weight=1)
root.grid_columnconfigure(0, weight=1)

# Create a frame for the content
content_frame = ttk.Frame(root, padding=(20, 10))
content_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

# Create a label to display instructions
instruction_label = ttk.Label(content_frame, text="Select the folder containing scripts to upgrade:", background="#282828", foreground="white")  # Set text color to white
instruction_label.grid(row=0, column=0, columnspan=2, pady=10)

# Create a button to select the folder
select_button = ttk.Button(content_frame, text="Select Folder", command=select_folder)
select_button.grid(row=1, column=0, pady=5)

# Create a progress bar
progress_bar = ttk.Progressbar(content_frame, orient="horizontal", length=200, mode="determinate")
progress_bar.grid(row=1, column=1, pady=5)

# Create a preview box
preview_box = tk.Text(content_frame, height=30, width=100, wrap=tk.WORD)
preview_box.grid(row=2, column=0, columnspan=2, pady=5, sticky=(tk.W, tk.E, tk.N, tk.S))
preview_box.configure(background="#1E1E1E", foreground="white", insertbackground="white")  # Set text and background colors to dark mode
preview_box.tag_configure("bold", font="TkDefaultFont 9 bold")
preview_box.tag_configure("italic", font="TkDefaultFont 9 italic")

# Add scrollbar to the preview box
scrollbar = ttk.Scrollbar(content_frame, command=preview_box.yview)
scrollbar.grid(row=2, column=2, sticky="ns")
preview_box.config(yscrollcommand=scrollbar.set)

# Create a checkbox for backup option
backup_checkbox_var = tk.BooleanVar()
backup_checkbox = ttk.Checkbutton(content_frame, text="Create Backup", variable=backup_checkbox_var)
backup_checkbox_style = ttk.Style()
backup_checkbox_style.configure("Dark.TCheckbutton", background="#282828", foreground="white")  # Set text color to white
backup_checkbox_style.map("Dark.TCheckbutton",
                          background=[('selected', '#282828')],  # Set background color when selected
                          foreground=[('selected', 'white')])    # Set text color when selected
backup_checkbox["style"] = "Dark.TCheckbutton"
backup_checkbox.grid(row=3, column=0, columnspan=2, pady=5)

# Run the Tkinter event loop
root.mainloop()
