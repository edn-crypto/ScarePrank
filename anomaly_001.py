# Copyright (c) 2025 s0l-godzz and edn-crypto
#
# MIT License
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED.

#!/usr/bin/env python3
"""
matrix_prank_complete.py

Full, runnable version with minor robustness fixes:
- use tkinter.font as tkfont (avoids shadowing)
- ensure protocol handlers get callables (lambda: ...)
- safer bring_to_front handling
- keep original behavior and UI text
"""

import os
import sys
import random
import json
import urllib.request
from urllib.parse import quote_plus
import getpass
import webbrowser
import tkinter as tk
import tkinter.font as tkfont
from tkinter import scrolledtext, simpledialog, messagebox



# requires Pillow: pip install pillow
from PIL import Image, ImageTk, ImageFilter

# -------------------------
# Fullscreen image glitch effect
# -------------------------
def show_image_glitch(root, image_path, duration_ms=750, noise_pixels=800, flicker_times=3):
    """
    Show a fullscreen, topmost Toplevel that displays `image_path` for duration_ms.
    Adds quick flicker + pixel disorder (small rectangles sampled from the image)
    to create a brief "glitch" effect.

    Where to put it:
    - Paste this function above start_visual_glitch (after your imports / GLITCH settings).
    - Call it from static_overlay() (see integration example below).
    """
    try:
        # Create fullscreen overlay window (no decorations)
        win = tk.Toplevel(root)
        try:
            win.attributes("-fullscreen", True)
        except Exception:
            sw, sh = win.winfo_screenwidth(), win.winfo_screenheight()
            win.geometry(f"{sw}x{sh}+0+0")
        try:
            win.attributes("-topmost", True)
        except Exception:
            pass
        win.overrideredirect(True)  # remove window frame

        sw, sh = win.winfo_screenwidth(), win.winfo_screenheight()

        # Load image with Pillow so we can resize and sample pixels
        try:
            img = Image.open(image_path).convert("RGBA")
        except Exception as e:
            # fallback: show a plain color box if image can't be loaded
            canvas = tk.Canvas(win, width=sw, height=sh, highlightthickness=0, bg="black")
            canvas.pack(fill="both", expand=True)
            win.after(duration_ms, lambda: (win.destroy() if win.winfo_exists() else None))
            return

        # Resize image to cover screen while preserving aspect ratio
        img_ratio = img.width / img.height
        screen_ratio = sw / sh
        if img_ratio > screen_ratio:
            # image is wider: scale by height
            new_h = sh
            new_w = int(img_ratio * new_h)
        else:
            new_w = sw
            new_h = int(new_w / img_ratio)
        img = img.resize((new_w, new_h), Image.LANCZOS)

        # Slight blur/sharpen to make the glitch pop
        img = img.filter(ImageFilter.UnsharpMask(radius=1, percent=50, threshold=2))

        photo = ImageTk.PhotoImage(img)

        # Place image on a Canvas so we can overlay disorder rectangles
        canvas = tk.Canvas(win, width=sw, height=sh, highlightthickness=0)
        canvas.pack(fill="both", expand=True)

        # center image
        x0 = (sw - new_w) // 2
        y0 = (sh - new_h) // 2
        canvas.create_image(x0, y0, anchor="nw", image=photo)
        # keep a reference to avoid GC
        canvas.photo = photo

        # A small helper to add pixel disorder using sampled colors from the image:
        def add_pixel_noise(count=noise_pixels, rect_size=(2, 6)):
            # sample random pixels from the resized Pillow image
            for _ in range(count):
                rx = random.randint(0, new_w - 1)
                ry = random.randint(0, new_h - 1)
                px = img.getpixel((rx, ry))
                # convert tuple to hex color (supports RGBA)
                color = f"#{px[0]:02x}{px[1]:02x}{px[2]:02x}"
                # map to screen coords
                sx = x0 + rx
                sy = y0 + ry
                w = random.randint(rect_size[0], rect_size[1])
                h = random.randint(rect_size[0], rect_size[1])
                # draw tiny block
                canvas.create_rectangle(sx, sy, sx + w, sy + h, fill=color, outline=color)

        # Flicker sequence: show image, add quick noise layers and small flashes

        def flicker_step(i=0):
            if i >= flicker_times:
                # final tiny noise burst, then schedule destroy
                add_pixel_noise(int(noise_pixels * 0.7), rect_size=(1, 5))
                win.after(duration_ms - 100, lambda: (win.destroy() if win.winfo_exists() else None))
                return
            # small random background flash to sell the effect
            try:
                flash_bg = random.choice(["#000000", "#111111", "#060606", "#1a1a1a"])
                canvas.configure(bg=flash_bg)
            except Exception:
                pass
            # add quick pixel noise overlay
            add_pixel_noise(int(noise_pixels / 3), rect_size=(1, 4))
            # short pause between flickers
            win.after(int(duration_ms / max(4, flicker_times * 2)), lambda: flicker_step(i + 1))

        # Start the flicker/noise and ensure removal
        win.after(50, lambda: flicker_step(0))
        # ensure cleanup in case timing drifts
        win.after(duration_ms + 250, lambda: (win.destroy() if win.winfo_exists() else None))

    except Exception:
        # Fail gracefully if Pillow or tk operations throw — no crash
        try:
            if 'win' in locals() and win.winfo_exists():
                win.destroy()
        except Exception:
            pass

        # choose style: matrix (green), red/cyber, tv (dots/lines), or image glitch
        style = random.choice(["matrix", "cyber_red", "tv_static", "image_glitch"])

        if style == "matrix":
            ...
        elif style == "cyber_red":
            ...
        elif style == "tv_static":
            ...
        elif style == "image_glitch":
            # show your uploaded image briefly as a fullscreen glitch
            # use the absolute or relative path to your image file
            # If your image is in the same folder as the script, "Download.jpg" will work.
            show_image_glitch(root, "/mnt/data/Download.jpg", duration_ms=750)
            # do not draw other overlay rectangles in this branch because show_image_glitch creates its own Toplevel


