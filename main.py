import ollama

print("\n\nHi there! (Press Ctrl+C to exit)")

try:
    while True:
        user_input = input("\n:> ")
        
        response = ollama.chat(model='tinyllama', messages=[
            {'role': 'user', 'content': user_input}
        ])
        
        print(f"AI: {response['message']['content']}")

except KeyboardInterrupt:
    print("\n\nClosing the chat.")