import os
import tkinter as tk
from tkinter import ttk, filedialog
from pytube import YouTube, Playlist
import threading
import string
import clipboard

# Global flag to indicate if the process should be canceled
CANCEL_FLAG = False

def remove_invalid_chars(filename):
    valid_chars = "-_.() %s%s" % (string.ascii_letters, string.digits)
    cleaned_filename = ''.join(c for c in filename if c in valid_chars)
    return cleaned_filename


def get_default_output_path():
    return os.path.join(os.path.expanduser("~"), "Music")


def extract_artist_and_title(video_title, channel_name):
    # Try to split the video title by '-' and strip any leading/trailing whitespaces
    title_parts = video_title.split('-', 1)
    if len(title_parts) == 2:
        artist = title_parts[0].strip()
        title = title_parts[1].strip()
    else:
        # If no artist found, use the channel name
        artist = channel_name.strip()
        title = video_title.strip()

    return artist, title

def download_youtube_video(url, output_path, progress_var, completion_label):
    global CANCEL_FLAG

    try:
        yt = YouTube(url)
    except Exception as e:
        completion_label.config(text=f"Invalid YouTube URL.")
        return

    video_stream = yt.streams.filter(only_audio=True).first()
    if not video_stream:
        completion_label.config(text=f"No audio stream found for the video.")
        return

    video_title = yt.title
    channel_name = yt.author

    # Extract artist and title from the video title and channel name
    artist, title = extract_artist_and_title(video_title, channel_name)

    # Combine the artist and title to form the MP3 filename
    mp3_filename = remove_invalid_chars(f"{artist} - {title}.mp3")
    mp3_filepath = os.path.join(output_path, mp3_filename)

    if os.path.exists(mp3_filepath):
        completion_label.config(text=f"Warning: Duplicate file found! Skipping download for: {mp3_filename}")
        return

    try:
        video_stream.download(output_path)
    except Exception as e:
        print(f"Error occurred while downloading video: {url}")
        print(f"Error message: {str(e)}")
        completion_label.config(text=f"Error occurred while downloading video.")
        return

    # Rename the downloaded audio file to the MP3 filename
    os.rename(os.path.join(output_path, video_stream.default_filename), mp3_filepath)

    completion_label.config(text=f"Download completed! MP3 file saved as: {mp3_filename}")

    progress_var.set(0)
    
def download_youtube_playlist(playlist_url, output_path, progress_var, completion_label):
    global CANCEL_FLAG

    playlist = Playlist(playlist_url)
    total_videos = len(playlist.video_urls)
    progress_var.set(0)

    # Get the title of the playlist
    playlist_title = remove_invalid_chars(playlist.title)
    
    # Create a folder for the playlist
    playlist_folder_path = os.path.join(output_path, playlist_title)
    os.makedirs(playlist_folder_path, exist_ok=True)

    completion_label.config(text=f"Downloading playlist: {playlist.title}")
    for index, url in enumerate(playlist.video_urls, 1):
        if CANCEL_FLAG:
            completion_label.config(text="Process canceled by user.")
            return

        try:
            download_youtube_video(url, playlist_folder_path, progress_var, completion_label)
        except Exception as e:
            print(f"Error occurred while downloading video: {url}")
            print(f"Error message: {str(e)}")

        progress_var.set(int((index / total_videos) * 100))
        root.update_idletasks()

    completion_label.config(text="Playlist download completed!")

def browse_save_location():
    save_location = filedialog.askdirectory(initialdir=get_default_output_path())
    entry_save_location.delete(0, tk.END)
    entry_save_location.insert(0, save_location)
    
def paste_url(event):
    url = clipboard.paste()
    entry_url.delete(0, tk.END)
    entry_url.insert(0, url)


def download_button_clicked():
    global CANCEL_FLAG

    url = entry_url.get()
    output_directory = entry_save_location.get()
    CANCEL_FLAG = False

    try:
        progress_var.set(0)
        completion_label.config(text="")
        if "/playlist?list=" in url:
            # Create a new thread for the downloading process
            download_thread = threading.Thread(target=download_youtube_playlist,
                                               args=(url, output_directory, progress_var, completion_label))
        else:
            download_thread = threading.Thread(target=download_youtube_video,
                                               args=(url, output_directory, progress_var, completion_label))

        download_thread.start()

    except Exception as e:
        completion_label.config(text=f"Error occurred: {str(e)}")

def cancel_button_clicked():
    global CANCEL_FLAG
    CANCEL_FLAG = True
    completion_label.config(text="Cancel button pressed. Cancelling...")

