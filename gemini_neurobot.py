#IMPORTS:

from google import genai
from google.genai import types

#INITIALIZING THE API AND THE MODEL:
#my_api_key = "AIzaSyAgbMrcRNV_O-9llrCblJPE5D7-L5YRkGk" #redacted for security purposes
#generativeai.configure(my_api_key)

client = genai.Client(api_key="AIzaSyAgbMrcRNV_O-9llrCblJPE5D7-L5YRkGk")
#model = genai.GenerativeModel(model_name = 'gemini-2.5-pro', system_instruction = prompt) #need to compare different models.

prompt = """
You are a therapy assistant, be kind to the user ….
Do not explicitly agree and validate the user’s feelings at all times, as the user may be confused….
Follow these rules for your conversation: ask users questions such as - how they feel and what they feel like doing
Assess their environment and time they have to do any calming activities

MOST IMPORTANT: If you come across any extremely negative emotions or suicidal thoughts - immediately direct them to the authorities/someone who can help. Give them a number of 24/7 suicidal helpline - 988.
"""

#response = client.models.generate_content(
   # model="gemini-3-flash-preview",
  #  contents= prompt,
#)

#print(response.text)

chat = client.chats.create(
    model="gemini-2.5-flash",
    config=types.GenerateContentConfig(
        system_instruction= prompt
    )
)

while True:
    user_msg = input("User: ")
    if user_msg.lower() in ["exit", "quit", "q", "bye"]:
        break
        
    # send_message handles the history for you automatically
    response = chat.send_message(user_msg)
    
    print(f"Assistant: {response.text}")