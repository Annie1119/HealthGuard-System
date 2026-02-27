import os
import httpx
import asyncio
from dotenv import load_dotenv

load_dotenv()

async def list_available_models():
    api_key = os.getenv("GEMINI_API_KEY")
    url = f"https://generativelanguage.googleapis.com/v1beta/models?key={api_key}"
    
    async with httpx.AsyncClient() as client:
        response = await client.get(url)
        if response.status_code == 200:
            models = response.json().get('models', [])
            print("--- 你可以使用的模型清單 ---")
            for model in models:
                # 只列出支援生成內容的模型
                if 'generateContent' in model.get('supportedGenerationMethods', []):
                    print(f"模型名稱: {model['name']}")
        else:
            print(f"錯誤: {response.status_code}")
            print(response.text)

if __name__ == "__main__":
    asyncio.run(list_available_models())