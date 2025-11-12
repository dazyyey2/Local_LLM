import requests
import json
import os
from datetime import datetime

OLLAMA_URL = "http://localhost:11434/"

def clear_terminal():
    os.system('cls' if os.name == 'nt' else 'clear')
    
def generate(model="gemma3:27b", prompt="Hello, world!", stream=False):
    payload = {"model": model, "prompt": prompt, "stream": stream}
    try:
        resp = requests.post(
            OLLAMA_URL+'api/generate',
            data=json.dumps(payload),
            headers={"Content-Type": "application/json"},
            timeout=500,
        )
        resp.raise_for_status()
        return resp.json()  # dict with keys like: response, model, created_at, done
    except requests.exceptions.RequestException as e:
        print(f"Request error: {e}")
        return None

def get_current_models():
    """Return a list of model names from Ollama or [] on error."""
    try:
        resp = requests.get(
            OLLAMA_URL + 'api/tags',
            headers={"Content-Type": "application/json"},
            timeout=30,
        )
        resp.raise_for_status()
        data = resp.json()
        # Expected shape: {"models":[{"name":"llama3:8b", ...}, ...]}
        models = [m.get("name") for m in data.get("models", []) if m.get("name")]
        return models
    except requests.exceptions.RequestException as e:
        print(f"[Error] Could not fetch models from {OLLAMA_URL}api/tags\n{e}")
        return []

def print_current_models():
    running_models = get_current_models()
    models = {}
    counter = 0
    for model in running_models:
        counter += 1
        print(f'{counter}: {model}')
        models[str(counter)] = model
    return models
        
def export_response(response_dict, file_name=None):
    # """
    # Save the entire JSON response to disk and return the model's text reply.
    # """
    # if response_dict is None:
    #     return ""

    # if not file_name:
    #     ts = datetime.now().strftime("%Y%m%d-%H%M%S")
    #     file_name = f"export-{ts}.json"

    # path = os.path.join(os.getcwd(), file_name)

    # with open(path, "w", encoding="utf-8") as f:
    #     json.dump(response_dict, f, ensure_ascii=False, indent=4)

    # # Return the model's actual text (if present)
    return response_dict.get("response", "")

def print_menu(state):
    print("##############################")
    print("     Valters Local LLM")
    print("##############################")
    models = print_current_models()
    print("##############################")
    user_input = str(input('Please enter choice of model (default: gemma3:27b): '))
    if user_input == '':
        state['current_model'] = 'gemma3:27b'
    else:
        state['current_model'] = models[user_input]
    return state

def main():
    state = {}
    try:
        while True:
            if state.get('current_model'):
                user_input = input("Please enter a prompt (or /quit): ").strip()
                clear_terminal()
                if user_input.lower() in {"/quit", "/exit"}:
                    print("Goodbye!")
                    break
                print('Waiting for reply...')
                result = generate(model=state['current_model'], prompt=user_input)
                reply_text = export_response(result)
                clear_terminal()
                if reply_text:
                    print(reply_text)
                else:
                    print("No reply text found in response.\n")
            else:
                state = print_menu(state)
    except KeyboardInterrupt:
        print("\nExiting...")

if __name__ == "__main__":
    main()