# -------------------------
# Colors (restored)
# -------------------------
BG = "#0b0710"              # main background
LABEL_COLOR = "#ff2e2e"     # red header
TEXT_COLOR = "#ffdcdc"      # pale text
BTN_BG = "#330000"          # deep red buttons
BTN_ACTIVE = "#550000"      # active deep red
EXTRA_BTN_BG = "#221100"    # darker extra-button tone
EXTRA_BTN_ACTIVE = "#553322"
YELLOW_BTN_BG = "#6b5d20"   # yellowish Emergency/Help
YELLOW_BTN_ACTIVE = "#8a7a30"

# -------------------------
# Secret code (new per run)
# -------------------------
def new_secret_code():
    return "{:04d}".format(random.randint(0, 9999))


SECRET_CODE = new_secret_code()
# print("DEBUG SECRET_CODE:", SECRET_CODE)


# -------------------------
# Helpers
# -------------------------
def panic_exit(event=None):
    """Immediate panic key: show a short popup then exit."""
    try:
        # show a tiny confirmation (may fail on some platforms)
        messagebox.showinfo("Killed", "You killed the menu.")
    except Exception:
        pass
    # hard exit
    os._exit(0)


def fetch_ip_location(timeout=3.0):
    """Best-effort IP -> (city, country). If fails returns ('', 'Unknown')."""
    services = [
        "https://ipapi.co/json/",
        "https://ipinfo.io/json",
        "https://ipwho.is/"
    ]

    for url in services:
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "matrix-prank/1.0"})
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                raw = resp.read().decode("utf-8", errors="ignore")
            try:
                data = json.loads(raw)
            except Exception:
                data = {}

            city = (data.get("city") or data.get("region") or "").strip()
            country = (data.get("country_name") or data.get("country") or "").strip()
            if city and country:
                return city, country
            if country:
                return "", country
        except Exception:
            continue

    return "", "Unknown"


def bring_to_front(win):
    """Try to bring a window to the front gracefully."""
    if win is None:
        return
    try:
        win.lift()
        # on some platforms attributes isn't supported
        try:
            win.attributes("-topmost", True)
            win.focus_force()
            win.after(150, lambda: win.attributes("-topmost", False))
        except Exception:
            # fallback
            win.focus_force()
    except Exception:
        try:
            win.lift()
        except Exception:
            pass


