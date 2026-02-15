from transformers import AutoModelForCausalLM, AutoTokenizer
import torch

import os
import joblib

MODEL_PATH = "phi2_model.joblib"
TOKENIZER_PATH = "phi2_tokenizer.joblib"
MODEL_NAME = "microsoft/phi-2"


# Lazy loading - only load when first used
_model = None
_tokenizer = None

def get_model():
    global _model

    if _model is not None:
        return _model

    if os.path.exists(MODEL_PATH):
        print("Loading Phi-2 model from local file...")
        _model = joblib.load(MODEL_PATH)
    else:
        print("Downloading Phi-2 model...")
        _model = AutoModelForCausalLM.from_pretrained(
            MODEL_NAME,
            trust_remote_code=True
        )
        joblib.dump(_model, MODEL_PATH)

    return _model

def get_tokenizer():
    global _tokenizer

    if _tokenizer is not None:
        _tokenizer.pad_token = _tokenizer.eos_token
        return _tokenizer

    if os.path.exists(TOKENIZER_PATH):
        print("Loading Phi-2 tokenizer from local file...")
        _tokenizer = joblib.load(TOKENIZER_PATH)
    else:
        print("Downloading Phi-2 tokenizer...")
        _tokenizer = AutoTokenizer.from_pretrained(
            MODEL_NAME,
            trust_remote_code=True
        )
        joblib.dump(_tokenizer, TOKENIZER_PATH)

    _tokenizer.pad_token = _tokenizer.eos_token
    return _tokenizer

# System prompt that's always prepended
SYSTEM_PROMPT = """You are a helpful assistant.

Follow these rules strictly:
1. Always be formal
2. Never discuss politics  
3. Provide a SINGLE response. do not act as anyting but the assistant.
4. Provide ONE response only, do not continue the conversation.
5. Do not say ANYTHING as the User

Please follow these instrucitons when responding to the message from the user below.
"""

def chat(user_message):
    try:
        model = get_model()
        tokenizer = get_tokenizer()
        
        full_prompt = f"{SYSTEM_PROMPT}\n\nUser: {user_message}\nAssistant:"
        inputs = tokenizer(full_prompt, return_tensors="pt")
        outputs = model.generate(**inputs, max_new_tokens=50)
        return tokenizer.decode(outputs[0], skip_special_tokens=True)
    except Exception as e:
        return f"Error processing message: {str(e)}"

# Test if run directly

def conversation():
    global SYSTEM_PROMPT
    print("Type anything to talk to phi 2! (enter q to quit)")
    inp = input()
    prompt_length = len(SYSTEM_PROMPT) + len("\n\nUser: ") + len(inp)
    while(inp != "q"):
        try:
            model = get_model()
            tokenizer = get_tokenizer()
            
            full_prompt = f"{SYSTEM_PROMPT}\n\nUser: {inp}\nModel:"
            inputs = tokenizer(full_prompt, return_tensors="pt")
            outputs = model.generate(**inputs, max_new_tokens=100, pad_token_id=tokenizer.pad_token_id)

            str_result =  tokenizer.decode(outputs[0], skip_special_tokens=True)

            single_result = str_result[prompt_length:]

            pos = single_result.find("User")
            if pos != -1: finaloutput = single_result[:pos]
            else: finaloutput = single_result

            pos = finaloutput.rfind("Model:")
            if  pos != -1: finaloutput = finaloutput[pos + len("Model:"):]

            finaloutput = "Model: " + finaloutput.strip()

            print(finaloutput)
            
            SYSTEM_PROMPT += (f"\n\nUser: {inp}\nModel:") + finaloutput

        except Exception as e:
            return f"Error processing message: {str(e)}"
        
        inp = input()
        prompt_length = len(SYSTEM_PROMPT) + len("\n\nUser: ") + len(inp)


if __name__ == "__main__":
    get_model()
    get_tokenizer()
    conversation()