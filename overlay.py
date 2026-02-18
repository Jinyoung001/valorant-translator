import tkinter as tk
import config


def run_overlay_manager(translation_queue):
    """
    Runs the Tkinter event loop in the main thread.
    Polls the translation queue every 300ms and shows an overlay for each result.
    Must be called from the main thread.
    """
    root = tk.Tk()
    root.withdraw()  # Hide the invisible root window

    def check_queue():
        try:
            while True:
                text = translation_queue.get_nowait()
                _create_overlay(root, text)
        except Exception:
            pass
        root.after(300, check_queue)

    root.after(300, check_queue)
    root.mainloop()


def _create_overlay(root, text):
    """
    Creates a borderless, always-on-top overlay positioned at the chat region.
    Auto-closes after OVERLAY_DURATION seconds.
    """
    win = tk.Toplevel(root)
    win.overrideredirect(True)
    win.attributes("-topmost", True)
    win.attributes("-alpha", config.OVERLAY_ALPHA)

    # Position the overlay at the same location as the chat region
    x = config.CHAT_REGION[0]
    y = config.CHAT_REGION[1]
    win.geometry(f"+{x}+{y}")

    label = tk.Label(
        win,
        text=text,
        font=("Malgun Gothic", 13, "bold"),
        fg="yellow",
        bg="#1a1a2e",
        wraplength=config.CHAT_REGION[2] - 10,  # match chat width
        justify="left",
        padx=8,
        pady=6,
    )
    label.pack()

    win.after(config.OVERLAY_DURATION * 1000, win.destroy)