# -------------------------
# Dense Binary rain canvas
# -------------------------
class BinaryRainCanvas(tk.Canvas):
    def __init__(self, parent, width, height, speed=35, **kwargs):
        super().__init__(parent, width=width, height=height, highlightthickness=0, **kwargs)
        self.width = width
        self.height = height
        self.speed = speed
        self.column_width = 10  # denser columns
        self.columns = max(10, int(self.width / self.column_width))
        self.drops = [random.randint(-self.height, 0) for _ in range(self.columns)]
        self.running = False

    def start(self):
        self.running = True
        self._animate()

    def stop(self):
        self.running = False

    def _animate(self):
        if not self.running:
            return
        # clear and redraw
        self.delete("all")
        for i in range(self.columns):
            x = i * self.column_width + 4
            y = self.drops[i]
            # draw multiple bits per column to look denser
            for k in range(3):
                char = random.choice(["0", "1"])
                # use a small monospace font (platform will fallback)
                try:
                    self.create_text(x, y - k * 12, text=char, fill="#00ff00",
                                     font=("Consolas", 10), anchor="nw")
                except Exception:
                    self.create_text(x, y - k * 12, text=char, fill="#00ff00",
                                     anchor="nw")
            self.drops[i] += random.randint(8, 20)
            if self.drops[i] > self.height + 40:
                self.drops[i] = random.randint(-160, -20)
        self.after(self.speed, self._animate)


# -------------------------
# Binary typing notepad
# -------------------------
class BinaryTypingNotepad(tk.Toplevel):
    def __init__(self, master, content, font_size=28, delay=70, fade_time=1000):
        super().__init__(master)
        self.master = master
        self.content = content
        self.delay = delay
        self.fade_time = fade_time
        self.idx = 0
        self.typing_running = True
        self.title("Notepad")

        W, H = 920, 480
        sw, sh = self.winfo_screenwidth(), self.winfo_screenheight()
        self.geometry(f"{W}x{H}+{(sw-W)//2}+{(sh-H)//2}")
        self.configure(bg=BG)

        # Binary background canvas (denser)
        self.canvas = BinaryRainCanvas(self, width=W, height=H, bg="black")
        self.canvas.place(x=0, y=0)

        # Text frame on top
        frame = tk.Frame(self, bg=BG)
        frame.place(relx=0.02, rely=0.03, relwidth=0.96, relheight=0.9)
        fam = "Consolas" if sys.platform.startswith("win") else "Courier"
        txt_font = tkfont.Font(family=fam, size=font_size)
        self.text_widget = scrolledtext.ScrolledText(frame, wrap="word", font=txt_font,
                                                     bg=BG, fg="#ff2222", insertbackground="#ff6666")
        self.text_widget.pack(fill="both", expand=True)
        self.text_widget.configure(state="disabled")

        # Close button inert during typing
        bottom = tk.Frame(self, bg=BG)
        bottom.place(relx=0, rely=0.93, relwidth=1, relheight=0.07)
        self.close_btn = tk.Button(bottom, text="Close", width=12, command=self.inert_close,
                                   bg=EXTRA_BTN_BG, fg=TEXT_COLOR, activebackground=EXTRA_BTN_ACTIVE)
        self.close_btn.pack(side="right", padx=8, pady=6)
        self.protocol("WM_DELETE_WINDOW", lambda: self.inert_close())

        # Start animations & typing
        self.canvas.start()
        # small delay before typing
        self.after(180, self._type_next_char)

    def inert_close(self):
        if self.typing_running:
            try:
                messagebox.showwarning("Locked", "This window cannot be closed while writing.")
            except Exception:
                pass
            bring_to_front(self)
        else:
            try:
                self.destroy()
            except Exception:
                pass

    def _type_next_char(self):
        # finished
        if self.idx >= len(self.content):
            self.typing_running = False
            try:
                self.text_widget.configure(state="normal")
            except Exception:
                pass
            self.text_widget.mark_set("insert", "end")
            # fade and then enable close
            self.after(250, self._fade_background_and_enable_close)
            return

        ch = self.content[self.idx]
        try:
            self.text_widget.configure(state="normal")
            self.text_widget.insert("end", ch)
            self.text_widget.see("end")
            self.text_widget.configure(state="disabled")
        except Exception:
            pass
        self.idx += 1

        # some delay sweetening for punctuation and newlines
        extra = 160 if ch in ".!?" else (70 if ch == "\n" else 0)
        self.after(max(10, self.delay + extra), self._type_next_char)

    def _fade_background_and_enable_close(self):
        steps = 12
        delay = max(20, int(self.fade_time / steps))

        def step(i=0):
            if i > steps:
                try:
                    self.canvas.stop()
                    self.canvas.delete("all")
                except Exception:
                    pass
                # now allow normal close
                try:
                    self.protocol("WM_DELETE_WINDOW", lambda: self.destroy())
                except Exception:
                    pass
                return

            # simulate light overlay grey_level 0..60
            grey_level = int((i / steps) * 60)
            # ensure 0..255
            grey_level = max(0, min(255, grey_level))
            grey = f"#{grey_level:02x}{grey_level:02x}{grey_level:02x}"
            try:
                # draw a rectangle overlay (tagged so repeated draws overwrite)
                self.canvas.delete("fade")
                self.canvas.create_rectangle(0, 0, self.canvas.width, self.canvas.height,
                                             fill=grey, outline=grey, tags="fade")
            except Exception:
                pass
            self.after(delay, lambda: step(i + 1))

        step()


