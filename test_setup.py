import subprocess
import requests
import time
import re

NGROK_TOKEN = "31XxI8ju9Pw3hToSBPReQxKhpdu_2GDTRbYPUeEnXyBijmkbo"
MODEL_NAME = "gemma2:9b"

def run_cmd(cmd, background=False):
    if background:
        return subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    else:
        return subprocess.run(cmd, shell=True, check=True, stdout=subprocess.PIPE).stdout.decode()

# 1. Install Ollama if not present
try:
    run_cmd("ollama --version")
    print("✅ Ollama already installed")
except:
    print("⬇️ Installing Ollama...")
    run_cmd("curl -fsSL https://ollama.com/install.sh | sh")

# 2. Start Ollama server
print("🚀 Starting Ollama server...")
run_cmd("nohup env OLLAMA_HOST=0.0.0.0:11434 ollama serve > ollama.log 2>&1 &", background=True)
time.sleep(5)

# 3. Pull the LLM model
print(f"⬇️ Pulling model {MODEL_NAME} ...")
run_cmd(f"ollama pull {MODEL_NAME}")

# 4. Install ngrok v3 if not present
try:
    run_cmd("./ngrok --version")
    print("✅ ngrok already installed")
except:
    print("⬇️ Downloading ngrok v3...")
    run_cmd("wget -q https://bin.equinox.io/c/bNyj1mQVY4c/ngrok-v3-stable-linux-amd64.tgz")
    run_cmd("tar -xvzf ngrok-v3-stable-linux-amd64.tgz")

# 5. Authenticate ngrok
print("🔑 Authenticating ngrok...")
run_cmd(f"./ngrok config add-authtoken {NGROK_TOKEN}")

# 6. Start tunnel to Ollama
print("🌐 Starting ngrok tunnel...")
ngrok_proc = subprocess.Popen(["./ngrok", "http", "11434"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)

# 7. Wait a few seconds and fetch tunnel URL from API
time.sleep(5)
try:
    tunnels = requests.get("http://127.0.0.1:4040/api/tunnels").json()
    public_url = tunnels["tunnels"][0]["public_url"]
    print(f"✅ Ollama is live at: {public_url}")
except Exception as e:
    print("⚠️ Could not fetch ngrok URL. Check ngrok logs.")