def reset():
    entry_save_location.delete(0, tk.END)
    entry_save_location.insert(0, get_default_output_path())
    entry_url.delete(0, tk.END)
    progress_var.set(0)
    completion_label.config(text="")

def open_info_window():
    info_window = tk.Toplevel(root)
    info_window.title("Info")
    info_window.geometry("500x400")
    info_window.configure(bg='#2b2b2b')

    info_text = """
    YouTube Audio Downloader

    This application allows you to download audio from YouTube videos
    or entire playlists. Simply enter the YouTube URL (for a single
    video) or Playlist URL, choose the download location, and click
    the 'Download' button.

    Developed by: [Ben Banks]
    Version: 1.3.1
    """

    info_label = tk.Label(info_window, text=info_text, foreground='white', background='#2b2b2b', font=("Helvetica", 12), justify=tk.LEFT)
    info_label.pack(padx=10, pady=10)

# Create the main window
root = tk.Tk()
root.title("YouTube Audio Downloader")

# Set window size and position
win_width = 670
win_height = 350
screen_width = root.winfo_screenwidth()
screen_height = root.winfo_screenheight()
x_offset = (screen_width - win_width) // 2
y_offset = (screen_height - win_height) // 2
root.geometry(f"{win_width}x{win_height}+{x_offset}+{y_offset}")

# Dark theme color scheme with darker gray
root.configure(bg='#2b2b2b')
style = ttk.Style()
style.theme_use('clam')  # Choose the closest available theme for the widgets

# Configure colors for labels, entries, and buttons
dark_gray = '#1e1e1e'
light_gray = '#363636'
white = 'white'
blue = '#0080ff'
style.configure("TLabel", foreground=white, background=dark_gray, font=("Helvetica", 12))
style.configure("TEntry", foreground='black', background=light_gray, font=("Helvetica", 12))
style.configure("TButton", foreground=white, background=blue, font=("Helvetica", 12), width=12)

# Map colors for active and pressed states of buttons
style.map("TButton",
          foreground=[('active', '!disabled', 'black'), ('pressed', white)],
          background=[('active', '#0059b3'), ('pressed', '#004080')])

# Title and Instructions
title_label = ttk.Label(root, text="YouTube Audio Downloader", foreground=white, background=dark_gray, font=("Helvetica", 18))
title_label.pack(pady=10)

instructions_label = ttk.Label(root, text="Enter the YouTube URL or Playlist URL to download audio.", foreground=white, background=dark_gray, font=("Helvetica", 12))
instructions_label.pack(pady=(0, 10))

# URL Input
label_url = ttk.Label(root, text="YouTube URL:", foreground=white, background=dark_gray, font=("Helvetica", 12))
label_url.pack(pady=5)
entry_url = ttk.Entry(root, width=50)
entry_url.pack()
entry_url.bind("<Button-3>", paste_url)

# Save Location Input
label_save_location = ttk.Label(root, text="Save Location:", foreground=white, background=dark_gray, font=("Helvetica", 12))
label_save_location.pack(pady=5)
entry_save_location = ttk.Entry(root, width=50)
entry_save_location.pack()

# Browse, Download, Cancel, Info, and Restart Buttons
button_frame = ttk.Frame(root)
button_frame.pack(pady=15, fill=tk.X)  # Set fill=tk.X to make buttons expand horizontally

browse_button = ttk.Button(button_frame, text="Browse", command=browse_save_location)
browse_button.pack(side=tk.LEFT, padx=5)

download_button = ttk.Button(button_frame, text="Download", command=download_button_clicked)
download_button.pack(side=tk.LEFT, padx=5)

cancel_button = ttk.Button(button_frame, text="Cancel", command=cancel_button_clicked)
cancel_button.pack(side=tk.LEFT, padx=5)

restart_button = ttk.Button(button_frame, text="Restart", command=reset)
restart_button.pack(side=tk.LEFT, padx=5)

info_button = ttk.Button(button_frame, text="Info", command=open_info_window)
info_button.pack(side=tk.LEFT, padx=5)


# Progress Bar
progress_var = tk.IntVar()
progress_frame = ttk.Frame(root)
progress_frame.pack(fill=tk.X, side=tk.BOTTOM)

progress = ttk.Progressbar(progress_frame, variable=progress_var, maximum=100, style='Horizontal.TProgressbar')
progress.pack(fill=tk.X, padx=10, pady=10)  # Added padding to the progress bar

# Outcome Label
completion_label = ttk.Label(root, text="", foreground='green', background='#2b2b2b', font=("Helvetica", 12))
completion_label.pack(pady=10)

# Set the default save location to the Downloads folder
entry_save_location.insert(0, get_default_output_path())

# Start the GUI main loop
root.mainloop()