# -------------------------
# Secret helpers (Clue Finder & Trivia Helper behavior)
# -------------------------
class SecretHelpers:
    def __init__(self, root, secret_code):
        self.root = root
        self.secret = secret_code
        # decide which positions clue finder reveals (2 positions)
        all_positions = list(range(4))
        random.shuffle(all_positions)
        self.clue_positions = sorted(all_positions[:2])  # e.g., [0,3]
        # other two positions for trivia reveal
        self.trivia_positions = sorted([p for p in all_positions if p not in self.clue_positions])

    def clue_finder(self):
        # reveal digits at clue_positions, show pattern like '2**2'
        s = list("****")
        for pos in self.clue_positions:
            s[pos] = self.secret[pos]
        pattern = "".join(s)
        messagebox.showinfo("Clue Finder", f"Clue revealed: {pattern}")
        bring_to_front(self.root)

    def trivia_helper(self):
        # ask 5 moderately hard but solvable questions; if all 5 correct reveal remaining digits
        qpool = [
            ("What is the atomic number of gold?", "79"),
            ("Which planet has the most moons (as of 2023)?", "saturn"),
            ("What is the capital city of Peru?", "lima"),
            ("In computing, what does 'CPU' stand for?", "central processing unit"),
            ("What is the approximate value of pi to 2 decimal places?", "3.14"),
            ("What year did the Berlin Wall fall?", "1989"),
            ("Which element has chemical symbol 'Na'?", "sodium"),
            ("Who wrote '1984'?", "george orwell"),
            ("What is the largest ocean on Earth?", "pacific"),
            ("What language is primarily spoken in Brazil?", "portuguese")
        ]
        picks = random.sample(qpool, 5)
        correct = 0
        for q, a in picks:
            ans = simpledialog.askstring("Trivia Helper", q, parent=self.root)
            if ans and ans.strip().lower() == a.lower():
                correct += 1

        if correct == 5:
            # reveal the trivia positions digits
            s = list("****")
            for pos in self.trivia_positions:
                s[pos] = self.secret[pos]
            pattern = "".join(s)
            messagebox.showinfo("Trivia Helper", f"Passed! Revealed: {pattern}")
        else:
            messagebox.showinfo("Trivia Helper", f"You got {correct}/5 correct.")
        bring_to_front(self.root)


