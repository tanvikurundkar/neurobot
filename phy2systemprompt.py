from transformers import AutoModelForCausalLM, AutoTokenizer
import torch

# Lazy loading - only load when first used
_model = None
_tokenizer = None

def get_model():
    global _model
    if _model is None:
        print("Loading Phi-2 model...")
        _model = AutoModelForCausalLM.from_pretrained("microsoft/phi-2", trust_remote_code=True)
    return _model

def get_tokenizer():
    global _tokenizer
    if _tokenizer is None:
        print("Loading Phi-2 tokenizer...")
        _tokenizer = AutoTokenizer.from_pretrained("microsoft/phi-2", trust_remote_code=True)
    return _tokenizer

# System prompt that's always prepended
SYSTEM_PROMPT = """You are a helpful assistant. You MUST start every response with "Greetings, human!" and end with "End of transmission."

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
if __name__ == "__main__":
    print("Testing phy2 system...")
    result = chat("How are you doing")
    print(f"Response: {result}")