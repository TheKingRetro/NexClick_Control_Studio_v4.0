import tkinter as tk
from tkinter import ttk, messagebox
import threading
import time
import random
import sys
import os

try:
    from pynput import mouse, keyboard
except ImportError:
    mouse = keyboard = None

APP_NAME = "NexClick Control Studio"
APP_VERSION = "4.0"


def resource_path(name):
    """Find bundled resources both in source mode and PyInstaller one-file mode."""
    root = getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(root, name)


class NexClickApp:
    BG = "#10141d"
    PANEL = "#191f2b"
    PANEL_2 = "#202838"
    TEXT = "#edf2fa"
    MUTED = "#9aa8bd"
    ACCENT = "#7c5cff"
    ACCENT_HOVER = "#927aff"
    GREEN = "#36d996"
    RED = "#ff667d"
    BORDER = "#2b3547"

    def __init__(self):
        self.root = tk.Tk()
        self.root.title(APP_NAME)
        self.root.geometry("760x760")
        self.root.minsize(700, 700)
        self.root.configure(bg=self.BG)
        try:
            self.root.iconbitmap(resource_path("nexclick.ico"))
        except Exception:
            pass

        self.controller = mouse.Controller() if mouse else None
        self.listener_mouse = None
        self.listener_keyboard = None
        self.worker = None
        self.stop_event = threading.Event()
        self.state_lock = threading.Lock()
        self.running = False
        self.closing = False

        self.recording = False
        self.recorded = []
        self.record_start = 0.0
        self.record_lock = threading.Lock()

        self.hotkey = "F6"
        self.hotkey_mouse_button = None
        self.hotkey_capture_callback = None
        self.pressed_keys = set()
        self.pick_armed = False
        self.overlay_window = None
        self.overlay_visible = True
        self.target_x = 0
        self.target_y = 0

        self.hours = tk.StringVar(value="0")
        self.minutes = tk.StringVar(value="0")
        self.seconds = tk.StringVar(value="0")
        self.millis = tk.StringVar(value="100")
        self.random_on = tk.BooleanVar(value=False)
        self.random_ms = tk.StringVar(value="0")
        self.mouse_button = tk.StringVar(value="Left")
        self.click_type = tk.StringVar(value="Single")
        self.repeat_mode = tk.StringVar(value="until")
        self.repeat_count = tk.IntVar(value=1)
        self.use_current = tk.BooleanVar(value=True)
        self.status = tk.StringVar(value="READY")
        self._setup_styles()
        self._build_ui()
        self._start_listeners()
        self.root.protocol("WM_DELETE_WINDOW", self.close)

    def _setup_styles(self):
        style = ttk.Style(self.root)
        try:
            style.theme_use("clam")
        except tk.TclError:
            pass
        style.configure(".", font=("Segoe UI", 10))
        style.configure("TFrame", background=self.BG)
        style.configure("Panel.TFrame", background=self.PANEL)
        style.configure("TLabel", background=self.BG, foreground=self.TEXT)
        style.configure("Muted.TLabel", background=self.BG, foreground=self.MUTED)
        style.configure("Panel.TLabel", background=self.PANEL, foreground=self.TEXT)
        style.configure("PanelMuted.TLabel", background=self.PANEL, foreground=self.MUTED)
        style.configure("TLabelframe", background=self.PANEL, foreground=self.TEXT, bordercolor=self.BORDER)
        style.configure("TLabelframe.Label", background=self.PANEL, foreground=self.MUTED, font=("Segoe UI", 9, "bold"))
        style.configure("TEntry", fieldbackground=self.PANEL_2, foreground=self.TEXT, insertcolor=self.TEXT, bordercolor=self.BORDER, padding=6)
        style.configure("TCombobox", fieldbackground=self.PANEL_2, background=self.PANEL_2, foreground=self.TEXT, arrowcolor=self.TEXT, padding=5)
        style.map("TCombobox", fieldbackground=[("readonly", self.PANEL_2)], foreground=[("readonly", self.TEXT)])
        style.configure("TSpinbox", fieldbackground=self.PANEL_2, foreground=self.TEXT, arrowcolor=self.TEXT, padding=5)
        style.configure("TCheckbutton", background=self.PANEL, foreground=self.TEXT)
        style.map("TCheckbutton", background=[("active", self.PANEL)], foreground=[("active", self.TEXT)])
        style.configure("TRadiobutton", background=self.PANEL, foreground=self.TEXT)
        style.map("TRadiobutton", background=[("active", self.PANEL)], foreground=[("active", self.TEXT)])
        style.configure("TButton", background=self.PANEL_2, foreground=self.TEXT, bordercolor=self.BORDER, padding=(10, 8))
        style.map("TButton", background=[("active", "#303b50"), ("disabled", "#202531")], foreground=[("disabled", "#69758a")])
        style.configure("Accent.TButton", background=self.ACCENT, foreground="#ffffff", bordercolor=self.ACCENT, font=("Segoe UI", 10, "bold"), padding=(12, 10))
        style.map("Accent.TButton", background=[("active", self.ACCENT_HOVER)])
        style.configure("Danger.TButton", background="#3a202d", foreground="#ff9bab", bordercolor="#613042", padding=(12, 10))
        style.map("Danger.TButton", background=[("active", "#4b2737")])

    def _build_ui(self):
        header = tk.Frame(self.root, bg=self.BG, padx=22, pady=18)
        header.pack(fill="x")
        logo = tk.Canvas(header, width=48, height=48, bg=self.BG, highlightthickness=0)
        logo.pack(side="left", padx=(0, 12))
        logo.create_oval(3, 3, 45, 45, fill=self.ACCENT, outline="")
        logo.create_polygon(18, 12, 18, 36, 36, 24, fill="#ffffff", outline="")
        titlebox = tk.Frame(header, bg=self.BG)
        titlebox.pack(side="left", fill="x", expand=True)
        tk.Label(titlebox, text="NEXCLICK", bg=self.BG, fg=self.TEXT, font=("Segoe UI", 17, "bold")).pack(anchor="w")
        tk.Label(titlebox, text="CONTROL STUDIO  •  v" + APP_VERSION, bg=self.BG, fg=self.MUTED, font=("Segoe UI", 9, "bold")).pack(anchor="w", pady=(1, 0))
        self.status_pill = tk.Label(header, text="● READY", bg="#202838", fg=self.GREEN, font=("Segoe UI", 9, "bold"), padx=12, pady=7)
        self.status_pill.pack(side="right")

        body = tk.Frame(self.root, bg=self.BG, padx=20)
        body.pack(fill="both", expand=True)

        interval = ttk.LabelFrame(body, text="  TIMING  ", padding=12)
        interval.pack(fill="x", pady=(0, 10))
        fields = [(self.hours, "HOURS"), (self.minutes, "MINUTES"), (self.seconds, "SECONDS"), (self.millis, "MILLISECONDS")]
        for i, (var, label) in enumerate(fields):
            cell = tk.Frame(interval, bg=self.PANEL)
            cell.grid(row=0, column=i, sticky="ew", padx=(0 if i == 0 else 7, 0))
            ttk.Label(cell, text=label, style="PanelMuted.TLabel", font=("Segoe UI", 8, "bold")).pack(anchor="w", pady=(0, 5))
            ttk.Entry(cell, textvariable=var, width=10, justify="center").pack(fill="x")
            interval.columnconfigure(i, weight=1)
        ttk.Checkbutton(interval, text="Random offset ±", variable=self.random_on).grid(row=1, column=0, sticky="w", pady=(12, 0))
        ttk.Entry(interval, textvariable=self.random_ms, width=9).grid(row=1, column=1, sticky="w", pady=(12, 0))
        ttk.Label(interval, text="milliseconds", style="PanelMuted.TLabel").grid(row=1, column=2, sticky="w", pady=(12, 0))

        row = tk.Frame(body, bg=self.BG)
        row.pack(fill="x", pady=(0, 10))
        options = ttk.LabelFrame(row, text="  CLICK OPTIONS  ", padding=12)
        options.pack(side="left", fill="both", expand=True, padx=(0, 5))
        ttk.Label(options, text="Mouse button", style="PanelMuted.TLabel").grid(row=0, column=0, sticky="w", pady=5)
        ttk.Combobox(options, textvariable=self.mouse_button, values=("Left", "Right", "Middle", "X1", "X2"), state="readonly", width=13).grid(row=0, column=1, sticky="ew", padx=(12, 0))
        ttk.Label(options, text="Click type", style="PanelMuted.TLabel").grid(row=1, column=0, sticky="w", pady=5)
        ttk.Combobox(options, textvariable=self.click_type, values=("Single", "Double"), state="readonly", width=13).grid(row=1, column=1, sticky="ew", padx=(12, 0))
        options.columnconfigure(1, weight=1)

        repeat = ttk.LabelFrame(row, text="  REPEAT  ", padding=12)
        repeat.pack(side="left", fill="both", expand=True, padx=(5, 0))
        ttk.Radiobutton(repeat, text="Fixed number", variable=self.repeat_mode, value="count").grid(row=0, column=0, sticky="w")
        ttk.Spinbox(repeat, from_=1, to=1000000, textvariable=self.repeat_count, width=9).grid(row=0, column=1, padx=(10, 0))
        ttk.Radiobutton(repeat, text="Until stopped", variable=self.repeat_mode, value="until").grid(row=1, column=0, columnspan=2, sticky="w", pady=(10, 0))

        position = ttk.LabelFrame(body, text="  CURSOR POSITION  ", padding=12)
        position.pack(fill="x", pady=(0, 10))
        ttk.Radiobutton(position, text="Current cursor", variable=self.use_current, value=True, command=self._position_mode).grid(row=0, column=0, sticky="w")
        ttk.Radiobutton(position, text="Fixed coordinates", variable=self.use_current, value=False, command=self._position_mode).grid(row=0, column=1, sticky="w", padx=(15, 0))
        ttk.Button(position, text="Pick on screen", command=self.arm_pick).grid(row=0, column=2, padx=(12, 0))
        ttk.Label(position, text="X", style="PanelMuted.TLabel").grid(row=0, column=3, padx=(12, 4))
        self.x_entry = ttk.Entry(position, width=7, justify="center")
        self.x_entry.insert(0, "0")
        self.x_entry.grid(row=0, column=4)
        ttk.Label(position, text="Y", style="PanelMuted.TLabel").grid(row=0, column=5, padx=(10, 4))
        self.y_entry = ttk.Entry(position, width=7, justify="center")
        self.y_entry.insert(0, "0")
        self.y_entry.grid(row=0, column=6)
        self.pick_hint = ttk.Label(position, text="Current cursor position will be used.", style="PanelMuted.TLabel")
        self.pick_hint.grid(row=1, column=0, columnspan=7, sticky="w", pady=(10, 0))

        controls = tk.Frame(body, bg=self.BG)
        controls.pack(fill="x", pady=(2, 10))
        self.start_btn = ttk.Button(controls, text="▶  START  (F6)", style="Accent.TButton", command=self.start)
        self.start_btn.pack(side="left", fill="x", expand=True, padx=(0, 5))
        self.stop_btn = ttk.Button(controls, text="■  STOP  (F6)", style="Danger.TButton", command=self.stop, state="disabled")
        self.stop_btn.pack(side="left", fill="x", expand=True, padx=(5, 0))

        tools = tk.Frame(body, bg=self.BG)
        tools.pack(fill="x", pady=(0, 10))
        ttk.Button(tools, text="⌨  Hotkey settings", command=self.set_hotkey).pack(side="left", fill="x", expand=True, padx=(0, 5))
        ttk.Button(tools, text="●  Record & playback", command=self.record_window).pack(side="left", fill="x", expand=True, padx=(5, 0))

        overlay = ttk.LabelFrame(body, text="  SCREEN OVERLAY  ", padding=10)
        overlay.pack(fill="x", pady=(0, 12))
        self.overlay_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(overlay, text="Keep status indicator above other windows", variable=self.overlay_var, command=self.toggle_overlay).pack(side="left")
        ttk.Button(overlay, text="Move to corner", command=self.move_overlay).pack(side="right")

        footer = tk.Frame(self.root, bg=self.PANEL, padx=20, pady=10)
        footer.pack(fill="x", side="bottom")
        tk.Label(footer, text="NEXCLICK  /  BUILT FOR WINDOWS", bg=self.PANEL, fg=self.MUTED, font=("Segoe UI", 8, "bold")).pack(side="left")
        tk.Label(footer, text="X1 / X2  •  GLOBAL HOTKEYS", bg=self.PANEL, fg=self.MUTED, font=("Segoe UI", 8)).pack(side="right")
        self._create_overlay()

    def _create_overlay(self):
        w = tk.Toplevel(self.root)
        w.title("NexClick status")
        w.overrideredirect(True)
        w.attributes("-topmost", True)
        try:
            w.attributes("-alpha", 0.96)
        except tk.TclError:
            pass
        w.configure(bg=self.PANEL)
        frame = tk.Frame(w, bg=self.PANEL, padx=12, pady=8, highlightthickness=1, highlightbackground=self.BORDER)
        frame.pack()
        self.overlay_dot = tk.Label(frame, text="●", font=("Segoe UI", 12), fg=self.RED, bg=self.PANEL)
        self.overlay_dot.pack(side="left", padx=(0, 7))
        self.overlay_label = tk.Label(frame, text="DISABLED", font=("Segoe UI", 10, "bold"), fg=self.TEXT, bg=self.PANEL)
        self.overlay_label.pack(side="left")
        self.overlay_window = w
        w.update_idletasks()
        self.move_overlay()
        self.drag_delta = [0, 0]
        for widget in (w, frame, self.overlay_dot, self.overlay_label):
            widget.bind("<ButtonPress-1>", self._drag_start)
            widget.bind("<B1-Motion>", self._drag_move)

    def _drag_start(self, event):
        self.drag_delta[:] = [event.x_root - self.overlay_window.winfo_x(), event.y_root - self.overlay_window.winfo_y()]

    def _drag_move(self, event):
        self._clamp_overlay(event.x_root - self.drag_delta[0], event.y_root - self.drag_delta[1])

    def _clamp_overlay(self, x, y):
        w = self.overlay_window
        w.update_idletasks()
        sw, sh = w.winfo_screenwidth(), w.winfo_screenheight()
        w.geometry(f"+{max(0, min(x, sw - w.winfo_width()))}+{max(0, min(y, sh - w.winfo_height()))}")

    def move_overlay(self):
        if self.overlay_window and self.overlay_window.winfo_exists():
            self.overlay_window.update_idletasks()
            self._clamp_overlay(self.overlay_window.winfo_screenwidth() - self.overlay_window.winfo_width() - 24, 24)

    def toggle_overlay(self):
        if self.overlay_var.get():
            self.overlay_window.deiconify()
            self.overlay_window.attributes("-topmost", True)
        else:
            self.overlay_window.withdraw()

    def update_overlay(self, active):
        self.overlay_label.config(text="ENABLED" if active else "DISABLED")
        color = self.GREEN if active else self.RED
        self.overlay_dot.config(fg=color)
        self.status.set("RUNNING" if active else "READY")
        self.status_pill.config(text="● RUNNING" if active else "● READY", fg=color, bg="#20372f" if active else "#202838")

    def _start_listeners(self):
        if not mouse or not keyboard:
            messagebox.showerror("Missing dependency", "Run INSTALL_AND_LAUNCH.bat to install pynput.")
            return
        self.listener_mouse = mouse.Listener(on_click=self._on_mouse_click)
        self.listener_mouse.daemon = True
        self.listener_mouse.start()
        self.listener_keyboard = keyboard.Listener(on_press=self._on_key_press, on_release=self._on_key_release)
        self.listener_keyboard.daemon = True
        self.listener_keyboard.start()

    @staticmethod
    def _key_name(key):
        try:
            if hasattr(key, "name") and key.name:
                return key.name.upper()
            return str(key).replace("Key.", "").strip("'").upper()
        except Exception:
            return ""

    def _on_key_press(self, key):
        name = self._key_name(key)
        if not name:
            return
        # Debounce OS key-repeat: toggle only on the initial key-down.
        if name in self.pressed_keys:
            return
        self.pressed_keys.add(name)
        if self.hotkey_mouse_button is None and name == self.hotkey.upper():
            self._schedule_toggle()

    def _on_key_release(self, key):
        name = self._key_name(key)
        self.pressed_keys.discard(name)

    def _schedule_toggle(self):
        if not self.closing:
            try:
                self.root.after(0, self._toggle_running)
            except tk.TclError:
                pass

    def _on_mouse_click(self, x, y, button, pressed):
        if not pressed:
            return
        if self.recording:
            with self.record_lock:
                self.recorded.append((time.monotonic() - self.record_start, x, y, str(button)))
        callback = self.hotkey_capture_callback
        if callback is not None and button in (getattr(mouse.Button, "x1", None), getattr(mouse.Button, "x2", None)):
            self._schedule_callback(callback, button)
            return
        if self.pick_armed:
            self._schedule_callback(self._set_picked, x, y)
        if self.hotkey_mouse_button is not None and button == self.hotkey_mouse_button:
            self._schedule_toggle()

    def _schedule_callback(self, callback, *args):
        if not self.closing:
            try:
                self.root.after(0, lambda: callback(*args))
            except tk.TclError:
                pass

    def arm_pick(self):
        self.pick_armed = True
        self.pick_hint.config(text="Click the target point anywhere on screen…")
        self.root.iconify()

    def _set_picked(self, x, y):
        self.pick_armed = False
        self.root.deiconify()
        self.root.lift()
        self.use_current.set(False)
        self.x_entry.delete(0, "end")
        self.x_entry.insert(0, str(x))
        self.y_entry.delete(0, "end")
        self.y_entry.insert(0, str(y))
        self.pick_hint.config(text=f"Selected coordinates: X={x}, Y={y}")

    def _position_mode(self):
        self.pick_hint.config(text="Current cursor position will be used." if self.use_current.get() else "Fixed X/Y coordinates will be used.")

    def _get_config_snapshot(self):
        def integer(var, label):
            try:
                value = int(var.get())
            except (ValueError, tk.TclError):
                raise ValueError(f"{label} must be a whole number.")
            if value < 0:
                raise ValueError(f"{label} cannot be negative.")
            return value
        h = integer(self.hours, "Hours")
        m = integer(self.minutes, "Minutes")
        s = integer(self.seconds, "Seconds")
        ms = integer(self.millis, "Milliseconds")
        interval = h * 3600 + m * 60 + s + ms / 1000.0
        if interval <= 0:
            raise ValueError("The click interval must be greater than zero.")
        jitter = integer(self.random_ms, "Random offset") / 1000.0 if self.random_on.get() else 0.0
        count = integer(tk.StringVar(value=str(self.repeat_count.get())), "Repeat count")
        count = max(1, count)
        if not self.use_current.get():
            try:
                x, y = int(self.x_entry.get()), int(self.y_entry.get())
            except ValueError:
                raise ValueError("X and Y coordinates must be whole numbers.")
            if x < 0 or y < 0:
                raise ValueError("Coordinates cannot be negative.")
        else:
            x = y = None
        button_names = {"Left": "left", "Right": "right", "Middle": "middle", "X1": "x1", "X2": "x2"}
        button_name = button_names[self.mouse_button.get()]
        button = getattr(mouse.Button, button_name, None)
        if button is None:
            raise ValueError(f"This pynput/Windows setup does not support sending {self.mouse_button.get()} clicks.")
        return {
            "interval": interval,
            "jitter": jitter,
            "count": count,
            "repeat_mode": self.repeat_mode.get(),
            "button": button,
            "clicks": 2 if self.click_type.get() == "Double" else 1,
            "fixed_position": not self.use_current.get(),
            "x": x,
            "y": y,
        }
    def _toggle_running(self):
            if self.closing:
                return

            if self.running:
                self.stop()
            else:
                self.start()
    def start(self):
        with self.state_lock:
            if self.running:
                return
        try:
            config = self._get_config_snapshot()
        except Exception as exc:
            messagebox.showerror("Check your settings", str(exc), parent=self.root)
            return
        with self.state_lock:
            if self.running:
                return
            self.running = True
        self.stop_event.clear()
        self.start_btn.state(["disabled"])
        self.stop_btn.state(["!disabled"])
        self.update_overlay(True)
        self.worker = threading.Thread(target=self._click_loop, args=(config,), daemon=True, name="NexClickWorker")
        self.worker.start()

    def _click_loop(self, config):
        completed = 0
        try:
            while not self.stop_event.is_set():
                if config["fixed_position"]:
                    self.controller.position = (config["x"], config["y"])
                self.controller.click(config["button"], config["clicks"])
                completed += 1
                if config["repeat_mode"] == "count" and completed >= config["count"]:
                    break
                delay = max(0.001, config["interval"] + random.uniform(-config["jitter"], config["jitter"]))
                self.stop_event.wait(delay)
        except Exception as exc:
            self._schedule_callback(self._show_worker_error, str(exc))
        finally:
            self._schedule_callback(self._finished)

    def _show_worker_error(self, message):
        if not self.closing:
            messagebox.showerror("Clicking stopped", message, parent=self.root)

    def _finished(self):
        with self.state_lock:
            self.running = False
        if self.closing:
            return
        self.start_btn.state(["!disabled"])
        self.stop_btn.state(["disabled"])
        self.update_overlay(False)

    def stop(self):
        self.stop_event.set()
        with self.state_lock:
            self.running = False
        self.start_btn.state(["!disabled"])
        self.stop_btn.state(["disabled"])
        self.update_overlay(False)

    def set_hotkey(self):
        win = tk.Toplevel(self.root)
        win.title("Hotkey settings")
        win.resizable(False, False)
        win.transient(self.root)
        win.attributes("-topmost", True)
        win.configure(bg=self.PANEL)
        win.grab_set()
        frm = tk.Frame(win, bg=self.PANEL, padx=22, pady=18)
        frm.pack(fill="both", expand=True)
        tk.Label(frm, text="SET START / STOP HOTKEY", bg=self.PANEL, fg=self.TEXT, font=("Segoe UI", 12, "bold")).pack()
        tk.Label(frm, text="Press a keyboard key, or click mouse side button X1/X2.", bg=self.PANEL, fg=self.MUTED, wraplength=330).pack(pady=(8, 12))
        current_name = self.hotkey if self.hotkey_mouse_button is None else ("Mouse X1" if self.hotkey_mouse_button == getattr(mouse.Button, "x1", None) else "Mouse X2")
        current = tk.Label(frm, text=f"Current: {current_name}", bg=self.PANEL, fg=self.GREEN, font=("Segoe UI", 10, "bold"))
        current.pack(pady=4)
        prompt = tk.Label(frm, text="Waiting for input…", bg=self.PANEL, fg=self.ACCENT)
        prompt.pack(pady=5)

        old_callback = self.hotkey_capture_callback
        finished = {"value": False}

        def cleanup():
            if not finished["value"]:
                self.hotkey_capture_callback = old_callback
            try:
                win.grab_release()
            except tk.TclError:
                pass

        def on_key(event):
            key_name = event.keysym.upper()
            if key_name in ("SHIFT_L", "SHIFT_R", "CONTROL_L", "CONTROL_R", "ALT_L", "ALT_R", "CAPS_LOCK"):
                prompt.config(text="Choose a regular key or function key.")
                return
            finished["value"] = True
            self.hotkey = key_name
            self.hotkey_mouse_button = None
            self.hotkey_capture_callback = old_callback
            self._update_hotkey_buttons()
            current.config(text=f"Current: {self.hotkey}")
            prompt.config(text="Hotkey saved.")
            win.after(450, win.destroy)

        def on_mouse(button):
            if finished["value"]:
                return
            if button not in (getattr(mouse.Button, "x1", None), getattr(mouse.Button, "x2", None)):
                return
            finished["value"] = True
            self.hotkey_mouse_button = button
            label = "X1" if button == getattr(mouse.Button, "x1", None) else "X2"
            self.hotkey_capture_callback = old_callback
            self._update_hotkey_buttons()
            current.config(text=f"Current: Mouse {label}")
            prompt.config(text="Hotkey saved.")
            win.after(450, win.destroy)

        def on_close():
            self.hotkey_capture_callback = old_callback
            win.destroy()

        self.hotkey_capture_callback = on_mouse
        win.bind("<KeyPress>", on_key)
        win.protocol("WM_DELETE_WINDOW", on_close)
        ttk.Button(frm, text="Cancel", command=on_close).pack(pady=(12, 0))
        win.focus_force()

    def _update_hotkey_buttons(self):
        label = self.hotkey if self.hotkey_mouse_button is None else ("Mouse X1" if self.hotkey_mouse_button == getattr(mouse.Button, "x1", None) else "Mouse X2")
        self.start_btn.config(text=f"▶  START  ({label})")
        self.stop_btn.config(text=f"■  STOP  ({label})")

    def record_window(self):
        win = tk.Toplevel(self.root)
        win.title("Record & playback")
        win.resizable(False, False)
        win.attributes("-topmost", True)
        win.configure(bg=self.PANEL)
        frame = tk.Frame(win, bg=self.PANEL, padx=18, pady=16)
        frame.pack(fill="both", expand=True)
        tk.Label(frame, text="Record mouse clicks and replay their timing and positions.", bg=self.PANEL, fg=self.TEXT, wraplength=340).pack(anchor="w", pady=(0, 10))
        state = tk.Label(frame, text=f"Recorded clicks: {len(self.recorded)}", bg=self.PANEL, fg=self.MUTED)
        state.pack(anchor="w", pady=5)

        def refresh():
            with self.record_lock:
                n = len(self.recorded)
            state.config(text=f"Recorded clicks: {n}")

        def begin():
            with self.record_lock:
                self.recorded = []
                self.record_start = time.monotonic()
                self.recording = True
            state.config(text="Recording… click around, then stop recording.")

        def end():
            self.recording = False
            refresh()

        def playback():
            with self.record_lock:
                has_data = bool(self.recorded)
            if not has_data:
                messagebox.showinfo("No recording", "Record at least one click first.", parent=win)
                return
            threading.Thread(target=self._play_recording, daemon=True).start()

        ttk.Button(frame, text="Start recording", command=begin).pack(fill="x", pady=3)
        ttk.Button(frame, text="Stop recording", command=end).pack(fill="x", pady=3)
        ttk.Button(frame, text="Play sequence", command=playback).pack(fill="x", pady=3)
        ttk.Button(frame, text="Clear recording", command=lambda: self._clear_recording(refresh)).pack(fill="x", pady=3)

    def _clear_recording(self, refresh):
        self.recording = False
        with self.record_lock:
            self.recorded.clear()
        refresh()

    def _play_recording(self):
        with self.record_lock:
            events = list(self.recorded)
        previous = 0.0
        for stamp, x, y, button_name in events:
            delay = max(0.0, min(stamp - previous, 30.0))
            if self.stop_event.wait(delay):
                break
            previous = stamp
            try:
                self.controller.position = (x, y)
                # Replay recorded button type where possible.
                name = button_name.rsplit(".", 1)[-1].lower()
                btn = getattr(mouse.Button, name, mouse.Button.left)
                self.controller.click(btn, 1)
            except Exception:
                pass

    def close(self):
        self.closing = True
        self.stop_event.set()
        self.hotkey_capture_callback = None
        try:
            if self.listener_mouse:
                self.listener_mouse.stop()
            if self.listener_keyboard:
                self.listener_keyboard.stop()
        except Exception:
            pass
        try:
            if self.overlay_window and self.overlay_window.winfo_exists():
                self.overlay_window.destroy()
        except tk.TclError:
            pass
        self.root.destroy()

    def run(self):
        self.root.mainloop()


if __name__ == "__main__":
    if not mouse or not keyboard:
        print("Missing dependency. Run INSTALL_AND_LAUNCH.bat.")
        input("Press Enter to exit...")
        sys.exit(1)
    NexClickApp().run()