# -------------------------
# Emergency quiz: 10 harder questions; must be all correct to prompt for code entry
# -------------------------
def emergency_quiz_flow(root, secret_code):
    if not messagebox.askyesno("Emergency", "Start the emergency quiz (10 questions)?"):
        bring_to_front(root)
        return

    qpool = [
        ("What is the capital of Iceland?", "reykjavik"),
        ("What year did the Titanic sink?", "1912"),
        ("What is the chemical formula for table salt?", "nacl"),
        ("Who painted the Mona Lisa?", "leonardo da vinci"),
        ("Which gas makes up ~78% of Earth's atmosphere?", "nitrogen"),
        ("What is the largest planet in our solar system?", "jupiter"),
        ("What is the square root of 144?", "12"),
        ("Which metal has the highest electrical conductivity?", "silver"),
        ("In which country is the Taj Mahal located?", "india"),
        ("Who proposed the theory of general relativity?", "albert einstein"),
        ("What is the freezing point of water in Celsius?", "0"),
        ("Which city hosted the 2012 Summer Olympics?", "london"),
        ("What currency is used in Japan?", "yen"),
        ("What is the chemical symbol for iron?", "fe"),
        ("Which scientist discovered penicillin?", "alexander fleming")
    ]
    picks = random.sample(qpool, 10)
    correct = 0
    for q, a in picks:
        ans = simpledialog.askstring("Emergency Quiz", q, parent=root)
        if ans and ans.strip().lower() == a.lower():
            correct += 1

    wrong = 10 - correct
    if wrong == 0:
        # allow user to enter the 4-digit code immediately
        messagebox.showinfo("Perfect", "All correct — enter the 4-digit secret code now.")
        code = simpledialog.askstring("Enter Code", "Enter the 4-digit secret code:", parent=root)
        if code and code.strip() == secret_code:
            messagebox.showinfo("Unlocked", "Correct code! Escape key: Ctrl + Shift + K")
            try:
                root.destroy()
            except Exception:
                pass
            os._exit(0)
        else:
            messagebox.showerror("Wrong", "Incorrect code.")
    else:
        messagebox.showinfo("Emergency Result", f"You got {wrong}/10 wrong.")
        bring_to_front(root)


# -------------------------
# Overlay (close/minimize abuse)
# -------------------------
def show_overlay_then_reset(root, duration_ms):
    if getattr(root, "overlay_open", False):
        bring_to_front(getattr(root, "active_overlay", None))
        return

    overlay = tk.Toplevel(root)
    # try to make fullscreen
    try:
        overlay.attributes("-fullscreen", True)
    except Exception:
        # fallback to covering the screen manually
        sw, sh = overlay.winfo_screenwidth(), overlay.winfo_screenheight()
        overlay.geometry(f"{sw}x{sh}+0+0")
    try:
        overlay.attributes("-topmost", True)
    except Exception:
        pass
    overlay.configure(bg="black")
    root.overlay_open = True
    root.active_overlay = overlay

    bigf = tkfont.Font(family="Segoe UI" if sys.platform.startswith("win") else "Helvetica", size=56, weight="bold")
    lbl = tk.Label(overlay, text="- Security Center -\nPotential threat detected:\ntaking protective actions",
                   font=bigf, fg="#ff3333", bg="black", justify="center")
    lbl.pack(pady=(80, 10))

    dotf = tkfont.Font(size=48)
    dot_lbl = tk.Label(overlay, text="", font=dotf, fg="#ff6666", bg="black")
    dot_lbl.pack()

    badgef = tkfont.Font(size=18, weight="bold")
    badge_box = tk.Label(overlay, text="🛡️ Microsoft Security", font=badgef,
                         fg="#ffdcdc", bg="#222222", padx=12, pady=8)
    badge_box.pack(pady=(30, 6))

    patent_label = tk.Label(overlay, text="(System Integrity Warning\nProtecting your files...)", font=("Segoe UI", 10), fg="#999999", bg="black")
    patent_label.pack()

    steps = ["", ".", "..", "..."]

    def animate(i=0):
        try:
            dot_lbl.config(text=steps[i % len(steps)])
        except Exception:
            pass
        overlay.after(450, lambda: animate(i + 1))

    animate()

    def finish():
        try:
            overlay.destroy()
        except Exception:
            pass
        root.overlay_open = False
        root.active_overlay = None
        root.attempts = 0
        bring_to_front(root)

    overlay.after(duration_ms, finish)
    bring_to_front(overlay)

# -------------------------
# Glitch settings (tweak to taste)
# -------------------------
GLITCH_MIN_DELAY = 8000   # minimum time between glitches (ms)
GLITCH_MAX_DELAY = 15000  # maximum time between glitches (ms)
GLITCH_DURATION = 2000    # how long glitch visuals last (ms)

