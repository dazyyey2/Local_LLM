import requests
import json
import os
from datetime import datetime

OLLAMA_URL = "http://localhost:11434/"

def generate(model="gemma3:27b", prompt="Hello, world!", stream=False):
    payload = {"model": model, "prompt": prompt, "stream": stream}
    try:
        resp = requests.post(
            OLLAMA_URL+'api/generate',
            data=json.dumps(payload),
            headers={"Content-Type": "application/json"},
            timeout=120,
        )
        resp.raise_for_status()
        return resp.json()  # dict with keys like: response, model, created_at, done
    except requests.exceptions.RequestException as e:
        print(f"Request error: {e}")
        return None

def get_current_models():
    try:
        resp = requests.post(
            OLLAMA_URL+'api/tags',
            headers={"Content-Type": "application/json"},
            timeout=120,
        )
        resp.raise_for_status()
        return resp.json()
    except requests.exceptions.RequestException as e:
        print(f"Request error: {e}")
        return None
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

def handle_choices(user_input):
    match user_input:
        case '1':
            return

def print_menu(state):
    print("##############################")
    print("     Valters Local LLM")
    print("##############################")
    print(get_current_models())
    print("##############################")
    user_input = str(input('Please enter choice of model (default: gemma3:27b): '))
    if user_input == '':
        state['current_model'] = 'gemma3:27b'
    else:
        state['current_model'] = user_input
    return state

def main():
    state = {}
    try:
        while True:
            if state.get('current_model'):
                state = print_menu(state)
                user_input = input("Please enter a prompt (or /quit): ").strip()
                if user_input.lower() in {"/quit", "/exit"}:
                    print("Goodbye!")
                    break

                result = generate(prompt=user_input)
                reply_text = export_response(result)  # writes JSON; returns reply text

                if reply_text:
                    print("\n########--- Model reply ---########")
                    print(reply_text)
                    print("---------------------------\n")
                else:
                    print("No reply text found in response.\n")
    except KeyboardInterrupt:
        print("\nExiting. Bye!")

if __name__ == "__main__":
    main()
