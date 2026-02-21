import google.generativeai as genai
from google.api_core.exceptions import (
    GoogleAPICallError,
    NotFound,
    InvalidArgument,
    PermissionDenied,
    ResourceExhausted,
    DeadlineExceeded,
)
from fastapi import HTTPException

def call_gemini(model: str, prompt: str, api_key: str) -> str:
    genai.configure(api_key=api_key)
    try:
        chat = genai.GenerativeModel(model).start_chat()
        response = chat.send_message(prompt)
        return response.text.strip()
    except InvalidArgument as e:
        raise HTTPException(status_code=400, detail=f"Invalid request to Gemini: {e}")
    except NotFound:
        raise HTTPException(status_code=404, detail=f"Gemini model not found: {model}")
    except PermissionDenied:
        raise HTTPException(status_code=403, detail="Permission denied by Gemini API")
    except ResourceExhausted:
        raise HTTPException(status_code=429, detail="Gemini quota exhausted or rate limit hit")
    except DeadlineExceeded:
        raise HTTPException(status_code=504, detail="Gemini request timed out")
    except GoogleAPICallError as e:
        raise HTTPException(status_code=502, detail=f"Error from Gemini API: {e}")
    except Exception as e:
        # Catch-all for anything unexpected
        raise HTTPException(status_code=500, detail=f"Unexpected error calling Gemini: {e}")