# -------------------------
# Visual glitch effect (shake + flicker + static)
# -------------------------
def start_visual_glitch(root):
    """Non-blocking short glitch animation inside the prank window."""
    # if overlay or notepad open, skip
    if getattr(root, "overlay_open", False) or getattr(root, "active_notepad", None):
        return

    x0, y0 = root.winfo_x(), root.winfo_y()

    # --- 1. Shake (async) ---
    def shake(i=0):
        if i >= 10:
            try:
                root.geometry(f"+{x0}+{y0}")
            except Exception:
                pass
            flicker(0)
            return
        dx, dy = random.randint(-6, 6), random.randint(-6, 6)
        try:
            root.geometry(f"+{x0 + dx}+{y0 + dy}")
        except Exception:
            pass
        root.after(20, lambda: shake(i + 1))

    # --- 2. Flicker colors ---
    def flicker(i):
        if i >= 3:
            try:
                root.configure(bg=BG)
            except Exception:
                pass
            static_overlay()
            return
        # a short blast of color to sell the glitch
        try:
            root.configure(bg=random.choice(["#004400", "#330000", "#0f3057", "#001100", "#002200"]))
        except Exception:
            pass
        root.after(70, lambda: flicker(i + 1))

    # --- 3. Static overlay (randomized style) ---
    def static_overlay():
        w, h = root.winfo_width(), root.winfo_height()
        if w <= 0 or h <= 0:
            # if sizes not ready, try again shortly
            root.after(50, static_overlay)
            return

        overlay = tk.Canvas(root, width=w, height=h, highlightthickness=0, bg="", bd=0)
        overlay.place(x=0, y=0)

        # choose style: matrix (green), red/cyber, tv (dots/lines)
        style = random.choice(["cyber", "tv", "bars", "image_glitch"])

        if style == "matrix":
            # dense green bits + faint vertical lines to mimic matrix rain
            for _ in range(200):
                x = random.randint(0, w)
                y = random.randint(0, h)
                hgt = random.randint(6, 30)
                overlay.create_text(x, y, text=random.choice(["0", "1"]), anchor="nw", font=("Consolas", 8), fill="#00ff66")
            # a few vertical translucent lines
            for _ in range(6):
                x = random.randint(0, w)
                overlay.create_rectangle(x, 0, x+2, h, fill="#003300", outline="")

        elif style == "cyber_red":
            # colored blocks, horizontal bars, and RGB offset rectangles
            palette = [
                ["#ff2e2e", "#cc2323", "#990f0f"],   # red tones
                ["#3a0ca3", "#4361ee", "#7209b7"],   # purple/blue
                ["#00ffcc", "#00ccff", "#0066ff"]    # cyan/blue
            ]
            colors = random.choice(palette)
            for _ in range(60):
                x1 = random.randint(0, w)
                y1 = random.randint(0, h)
                x2 = x1 + random.randint(10, 120)
                y2 = y1 + random.randint(6, 40)
                c = random.choice(colors)
                overlay.create_rectangle(x1, y1, x2, y2, fill=c, outline="")

            # a few thin vertical neon lines for tearing effect
            for _ in range(5):
                x = random.randint(0, w)
                overlay.create_rectangle(x, 0, x + random.randint(2,5), h, fill=random.choice(colors), outline="")

        elif style == "tv_static":
            # gray/white pixel noise + horizontal scan bars
            for _ in range(1200):
                x = random.randint(0, w)
                y = random.randint(0, h)
                gray = random.choice(["#AAAAAA", "#BBBBBB", "#CCCCCC", "#EEEEEE", "#FFFFFF"])
                overlay.create_rectangle(x, y, x + 1, y + 1, fill=gray, outline=gray)
            # a few horizontal neon scan lines
            for _ in range(8):
                y = random.randint(0, h)
                overlay.create_rectangle(0, y, w, y + random.randint(1,4), fill=random.choice(["#ff0077", "#00ffee", "#ffff00"]), outline="")

        elif style == "image_glitch":
            # show your uploaded image briefly as a fullscreen glitch
            show_image_glitch(root, "/mnt/data/Download.jpg", duration_ms=750)


        # slight background flash to sell effect
        try:
            root.configure(bg=random.choice(["#0a0a0a", "#101010", "#070707"]))
        except Exception:
            pass

        # destroy overlay after GLITCH_DURATION
        root.after(GLITCH_DURATION, lambda: overlay.destroy() if overlay.winfo_exists() else None)
        # --- Optional realistic photo fade-in/fade-out ---
        def show_realistic_flash():
            import time
            from PIL import Image, ImageTk

            # full overlay on top of glitch canvas
            flash = tk.Toplevel(root)
            flash.attributes("-fullscreen", True)
            flash.attributes("-topmost", True)
            flash.configure(bg="black")

            screen_w = flash.winfo_screenwidth()
            screen_h = flash.winfo_screenheight()

            # Load your local image (update filename!)
            img = Image.open("Download.jpg")
            img = img.resize((int(screen_w * 0.6), int(screen_h * 0.6)))
            photo = ImageTk.PhotoImage(img)

            lbl = tk.Label(flash, image=photo, bg="black")
            lbl.image = photo
            lbl.place(relx=0.5, rely=0.5, anchor="center")

            # fade in/out loop
            steps = 20
            def fade(i=0):
                if i <= steps:
                    alpha = i / steps
                    flash.attributes("-alpha", alpha)
                    flash.after(40, lambda: fade(i + 1))
                elif i <= 2 * steps:
                    alpha = 1 - (i - steps) / steps
                    flash.attributes("-alpha", alpha)
                    flash.after(40, lambda: fade(i + 1))
                else:
                    flash.destroy()
            fade()

        # call flash right after static glitch starts
        root.after(250, show_realistic_flash)

    # start the sequence
    shake()


