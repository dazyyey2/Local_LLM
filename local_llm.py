import requests
import json
import os
import base64

OLLAMA_URL = 'http://localhost:11434/'

def clear_terminal():
    os.system('cls' if os.name == 'nt' else 'clear')
    
def encode_image_to_base64(path):
    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")

def vision_generate(model="gemma3:27b", prompt="Describe this image.", image_paths=None, stream=True, context=None):
    """
    Call an Ollama vision-capable model with one or more images + a text prompt.
    Streams the response to stdout and returns the final context (if any).
    """

    if isinstance(image_paths, str):
        image_paths = [image_paths]

    images_b64 = []
    if image_paths:
        for path in image_paths:
            if not os.path.exists(path):
                print(f"[Warning] Image not found: {path}")
                continue
            try:
                images_b64.append(encode_image_to_base64(path))
            except Exception as e:
                print(f"[Warning] Failed to read image {path}: {e}")

    payload = {
        "model": model,
        "prompt": prompt,
        "stream": stream,
    }

    if images_b64:
        payload["images"] = images_b64

    if context is not None:
        payload["context"] = context

    try:
        resp = requests.post(
            OLLAMA_URL + "api/generate",
            data=json.dumps(payload),
            headers={"Content-Type": "application/json"},
            stream=True,
            timeout=120,
        )
        resp.raise_for_status()
    except requests.exceptions.RequestException as e:
        print("Request error:", e)
        return None

    final_context = None

    for line in resp.iter_lines(decode_unicode=True):
        if not line:
            continue
        try:
            data = json.loads(line)
        except json.JSONDecodeError:
            print("\n[Warning] Received non-JSON line from server.")
            continue

        text = data.get("response", "")
        if text:
            print(text, end="", flush=True)

        if data.get("done"):
            final_context = data.get("context")
            break

    return final_context

def generate(model, prompt, stream=True, context=None):
    payload = {
        "model": model,
        "prompt": prompt,
        "stream": stream,
    }
    if context:
        payload["context"] = context

    try:
        resp = requests.post(
            OLLAMA_URL + "api/generate",
            data=json.dumps(payload),
            headers={"Content-Type": "application/json"},
            stream=True,
        )
    except Exception as e:
        print("Request error:", e)
        return None

    final_context = None

    for line in resp.iter_lines(decode_unicode=True):
        if not line:
            continue
        data = json.loads(line)

        text = data.get("response", "")
        if text:
            print(text, end="", flush=True)

        if data.get("done"):
            final_context = data.get("context")
            break

    return final_context

def get_current_models():
    try:
        resp = requests.get(
            OLLAMA_URL + 'api/tags',
            headers={'Content-Type': 'application/json'},
            timeout=30,
        )
        resp.raise_for_status()
        data = resp.json()
        models = [m.get('name') for m in data.get('models', []) if m.get('name')]
        return models
    except requests.exceptions.RequestException as e:
        print(f'[Error] Could not fetch models from {OLLAMA_URL}api/tags\n{e}')
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

def print_menu(state):
    print('===============================================')
    print('              Valters Lokala LLM')
    print('===============================================')
    models = print_current_models()
    print('===============================================')
    user_input = str(input('Please enter choice of model (default: gemma3:27b): '))
    if user_input == '':
        state['current_model'] = 'gemma3:27b'
    elif models.get(user_input):
        state['current_model'] = models[user_input]
    else:
        print('No model with that ID, please enter a valid ID')
    return state

def main():
    state = {
    "current_model": None,
    "context": None,
}
    try:
        while True:
            if state.get('current_model'):
                image_path = ''
                
                user_input = input('Please enter a prompt (or /quit): ').strip()
                if not user_input.lower() in {'/quit', '/exit', '/b'}:
                    image_path = input("Enter image path (or leave empty for text-only): ").strip()
                clear_terminal()
                if image_path:
                    print(f"Currently selected LLM (vision): {state['current_model']}")
                    print('----------------------------------------------------\n')
                    state["context"] = vision_generate(
                        model=state["current_model"],
                        prompt=user_input,
                        image_paths=image_path,
                        stream=True,
                        context=state.get("context"),
                    )
                    print('\n\n----------------------------------------------------\n')
                else:
                    if not user_input.lower() in {'/quit', '/exit', '/b'}:
                        print(f'Currently selected LLM: {state["current_model"]}')
                        print('----------------------------------------------------\n')
                        context = state.get("context")
                        state['context'] = generate(model=state['current_model'], prompt=user_input, stream=True, context=context)
                        print('\n\n----------------------------------------------------\n')
                    else:
                        state['current_model'] = None
                        state['context'] = None
            else:
                state = print_menu(state)
    except KeyboardInterrupt:
        print('\nExiting...')

if __name__ == '__main__':
    main()

