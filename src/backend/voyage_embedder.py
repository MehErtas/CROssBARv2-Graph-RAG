import voyageai

from dotenv import load_dotenv
import os

load_dotenv()


vo = voyageai.Client(api_key=os.getenv("VOYAGE_API_KEY")) 

def question_or_info_embedder(info):
    response = vo.embed(info, model="voyage-3-large") 
    return response.embeddings[0]