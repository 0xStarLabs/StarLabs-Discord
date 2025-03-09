from loguru import logger
from openai import OpenAI
from typing import Optional
import httpx



def ask_chatgpt(api_key: str, model: str, user_message: str, prompt: str, proxy: str = "") -> tuple[bool, str]:
    """
    Send a message to ChatGPT and get a response.

    Args:
        api_key (str): OpenAI API key
        user_message (str): The message to send to ChatGPT
        proxy (str): Proxy in format user:pass@ip:port or ip:port

    Returns:
        str: ChatGPT's response
    """

    if proxy:
        logger.info(f"Using proxy: {proxy} for ChatGPT")
        # Format proxy URL with scheme if not present
        if not proxy.startswith(("http://", "https://")):
            proxy = f"http://{proxy}"

        http_client = httpx.Client(proxy=proxy)
        client = OpenAI(api_key=api_key, http_client=http_client)

    else:
        client = OpenAI(api_key=api_key)

    # Prepare the messages
    messages = []
    if prompt:
        messages.append({"role": "system", "content": prompt})
    messages.append({"role": "user", "content": user_message})

    try:
        # Make the API call
        response = client.chat.completions.create(model=model, messages=messages)

        # Extract and return the response text
        response_text = response.choices[0].message.content
        if "Rate limit reached" in response_text:
            raise Exception("GPT rate limit reached, please try again later.")
        
        if "You exceeded your current quota" in response_text:
            raise Exception("Your ChatGPT API key has no balance.")
        
        return True, response_text
    except Exception as e:
        if "Rate limit reached" in str(e):
            return False, "GPT rate limit reached, please try again later."
        
        if "You exceeded your current quota" in str(e):
            return False, "Your ChatGPT API key has no balance."
        
        return False, f"GPT Error occurred: {str(e)}"