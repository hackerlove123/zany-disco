import urllib.request as urllib2
import threading
import socket
import sys
import time
import tkinter as tk
from tkinter import filedialog, messagebox
from tkinter import ttk
from struct import pack
from datetime import datetime

sys.dont_write_bytecode = True

# Màu sắc
red = "red"
green = "green"
defcol = "black"

socks = []
working = []
toCheck = []
threads = []
checking = True
stop_flag = False
dead_proxies_count = 0
working_proxies_count = 0
output_file = ""

def log_message(msg, color=defcol):
    log_text.insert(tk.END, msg + "\n", color)
    log_text.see(tk.END)

def error(msg):
    log_message("[!] - " + msg, red)

def action(msg):
    log_message("[+] - " + msg, green)

def generate_output_filename(proxy_type):
    now = datetime.now().strftime("%Y%m%d_%H%M%S")
    return f"{proxy_type}_{now}.txt"

def saveToFile(proxy):
    with open(output_file, 'a') as file:
        file.write(f"{proxy}\n")  # Ghi proxy vào file

def isSocks4(host, port, soc):
    packet4 = b"\x04\x01" + pack(">H", int(port)) + socket.inet_aton(host) + b"\x00"
    try:
        soc.sendall(packet4)
        data = soc.recv(8)
        if len(data) < 2 or data[0] != 0 or data[1] != 0x5A:
            return False
        return True
    except (BrokenPipeError, socket.error):
        return False

def isSocks5(host, port, soc):
    try:
        soc.sendall(b"\x05\x01\x00")
        data = soc.recv(2)
        if len(data) < 2 or data[0] != 5 or data[1] != 0:
            return False
        return True
    except (BrokenPipeError, socket.error):
        return False

def check_http(proxy):
    try:
        start_time = time.time()
        proxy_handler = urllib2.ProxyHandler({'http': proxy, 'https': proxy})
        opener = urllib2.build_opener(proxy_handler)
        opener.addheaders = [('User-agent', 'Mozilla/5.0')]
        urllib2.install_opener(opener)
        req = urllib2.Request('http://www.google.com')
        sock = urllib2.urlopen(req, None, timeout=5)
        response_time = time.time() - start_time
        return response_time
    except:
        return None

def checkProxies():
    global dead_proxies_count, working_proxies_count
    while len(toCheck) > 0 and not stop_flag:
        proxy = toCheck.pop(0).strip()

        if ':' not in proxy:
            error(f"Proxy không hợp lệ: {proxy}")
            continue

        try:
            host, port = proxy.split(":")
            port = int(port)
        except ValueError:
            error(f"Không thể phân tích proxy: {proxy}")
            continue

        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(1)

        if isSocks4(host, port, s):
            working.append(proxy)
            proxy_type = "SOCKS4"
            saveToFile(proxy)
            working_proxies_count += 1
            action(f"Proxy SOCKS4 hoạt động: {proxy}")
            add_to_working_table(proxy, proxy_type, "N/A")
        elif isSocks5(host, port, s):
            working.append(proxy)
            proxy_type = "SOCKS5"
            saveToFile(proxy)
            working_proxies_count += 1
            action(f"Proxy SOCKS5 hoạt động: {proxy}")
            add_to_working_table(proxy, proxy_type, "N/A")
        else:
            response_time = check_http(proxy)
            if response_time is not None:
                working.append(proxy)
                proxy_type = "HTTP"
                saveToFile(proxy)
                working_proxies_count += 1
                action(f"Proxy HTTP hoạt động: {proxy} - Thời gian phản hồi: {response_time:.2f} giây")
                add_to_working_table(proxy, proxy_type, f"{response_time:.2f} giây")
            else:
                dead_proxies_count += 1
                error(f"Proxy chết: {proxy}")
                add_to_dead_table(proxy)

        s.close()
        update_progress()
        update_counters()

def add_to_working_table(proxy, proxy_type, response_time):
    working_table.insert(tk.END, f"{proxy} | {proxy_type} | {response_time}")
    working_table.see(tk.END)

def add_to_dead_table(proxy):
    dead_table.insert(tk.END, proxy)
    dead_table.see(tk.END)