# -------------------------
# Main App
# -------------------------
def run_app():
    global SECRET_CODE
    SECRET_CODE = new_secret_code()  # regenerate code each run

    root = tk.Tk()
    root.title("Can I hack you?")
    W, H = 760, 360
    sw, sh = root.winfo_screenwidth(), root.winfo_screenheight()
    root.geometry(f"{W}x{H}+{(sw-W)//2}+{(sh-H)//2}")
    root.resizable(False, False)
    root.configure(bg=BG)

    root.overlay_open = False
    root.active_overlay = None
    root.active_notepad = None

    # Panic key (works but not advertised)
    root.bind_all("<Control-Shift-KeyPress-K>", panic_exit)
    root.bind_all("<Control-Shift-KeyPress-k>", panic_exit)

    # Prepare helpers (clue & trivia will share the same secret code)
    helpers = SecretHelpers(root, SECRET_CODE)

    # Header
    title_font = tkfont.Font(family="Segoe UI" if sys.platform.startswith("win") else "Helvetica",
                             size=40, weight="bold")
    header = tk.Label(root, text="Can I hack you?", font=title_font, fg=LABEL_COLOR, bg=BG)
    header.pack(pady=(24, 6))
    subtitle = tk.Label(root, text="Answer honestly.", font=("Segoe UI", 12), fg=TEXT_COLOR, bg=BG)
    subtitle.pack()

    # Buttons
    sub_font = tkfont.Font(family="Segoe UI" if sys.platform.startswith("win") else "Helvetica", size=12)
    btn_frame = tk.Frame(root, bg=BG)
    btn_frame.pack(pady=(14, 12))
    yes_btn = tk.Button(btn_frame, text="Yes", width=14, height=2, font=sub_font,
                        bg=BTN_BG, fg=TEXT_COLOR, activebackground=BTN_ACTIVE)
    no_btn = tk.Button(btn_frame, text="No", width=14, height=2, font=sub_font,
                       bg=BTN_BG, fg=TEXT_COLOR, activebackground=BTN_ACTIVE)
    yes_btn.pack(side="left", padx=20)
    no_btn.pack(side="left", padx=20)

    # Helper buttons (clue & trivia)
    helper_frame = tk.Frame(root, bg=BG)
    helper_frame.pack(pady=(8, 6))
    clue_btn = tk.Button(helper_frame, text="Clue Finder", width=14, command=helpers.clue_finder,
                         bg=EXTRA_BTN_BG, fg=TEXT_COLOR, activebackground=EXTRA_BTN_ACTIVE)
    trivia_btn = tk.Button(helper_frame, text="Trivia Helper", width=14, command=helpers.trivia_helper,
                           bg=EXTRA_BTN_BG, fg=TEXT_COLOR, activebackground=EXTRA_BTN_ACTIVE)
    clue_btn.pack(side="left", padx=6)
    trivia_btn.pack(side="left", padx=6)

    # Emergency (yellow) and Help (yellow) aligned together
    emergency_btn = tk.Button(root, text="Emergency", width=10, bg=YELLOW_BTN_BG, fg=TEXT_COLOR,
                              activebackground=YELLOW_BTN_ACTIVE,
                              command=lambda: emergency_quiz_flow(root, SECRET_CODE))
    help_btn = tk.Button(root, text="Help", width=8, bg=YELLOW_BTN_BG, fg=TEXT_COLOR,
                         activebackground=YELLOW_BTN_ACTIVE,
                         command=lambda: (messagebox.showinfo(
                             "Help",
                             "Want to kill the menu, huh? Then find the secret code.\n\n"
                             "Pro tip (if you're a noob look away): Clue Finder, Trivia Helper and Emergency can help you.\n\n"
                             "Now close me >:("
                         ), bring_to_front(root)))
    emergency_btn.place(relx=0.85, rely=0.98, anchor="se")
    help_btn.place(relx=0.98, rely=0.98, anchor="se")

    # Pulsing header colors (red tones)
    pulse = ["#ff2e2e", "#cc2323", "#990f0f"]
    pi = {"i": 0}

    def pulse_label():
        try:
            header.config(fg=pulse[pi["i"]])
            pi["i"] = (pi["i"] + 1) % len(pulse)
        except Exception:
            pass
        root.after(350, pulse_label)

    pulse_label()

    # Keep track of attempts (close/minimize)
    root.attempts = 0

    # Close/minimize attempts: first warn, second shows overlay for 9-17s and then returns
    def on_close_attempt():
        root.attempts += 1
        if root.attempts == 1:
            messagebox.showwarning("Don't", "Don't do this again")
            bring_to_front(root)
        else:
            dur = random.randint(9, 17) * 1000
            show_overlay_then_reset(root, dur)

    root.protocol("WM_DELETE_WINDOW", lambda: on_close_attempt())

    # Handle minimize/unmap attempts
    def on_unmap(event=None):
        try:
            if root.state() == "iconic":
                root.attempts += 1
                root.after(50, lambda: root.deiconify())
                if root.attempts == 1:
                    messagebox.showwarning("Don't", "Don't do this again")
                    bring_to_front(root)
                else:
                    dur = random.randint(9, 17) * 1000
                    show_overlay_then_reset(root, dur)
        except Exception:
            pass

    root.bind("<Unmap>", on_unmap)

    # Yes flow: create typing notepad with dense binary background that types username & location and opens Google Maps
    def yes_flow():
        if not messagebox.askyesno("Confirm", "Are you sure you want to answer YES?"):
            bring_to_front(root)
            return

        try:
            username = getpass.getuser()
        except Exception:
            username = "User"

        city, country = fetch_ip_location()
        content_lines = [
            f"Hello, {username}",
            "",
            f"Approx. location: {city}, {country}",
            f"City: {city}",
            f"Country: {country}",
            "",
            "— end of report —"
        ]
        content = "\n".join(content_lines) + "\n"

        # open Google Maps to city (best-effort)
        if city:
            try:
                webbrowser.open_new_tab("https://www.google.com/maps/search/?api=1&query=" + quote_plus(city))
            except Exception:
                pass

        # open the typing notepad with binary background
        notepad = BinaryTypingNotepad(root, content, font_size=26, delay=70, fade_time=1200)
        root.active_notepad = notepad
        bring_to_front(notepad)

    def no_flow():
        messagebox.showinfo("Haha", "haha get pranked, find another way!")
        bring_to_front(root)

    yes_btn.config(command=yes_flow)
    no_btn.config(command=no_flow)

    # Keep window always on top briefly if it loses focus
    # Keep window always on top briefly if user clicks outside
    def enforce_focus():
        if not root.focus_displayof():
            # Bring back to front
            root.lift()
            root.attributes("-topmost", True)
            root.after(800, lambda: root.attributes("-topmost", False))
            root.after(250, root.focus_force)

            # Show playful popup
            try:
                messagebox.showinfo("Haha >:)", "Haha you cannot close it >:)")
            except Exception:
                pass

        root.after(500, enforce_focus)

    enforce_focus()  # start focus enforcement

    # -------------------------
    # Automatic 8–15s glitch loop
    # -------------------------
    def glitch_loop():
        start_visual_glitch(root)
        root.after(random.randint(3000, 8000), glitch_loop)

    # initial schedule for the first glitch
    root.after(random.randint(3000, 8000), glitch_loop)


    root.mainloop()


if __name__ == "__main__":
    run_app()

# --- IGNORE ---

    

