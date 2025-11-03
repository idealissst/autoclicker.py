import tkinter as tk
from tkinter import messagebox
import pyautogui
import threading
import time
import random
from pynput import mouse, keyboard

class AutoclickerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Autoclicker")
        self.root.geometry("300x400")
        pyautogui.FAILSAFE = True  # Move mouse to top-left to abort
        pyautogui.PAUSE = 0.01  # Small pause for stability

        # Variables
        self.interval_var = tk.StringVar(value="1000")  # Default: 1s
        self.x1_var = tk.StringVar(value="0")
        self.y1_var = tk.StringVar(value="0")
        self.x2_var = tk.StringVar(value=str(pyautogui.size()[0]))  # Screen width
        self.y2_var = tk.StringVar(value=str(pyautogui.size()[1]))  # Screen height
        self.clicks_var = tk.StringVar(value="0")  # 0 = infinite
        self.click_type_var = tk.StringVar(value="left")
        self.is_running = False
        self.capturing = None  # None, 'top-left', or 'bottom-right'

        # GUI Elements
        tk.Label(root, text="Interval (ms):").grid(row=0, column=0, padx=5, pady=5)
        tk.Entry(root, textvariable=self.interval_var).grid(row=0, column=1, padx=5, pady=5)
        tk.Label(root, text="Top-Left X:").grid(row=1, column=0, padx=5, pady=5)
        tk.Entry(root, textvariable=self.x1_var).grid(row=1, column=1, padx=5, pady=5)
        tk.Label(root, text="Top-Left Y:").grid(row=2, column=0, padx=5, pady=5)
        tk.Entry(root, textvariable=self.y1_var).grid(row=2, column=1, padx=5, pady=5)
        tk.Label(root, text="Bottom-Right X:").grid(row=3, column=0, padx=5, pady=5)
        tk.Entry(root, textvariable=self.x2_var).grid(row=3, column=1, padx=5, pady=5)
        tk.Label(root, text="Bottom-Right Y:").grid(row=4, column=0, padx=5, pady=5)
        tk.Entry(root, textvariable=self.y2_var).grid(row=4, column=1, padx=5, pady=5)
        tk.Label(root, text="Clicks (0 = infinite):").grid(row=5, column=0, padx=5, pady=5)
        tk.Entry(root, textvariable=self.clicks_var).grid(row=5, column=1, padx=5, pady=5)
        tk.Label(root, text="Click Type:").grid(row=6, column=0, padx=5, pady=5)
        tk.Radiobutton(root, text="Left", variable=self.click_type_var, value="left").grid(row=6, column=1, padx=5, pady=5)
        tk.Radiobutton(root, text="Right", variable=self.click_type_var, value="right").grid(row=6, column=2, padx=5, pady=5)
        tk.Button(root, text="Start", command=self.start_clicking).grid(row=7, column=0, columnspan=2, pady=10)
        tk.Button(root, text="Stop", command=self.stop_clicking).grid(row=7, column=1, columnspan=2, pady=10)
        tk.Button(root, text="Define Position", command=self.start_capture).grid(row=10, column=0, columnspan=2, pady=5)
        self.status_var = tk.StringVar(value="Idle")
        tk.Label(root, textvariable=self.status_var, fg="blue").grid(row=8, column=0, columnspan=3, pady=10)

        # Start hotkey listener
        self.hotkey_thread = threading.Thread(target=self.watch_hotkey, daemon=True)
        self.hotkey_thread.start()

    def validate_inputs(self):
        try:
            interval = float(self.interval_var.get()) / 1000
            if interval <= 0:
                raise ValueError("Interval must be positive")
            x1 = int(self.x1_var.get())
            y1 = int(self.y1_var.get())
            x2 = int(self.x2_var.get())
            y2 = int(self.y2_var.get())
            screen_width, screen_height = pyautogui.size()
            if x1 < 0 or y1 < 0 or x2 > screen_width or y2 > screen_height:
                raise ValueError("Coordinates out of screen bounds")
            if x1 >= x2 or y1 >= y2:
                raise ValueError("Invalid coordinates: x1 < x2 and y1 < y2 required")
            clicks = int(self.clicks_var.get())
            if clicks < 0:
                raise ValueError("Clicks cannot be negative")
            click_type = self.click_type_var.get()
            if click_type not in ["left", "right"]:
                raise ValueError("Invalid click type")
            return interval, x1, y1, x2, y2, clicks, click_type
        except ValueError as e:
            messagebox.showerror("Input Error", str(e))
            return None

    def autoclick_loop(self):
        inputs = self.validate_inputs()
        if inputs is None:
            self.stop_clicking()
            return
        interval, x1, y1, x2, y2, clicks, click_type = inputs
        count = 0
        while self.is_running and (clicks == 0 or count < clicks):
            x = random.randint(x1, x2)
            y = random.randint(y1, y2)
            try:
                pyautogui.click(x, y, button=click_type)
                count += 1
                self.status_var.set(f"Running... Clicks: {count}")
                self.root.update()
            except pyautogui.FailSafeException:
                self.stop_clicking()
                break
            time.sleep(interval)
        self.stop_clicking()

    def start_clicking(self):
        if not self.is_running and self.capturing is None:
            self.is_running = True
            self.status_var.set("Running...")
            threading.Thread(target=self.autoclick_loop, daemon=True).start()

    def stop_clicking(self):
        self.is_running = False
        self.capturing = None  # Reset capturing state
        self.status_var.set("Idle")

    def start_capture(self):
        if self.is_running:
            messagebox.showwarning("Warning", "Cannot define position while clicking")
            return
        if self.capturing is None:
            self.capturing = 'top-left'
            self.status_var.set("Move mouse and click to set top-left point")
            self.root.update()
            threading.Thread(target=self.listen_for_click, daemon=True).start()
        elif self.capturing == 'top-left':
            self.capturing = 'bottom-right'
            self.status_var.set("Move mouse and click to set bottom-right point")
            self.root.update()
            threading.Thread(target=self.listen_for_click, daemon=True).start()

    def listen_for_click(self):
        def on_click(x, y, button, pressed):
            if pressed and button == mouse.Button.left:
                self.root.after(0, self.set_position, x, y)
                return False  # Stop listener
        with mouse.Listener(on_click=on_click) as listener:
            listener.join()

    def set_position(self, x, y):
        if self.capturing == 'top-left':
            self.x1_var.set(str(int(x)))
            self.y1_var.set(str(int(y)))
            self.start_capture()  # Prompt for bottom-right
        elif self.capturing == 'bottom-right':
            self.x2_var.set(str(int(x)))
            self.y2_var.set(str(int(y)))
            self.capturing = None
            self.status_var.set("Position set. Ready to start.")

    def watch_hotkey(self):
        def on_press(key):
            if key == keyboard.Key.esc and self.is_running:
                self.root.after(0, self.stop_clicking)
                return False  # Stop listener
        with keyboard.Listener(on_press=on_press) as listener:
            listener.join()

if __name__ == "__main__":
    root = tk.Tk()
    app = AutoclickerApp(root)
    root.mainloop()