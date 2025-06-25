import os
import time
import hmac
import hashlib
import base64
import requests
from requests_toolbelt.multipart.encoder import MultipartEncoder

# Setup
access_key = "29c61d09c5fd397ea8b724318bb2c993"
access_secret = ""
host = "identify-ap-southeast-1.acrcloud.com"
endpoint = f"https://{host}/v1/identify"
file_path = "downloaded_reels/romanianbits/romanianbits_reel_5_audio.mp3"

# Timestamp and signature
timestamp = str(int(time.time()))
string_to_sign = f"POST\n/v1/identify\n{access_key}\naudio\n1\n{timestamp}"
signature = base64.b64encode(
    hmac.new(access_secret.encode('utf-8'), string_to_sign.encode('utf-8'), digestmod=hashlib.sha1).digest()
).decode('utf-8')

# Double check file path
assert os.path.exists(file_path), "Audio file does not exist."

# Proper multipart encoding
m = MultipartEncoder(
    fields={
        'access_key': access_key,
        'timestamp': timestamp,
        'signature': signature,
        'data_type': 'audio',
        'signature_version': '1',
        'sample': ('filename.mp3', open(file_path, 'rb'), 'audio/mpeg')
    }
)

# POST
response = requests.post(endpoint, data=m, headers={'Content-Type': m.content_type})

print("🔄 Status:", response.status_code)
print("📬 Response:", response.text)
