import requests
import json
import os
import base64

OLLAMA_URL = 'http://localhost:11434/'

def clear_terminal():
    os.system('cls' if os.name == 'nt' else 'clear')
    
def encode_image_to_base64(path):
    with open(path, 'rb') as f:
        return base64.b64encode(f.read()).decode('utf-8')

def send_request(model='gemma3:27b', prompt='Describe this image.', image_paths=None, stream=True, context=None, state={}):
    
    if isinstance(image_paths, str):image_paths = [image_paths]
    if image_paths is None and state.get('image_url'): #If there has been an image given in earlier promt, use that image for context.
        image_paths = state['image_url']
        
    images_b64 = []
    if image_paths: #If image is given.
        state['image_url'] = image_paths
        for path in image_paths:
            if not os.path.exists(path):
                path = path[1:-1] #Remove first and last letter of the path
                if not os.path.exists(path):
                    return 'NotFound', state['image_url'] #Return image not found.
            try:
                images_b64.append(encode_image_to_base64(path))
            except Exception as e:
                print(f'Failed to read image {path}: {e}')
    else: ############ If no image has been given given. #############
        payload = {'model': model, 'prompt': prompt, 'stream': stream}
        if context:
            payload['context'] = context

        try:
            resp = requests.post(
                OLLAMA_URL + 'api/generate',
                data=json.dumps(payload),
                headers={'Content-Type': 'application/json'},
                stream=True,
            )
            resp.raise_for_status()
        except Exception as e:
            print('Request error:', e)
            return None, state['image_url']

        final_context = None

        for line in resp.iter_lines(decode_unicode=True):
            if not line:
                continue
            data = json.loads(line)

            text = data.get('response', '')
            if text:
                print(text, end='', flush=True)

            if data.get('done'):
                final_context = data.get('context')
                break

        return final_context, state['image_url'] #Return from not having been given an image.

########### Been given an image ################
    payload = {'model': model, 'prompt': prompt, 'stream': stream}

    if images_b64:
        payload['images'] = images_b64

    if context is not None:
        payload['context'] = context

    try:
        resp = requests.post(
            OLLAMA_URL + 'api/generate',
            data=json.dumps(payload),
            headers={'Content-Type': 'application/json'},
            stream=True,
            timeout=120,
        )
        resp.raise_for_status()
    except requests.exceptions.RequestException as e:
        print('Request error:', e)
        return None, state['image_url']

    final_context = None

    for line in resp.iter_lines(decode_unicode=True):
        if not line:
            continue
        try:
            data = json.loads(line)
        except json.JSONDecodeError:
            print('\n[Warning] Received non-JSON line from server.')
            continue

        text = data.get('response', '')
        if text:
            print(text, end='', flush=True)

        if data.get('done'):
            final_context = data.get('context')
            break

    return final_context, state['image_url'] #Return from being given an image

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
    print('              Valters Local LLM')
    print('===============================================')
    models = print_current_models()
    print('===============================================')
    user_input = str(input('Please enter choice of model (default: gemma3:27b): '))
    if user_input == '':
        state['current_model'] = 'gemma3:27b'
        state['used_models'].add('gemma3:27b')
    elif models.get(user_input):
        state['current_model'] = models[user_input]
        state['used_models'].add(state['current_model'])
    else:
        print('No model with that ID, please enter a valid ID')
    return state

def main():
    state = {'current_model': None, 'context': None, 'image_url': None, 'used_models': set()}
    try:
        while True: #Main program loop
            if state.get('current_model'): #If a model is selected, proceed with using that model.
                image_path = ''
                user_input = input('Please enter a prompt (or /help): ').strip()
                if user_input == '/help':
                    print('/quit, /exit or /b - Exit to the menu.')
                    print('/img [imgURL] - Give the model image context')
                else:
                    if not user_input.lower() in {'/quit', '/exit', '/b'}: #If user doesn't want to quit, check if user wants to give image.
                        counter = 0
                        for word in user_input.split(): #Find the image url after user writes "/img"
                            if counter == 1:
                                image_path = word.strip()
                            if counter == 0:
                                if word == '/img':
                                    counter = 1
                    if image_path: #If the user gives an image, process the image
                        print(f'Currently selected LLM: {state['current_model']}')
                        print('----------------------------------------------------\n')
                        new_context, state['image_url'] = send_request(model=state['current_model'], prompt=user_input, image_paths=image_path, stream=True, context=state.get('context'), state=state) #Save the context in new_context.
                        if new_context is not None and new_context != 'NotFound': #Update context.
                            state['context'] = new_context
                        if new_context == 'NotFound': #If image path is not found
                            print('Image not found, please enter a valid image path.', end='')
                        print('\n\n----------------------------------------------------\n')
                    else: #If the user doesn't give an image.
                        if not user_input.lower() in {'/quit', '/exit', '/b'}:
                            print(f'Currently selected LLM: {state['current_model']}')
                            print('----------------------------------------------------\n')
                            new_context, state['image_url'] = send_request(model=state['current_model'], prompt=user_input, stream=True, context=state.get('context'), state=state) #Save the context in new_context.
                            if new_context is not None: #Update context.
                                state['context'] = new_context
                            print('\n\n----------------------------------------------------\n')
                        else: #If user_input is /quit, /exit or /b: restart.
                            clear_terminal()
                            state['current_model'] = None
                            state['context'] = None
                            state['image_url'] = None
            else: #If no model is selected, print the menu.
                state = print_menu(state)
    except KeyboardInterrupt: #If ctrl+c, exit gracefully.
        print('\nStopping LLMs...')
        for model in state['used_models']: #Stop all used models.
            print(f'Stopping {model}')
            os.system(f'ollama stop {model}')
        print('\nExiting...')

if __name__ == '__main__':
    main()

