from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware


class EncryptRequest(BaseModel):
    text: str
    key: int

class DecryptRequest(BaseModel):
    text: str

from fastapi import FastAPI, HTTPException
import requests

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Разрешить запросы с любого источника (для разработки)
    allow_credentials=True,
    allow_methods=["*"],  # Разрешить все методы (GET, POST и т.д.)
    allow_headers=["*"],  # Разрешить любые заголовки
)

dictionary = set()

def load_dictionary():
    url = "https://raw.githubusercontent.com/dwyl/english-words/master/words.txt"
    response = requests.get(url)
    if response.status_code == 200:
        global dictionary
        dictionary = set(word.strip().lower() for word in response.text.splitlines())
    else:
        raise Exception("Cannot load the dictionary")

def caesar_cipher(text: str, key: int, mode: str = "encrypt") -> str:
    result = []
    for char in text:
        if 'a' <= char <= 'z':
            base = ord('a')
            offset = (ord(char) - base + key) % 26 if mode == 'encrypt' else (ord(char) - base - key) % 26
            result.append(chr(base + offset))
        elif 'A' <= char <= 'Z':
            base = ord('A')
            offset = (ord(char) - base + key) % 26 if mode == 'encrypt' else (ord(char) - base - key) % 26
            result.append(chr(base + offset))
        else:
            result.append(char)  # Не изменяем неалфавитные символы
    return ''.join(result)

def is_meaningful(text: str) -> bool:
    if not dictionary:
        raise Exception("Dictionary is not loaded. Call load_dictionary() first.")

    words = text.lower().split()
    meaningful_word_count = sum(1 for word in words if word in dictionary)
    return len(words) > 0 and meaningful_word_count / len(words) > 0.5

def find_key_with_dictionary(cipher_text: str):
    if not dictionary:
        raise Exception("Dictionary is not loaded. Call load_dictionary() first.")

    for key in range(26):
        decrypted_text = caesar_cipher(cipher_text, key, mode='decrypt')
        if is_meaningful(decrypted_text):
            return key, decrypted_text
    return None, None

@app.on_event("startup")
def startup_event():
    try:
        load_dictionary()
        print("Dictionary loaded successfully!")
    except Exception as e:
        print(f"Error loading dictionary: {e}")

@app.post("/encrypt")
def encrypt_post(request: EncryptRequest):
    return {"encrypted_text": caesar_cipher(request.text, request.key)}

@app.post("/decrypt")
def decrypt_post(request: DecryptRequest):
    key, decrypted_text = find_key_with_dictionary(request.text)
    if key is None:
        raise HTTPException(status_code=400, detail="Could not decrypt the text")
    return {"key": key, "decrypted_text": decrypted_text}

@app.get("/encrypt")
def encrypt(text: str, key: int):
    """API-ручка для шифрования текста"""
    if not text:
        raise HTTPException(status_code=400, detail="Text cannot be empty")
    return {"encrypted_text": caesar_cipher(text, key)}

@app.get("/decrypt")
def decrypt(text: str):
    """API-ручка для расшифровки текста"""
    key, decrypted_text = find_key_with_dictionary(text)
    if key is None:
        raise HTTPException(status_code=400, detail="Could not decrypt the text")
    return {"key": key, "decrypted_text": decrypted_text}
