#!/usr/bin/env python3
"""
Script to check available Ollama models and pull missing ones
"""
import requests
import json
from app.config import settings

def check_available_models():
    """Check what models are available on the Ollama server"""
    base_url = settings.ollama_base_url.rstrip('/')
    api_url = f"{base_url}/api/tags"
    
    print(f"Checking Ollama server at: {base_url}")
    print(f"Looking for model: {settings.ollama_model}\n")
    
    try:
        response = requests.get(api_url, timeout=10)
        if response.status_code == 200:
            data = response.json()
            models = data.get('models', [])
            
            if models:
                print("✅ Available models on server:")
                for model in models:
                    model_name = model.get('name', 'unknown')
                    print(f"  - {model_name}")
                
                # Check if our model is available
                model_names = [m.get('name', '') for m in models]
                if settings.ollama_model in model_names:
                    print(f"\n✅ Model '{settings.ollama_model}' is available!")
                    return True
                else:
                    print(f"\n❌ Model '{settings.ollama_model}' is NOT available.")
                    print(f"\nOptions:")
                    print(f"1. Pull the model on the remote server:")
                    print(f"   curl -X POST {base_url}/api/pull -d '{{\"name\": \"{settings.ollama_model}\"}}'")
                    print(f"2. Use one of the available models by updating app/config.py")
                    return False
            else:
                print("❌ No models found on the server")
                return False
        else:
            print(f"❌ Failed to connect: HTTP {response.status_code}")
            print(f"Response: {response.text}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"❌ Error connecting to Ollama server: {e}")
        print(f"\nPossible issues:")
        print(f"1. The ngrok tunnel may be down")
        print(f"2. The server URL may be incorrect")
        print(f"3. Network connectivity issues")
        return False

def pull_model():
    """Attempt to pull the required model"""
    base_url = settings.ollama_base_url.rstrip('/')
    api_url = f"{base_url}/api/pull"
    
    print(f"\nAttempting to pull model: {settings.ollama_model}")
    print(f"From server: {base_url}\n")
    
    try:
        response = requests.post(
            api_url,
            json={"name": settings.ollama_model},
            stream=True,
            timeout=300  # 5 minutes for large models
        )
        
        if response.status_code == 200:
            print("Pulling model (this may take a while)...")
            for line in response.iter_lines():
                if line:
                    try:
                        data = json.loads(line)
                        if 'status' in data:
                            print(f"  {data['status']}")
                    except:
                        pass
            print("\n✅ Model pull completed!")
            return True
        else:
            print(f"❌ Failed to pull model: HTTP {response.status_code}")
            print(f"Response: {response.text}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"❌ Error pulling model: {e}")
        return False

if __name__ == "__main__":
    print("=" * 60)
    print("Ollama Model Checker")
    print("=" * 60)
    print()
    
    if check_available_models():
        print("\n✅ Everything looks good!")
    else:
        print("\n" + "=" * 60)
        response = input("\nWould you like to try pulling the model? (y/n): ")
        if response.lower() == 'y':
            pull_model()
        else:
            print("\nTo fix this manually:")
            print(f"1. SSH into the server running Ollama")
            print(f"2. Run: ollama pull {settings.ollama_model}")
            print(f"3. Or update app/config.py to use an available model")