def start_checking():
    global threadsnum, toCheck, checking, stop_flag, dead_proxies_count, working_proxies_count, output_file

    threadsnum = int(threads_entry.get())
    proxy_list_path = proxy_list_entry.get()
    with open(proxy_list_path, "r") as f:
        toCheck.extend(line.strip() for line in f.readlines())

    stop_flag = False
    dead_proxies_count = 0
    working_proxies_count = 0

    output_file = generate_output_filename("proxy")

    for _ in range(threadsnum):
        thread = threading.Thread(target=checkProxies)
        thread.daemon = True
        thread.start()

    global checking
    checking = True
    monitor_threads()

def monitor_threads():
    global checking
    if checking:
        if all(not thread.is_alive() for thread in threading.enumerate()
               if thread is not threading.current_thread()):
            action("Tất cả các luồng đã hoàn thành.")
            messagebox.showinfo(
                "Hoàn thành",
                f"Quá trình chạy hoàn thành! Proxy đã được xuất ra file: {output_file}"
            )
            checking = False
        else:
            root.after(1000, monitor_threads)

def update_progress():
    progress_bar['value'] = len(working)
    root.update_idletasks()

def update_counters():
    dead_proxies_label.config(text=f"Proxy chết: {dead_proxies_count}")
    working_proxies_label.config(
        text=f"Proxy hoạt động: {working_proxies_count}")

def exit_tool():
    root.quit()

# Thiết lập GUI
root = tk.Tk()
root.title("Check Live Proxy")

# Thiết lập các phần tử giao diện
tk.Label(root, text="Danh sách proxy:").grid(row=0, column=0, padx=10, pady=5)
proxy_list_entry = ttk.Entry(root, width=50)
proxy_list_entry.grid(row=0, column=1, padx=10, pady=5)
ttk.Button(root,
           text="Duyệt",
           command=lambda: proxy_list_entry.insert(
               0, filedialog.askopenfilename())).grid(row=0,
                                                      column=2,
                                                      padx=10,
                                                      pady=5)

tk.Label(root, text="Số lượng luồng:").grid(row=2, column=0, padx=10, pady=5)
threads_entry = ttk.Entry(root, width=50)
threads_entry.grid(row=2, column=1, padx=10, pady=5)

ttk.Button(root, text="Bắt đầu", command=start_checking).grid(row=4,
                                                              column=1,
                                                              padx=10,
                                                              pady=20)
ttk.Button(root, text="Dừng",
           command=lambda: setattr(stop_flag, True)).grid(row=4,
                                                          column=2,
                                                          padx=10,
                                                          pady=20)
ttk.Button(root, text="Thoát", command=exit_tool).grid(row=4,
                                                       column=3,
                                                       padx=10,
                                                       pady=20)

progress_bar = ttk.Progressbar(root,
                               orient="horizontal",
                               length=400,
                               mode="determinate")
progress_bar.grid(row=5, column=0, columnspan=4, padx=10, pady=20)

log_text = tk.Text(root, height=10, width=80)
log_text.grid(row=6, column=0, columnspan=4, padx=10, pady=10)

# Bảng thông báo cho proxy sống
ttk.Label(root, text="Proxy Sống:").grid(row=7, column=0, padx=10, pady=5)
working_table = tk.Listbox(root, width=80, height=5)
working_table.grid(row=8, column=0, columnspan=4, padx=10, pady=5)

# Bảng thông báo cho proxy chết
ttk.Label(root, text="Proxy Chết:").grid(row=9, column=0, padx=10, pady=5)
dead_table = tk.Listbox(root, width=80, height=5)
dead_table.grid(row=10, column=0, columnspan=4, padx=10, pady=5)

# Thêm các thẻ cho màu sắc
log_text.tag_config("red", foreground="red")
log_text.tag_config("green", foreground="green")
log_text.tag_config("black", foreground="black")

# Thêm nhãn cho bộ đếm
dead_proxies_label = ttk.Label(root, text="Proxy chết: 0")
dead_proxies_label.grid(row=11, column=0, padx=10, pady=5)

working_proxies_label = ttk.Label(root, text="Proxy hoạt động: 0")
working_proxies_label.grid(row=11, column=1, padx=10, pady=5)

root.mainloop()
