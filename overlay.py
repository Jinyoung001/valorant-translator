import tkinter as tk
import config


def run_overlay_manager(translation_queue):
    """
    Runs the Tkinter event loop in the main thread.
    Polls the queue and shows overlays for new translated chat lines.
    Must be called from the main thread.
    """
    root = tk.Tk()
    root.withdraw()

    def check_queue():
        try:
            while True:
                item = translation_queue.get_nowait()
                _create_overlay(root, item)
        except Exception:
            pass
        root.after(300, check_queue)

    root.after(300, check_queue)
    root.mainloop()


def _create_overlay(root, item):
    """
    Creates a borderless overlay at the chat region position.

    item: {
        'lines':  [{"nickname": str, "translated": str}, ...],
        'region': (x, y, w, h)  ← pixel coordinates
    }
    """
    lines  = item['lines']
    region = item['region']

    display_text = '\n'.join(
        f"{entry['nickname']}: {entry['translated']}" for entry in lines
    )

    win = tk.Toplevel(root)
    win.overrideredirect(True)
    win.attributes("-topmost", True)
    win.attributes("-alpha", config.OVERLAY_ALPHA)
    win.geometry(f"+{region[0]}+{region[1]}")

    label = tk.Label(
        win,
        text=display_text,
        font=("Malgun Gothic", 13, "bold"),
        fg="yellow",
        bg="#1a1a2e",
        wraplength=region[2] - 10,
        justify="left",
        padx=8,
        pady=6,
    )
    label.pack()

    win.after(config.OVERLAY_DURATION * 1000, win.destroy)
