import os
import google.generativeai as genai
from dotenv import load_dotenv

def main():
    load_dotenv()
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("Error: GEMINI_API_KEY not found in .env")
        return
        
    print(f"Using API Key starting with: {api_key[:10]}...")
    genai.configure(api_key=api_key)
    
    try:
        models = list(genai.list_models())
        print(f"\nFound {len(models)} models accessible with this API key.")
        print("-" * 50)
        
        valid_models = []
        for m in models:
            if 'generateContent' in m.supported_generation_methods:
                print(f"✅ {m.name}")
                valid_models.append(m.name)
            else:
                print(f"❌ {m.name} (does not support generateContent)")
                
        print("-" * 50)
        if valid_models:
            print(f"Please copy one of the ✅ model names above (e.g., '{valid_models[0].split('models/')[-1]}')")
            print("and update 'gemini_model' in app/config.py!")
        else:
            print("No models supporting generateContent were found for this API key.")
            
    except Exception as e:
        print(f"API Error when listing models: {e}")

if __name__ == "__main__":
    main()
