from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
import logging
from dotenv import load_dotenv
from contextlib import asynccontextmanager
import json
import traceback
import asyncio

from models import QueryRequest, QueryResponse
from prompt import build_prompt
from llm_router import generate_response
from boot import system_boot_bm25
from retriever import graph_retriever
import os

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Lifespan: initialize retrieval components
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Boots up the chromaDB
    app.state.all_bm25s = system_boot_bm25()
    yield

# Create app with lifespan
app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:1793","http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from fastapi import Response

@app.options("/query/stream")
def options_query_stream():
    return Response(status_code=200)

@app.post("/query", response_model=QueryResponse)
def handle_query(request: Request, data: QueryRequest):
    try:
        # ------ Stage 1: Condense conversation ------
        if len(data.messages) <= 1:
            single_question = data.content
        else:
            convo_text = "\n".join([f"{msg.role.capitalize()}: {msg.content}" for msg in data.messages])
            condense_prompt = (
                "You are an expert assistant. Given the following conversation between a user and an assistant, "
                "please summarize it into a single concise question.\n\n"
                f"Conversation:\n{convo_text}\n\n"
                "Single Question:"
            )
            single_question = generate_response(model="gemini-2.5-flash", prompt=condense_prompt, api_key=os.getenv("GEMINI_API_KEY"))
        logger.info(f"Stage 1 (Condense) result: {single_question}")

        # ------ Stage 2: Retrieval ------
        retrieved_docs = graph_retriever(
            single_question,
            data.searchLength,
            data.extensionSize,
            request
        )
        logger.info(f"Stage 2 (Retrieval) returned {len(retrieved_docs)} docs")

        # ------ Stage 3: Generation ------
        prompt = build_prompt(retrieved_docs, single_question)
        logger.info(f"Stage 3 (Prompt built): {prompt[:200]}...")

        answer = generate_response(
            model=data.model,
            prompt=prompt,
            api_key=data.api_key
        )
        logger.info(f"Stage 3 (Generation) answer: {answer}")

        return QueryResponse(chat_id=data.chat_id, response=answer)

    except Exception as e:
        logger.error(f"Error processing query: {e}")
        raise HTTPException(status_code=500, detail=str(e))


    
@app.get("/query/stream")
async def handle_query_stream(request: Request):
    # 1) Pull raw JSON from the ?data=… query param
    raw = request.query_params.get("data")
    if not raw:
        raise HTTPException(status_code=400, detail="Missing ⁠ data ⁠ query parameter")

    # 2) Parse into our Pydantic model
    try:
        payload = json.loads(raw)
        data = QueryRequest(**payload)
    except (ValueError, TypeError) as e:
        raise HTTPException(status_code=400, detail=f"Invalid JSON payload: {e}")
    
    async def event_generator():
        try:
            # Stage 1
            yield "event: stage\ndata: Analysing your question...\n\n"
            await asyncio.sleep(0) #

            if len(data.messages) <= 1:
                question = data.content
            else:
                convo_text = "\n".join(
                    f"{msg.role.capitalize()}: {msg.content}" for msg in data.messages
                )
                condense_prompt = (
                    "You are an expert assistant. Given the following conversation, "
                    "please summarize it into a single concise question.\n\n"
                    f"Conversation:\n{convo_text}\n\n"
                    "Single Question:"
                )
                question = generate_response(
                    model="gemini-2.5-flash",
                    prompt=condense_prompt,
                    api_key=data.api_key
                )
            logger.info(f"Stage 1 (Condense) result: {question}")

            # Stage 2
            yield "event: stage\ndata: Retrieving nodes...\n\n"
            await asyncio.sleep(0)  # 🔥 REQUIRED

            docs = graph_retriever(
                question,
                data.searchLength,
                data.extensionSize,
                request
            )
            logger.info(f"Stage 2 (Retrieval) returned {len(docs)} docs")

            # Stage 3
            yield "event: stage\ndata: Generating answer...\n\n"
            await asyncio.sleep(0)  # 🔥 REQUIRED

            final_prompt = build_prompt(docs, question)
            answer = generate_response(
                model=data.model,
                prompt=final_prompt[:600000],
                api_key=data.api_key
            )
            logger.info(f"Stage 3 (Generation) answer: {answer}")
            
            # Final result
            payload = {"chat_id": data.chat_id, "response": answer}
            yield "event: result\ndata: " + json.dumps(payload) + "\n\n"
            return
        #except Exception as e:
            # Emit an error event, then exit
            #err = {"error": str(e)}
            #yield "event: error\ndata: " + json.dumps(err) + "\n\n"
        except Exception:
            logger.exception("Unhandled exception in event_generator")
        #logging.error("Exception occurred:\n%s", tb)

            err = {
                "error": "Internal server error",
            }

            yield "event: error\ndata: " + json.dumps(err) + "\n\n"
            return

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream; charset=utf-8",
        headers={
            "Access-Control-Allow-Origin": "http://localhost:1794",
            "Access-Control-Allow-Headers": "Content-Type, Accept",
            "Access-Control-Allow-Methods": "GET",
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        },
    )
