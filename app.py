# app.py
# Final Corrected MVP with enhanced error logging to expose the root cause.

import os
import json
import asyncio
import base64
import traceback # Import the traceback module
from dotenv import load_dotenv
from fastapi import FastAPI, WebSocket
from twilio.twiml.voice_response import VoiceResponse, Connect
from deepgram import DeepgramClient, LiveTranscriptionEvents, LiveOptions
import google.generativeai as genai
from elevenlabs.client import AsyncElevenLabs

# --- Initialization ---
load_dotenv()
app = FastAPI()

# Load API keys from environment
DEEPGRAM_API_KEY = os.getenv("DEEPGRAM_API_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY")

# Configure API clients
genai.configure(api_key=GEMINI_API_KEY)
elevenlabs_client = AsyncElevenLabs(api_key=ELEVENLABS_API_KEY)

# Configure the Gemini Model
llm_model = genai.GenerativeModel(model_name="gemini-1.5-flash-latest")
print("--- ALL API CLIENTS CONFIGURED SUCCESSFULLY ---")


# --- Knowledge Base Loading ---
def load_knowledge_base():
    try:
        with open("knowledge_base/config.json") as f:
            config = json.load(f)
        with open("knowledge_base/menu.json") as f:
            menu = json.load(f)
        with open("knowledge_base/faq.json") as f:
            faq = json.load(f)
        
        system_prompt = f"""
You are Lexi, a friendly, efficient, and conversational AI assistant for a restaurant called {config['restaurant_name']}.
Your personality is helpful and concise. Your goal is to answer customer questions and take food orders.
Use the information provided below to answer questions. Do not make up information.

Restaurant Story: {config['story']}
Cuisine Type: {config['cuisine_type']}
Full Menu: {json.dumps(menu, indent=2)}
Frequently Asked Questions: {json.dumps(faq, indent=2)}
"""
        print("--- KNOWLEDGE BASE LOADED SUCCESSFULLY ---")
        return system_prompt, config.get("initial_greeting", "Hello, how can I help you?")
    except FileNotFoundError as e:
        print(f"!!! KNOWLEDGE BASE FILE NOT FOUND: {e}. !!!")
        return None, None

SYSTEM_PROMPT, INITIAL_GREETING = load_knowledge_base()


# --- Main HTTP Endpoint ---
@app.post("/incoming-call")
def handle_incoming_call():
    print("--- INCOMING CALL DETECTED ---")
    response = VoiceResponse()
    connect = Connect()
    # IMPORTANT: Replace with your ngrok URL
    connect.stream(url=f"wss://7a8dda521fbb.ngrok-free.app/stream")
    response.append(connect)
    print("--- TwiML RESPONSE SENT TO TWILIO TO START STREAM ---")
    from fastapi.responses import Response
    return Response(content=str(response), media_type="text/xml")


# --- WebSocket Handler ---
@app.websocket("/stream")
async def stream_handler(websocket: WebSocket):
    await websocket.accept()
    print("--- WEBSOCKET CONNECTION OPENED ---")

    conversation_history = [{"role": "user", "parts": [SYSTEM_PROMPT]}, {"role": "model", "parts": [INITIAL_GREETING]}]
    
    # This function sends audio data back to Twilio
    async def text_to_speech_sender(ws: WebSocket, text_queue: asyncio.Queue, stream_sid: str):
        print("--- TTS SENDER TASK STARTED ---")
        while True:
            try:
                text_to_speak = await text_queue.get()
                if text_to_speak is None:
                    break
                
                # --- THIS IS THE FIX ---
                # The .stream() method returns an async generator, which we loop over directly
                # without an 'await' on the initial call.
                audio_stream = elevenlabs_client.text_to_speech.stream(
                    text=text_to_speak,
                    voice_id="i4CzbCVWoqvD0P1QJCUL", # Make sure this is updated
                    model_id="eleven_multilingual_v2",
                    output_format="ulaw_8000"
                )

                async for audio_chunk in audio_stream:
                    media_response = {
                        "event": "media",
                        "streamSid": stream_sid,
                        "media": { "payload": base64.b64encode(audio_chunk).decode('utf-8') }
                    }
                    await ws.send_text(json.dumps(media_response))

            except Exception as e:
                # We now print the full traceback to see the real, underlying error.
                print(f"!!! TTS SENDER ERROR !!!")
                traceback.print_exc()
        
        print("--- TTS SENDER TASK FINISHED ---")


    # This function processes transcriptions and calls the LLM
    async def llm_processor(transcription_queue: asyncio.Queue, text_queue: asyncio.Queue):
        print("--- LLM PROCESSOR TASK STARTED ---")
        await text_queue.put(INITIAL_GREETING)

        while True:
            transcript = await transcription_queue.get()
            if transcript is None:
                break
            
            print(f"   >>> User said: {transcript}")
            conversation_history.append({"role": "user", "parts": [transcript]})
            
            try:
                response = await llm_model.generate_content_async(conversation_history)
                llm_response_text = response.text
                conversation_history.append({"role": "model", "parts": [llm_response_text]})
                print(f"   >>> Lexi's thought: {llm_response_text}")
                await text_queue.put(llm_response_text)
            except Exception as e:
                print(f"!!! GEMINI API ERROR !!!")
                traceback.print_exc()

        await text_queue.put(None)
        print("--- LLM PROCESSOR TASK FINISHED ---")

    # This function handles Deepgram transcription
    async def deepgram_sender(audio_queue: asyncio.Queue, transcription_queue: asyncio.Queue):
        print("--- DEEPGRAM SENDER TASK STARTED ---")
        try:
            deepgram = DeepgramClient(DEEPGRAM_API_KEY)
            dg_connection = deepgram.listen.asynclive.v("1")
            async def on_message(self, result, **kwargs):
                transcript = result.channel.alternatives[0].transcript
                if len(transcript) > 0:
                    await transcription_queue.put(transcript)
            dg_connection.on(LiveTranscriptionEvents.Transcript, on_message)
            options = LiveOptions(model="nova-2", language="en-US", smart_format=True, encoding="mulaw", channels=1, sample_rate=8000)
            await dg_connection.start(options)
            while True:
                payload = await audio_queue.get()
                if payload is None: break
                await dg_connection.send(base64.b64decode(payload))
            await dg_connection.finish()
        except Exception as e:
            print(f"!!! DEEPGRAM SENDER ERROR !!!")
            traceback.print_exc()
        finally:
            await transcription_queue.put(None)
            print("--- DEEPGRAM SENDER TASK FINISHED ---")

    # This function receives audio from Twilio
    async def receive_from_twilio(ws: WebSocket, audio_queue: asyncio.Queue):
        print("--- TWILIO RECEIVER TASK STARTED ---")
        stream_sid = None
        try:
            while True:
                message = await ws.receive_text()
                packet = json.loads(message)
                if packet['event'] == 'start':
                    stream_sid = packet['start']['streamSid']
                    print(f"--- TWilio MEDIA STREAM STARTED (SID: {stream_sid}) ---")
                elif packet['event'] == 'media':
                    await audio_queue.put(packet['media']['payload'])
                elif packet['event'] == 'stop':
                    print("--- TWILIO MEDIA STREAM STOPPED ---")
                    break
        except Exception as e:
            print(f"!!! TWILIO RECEIVER ERROR !!!")
            traceback.print_exc()
        finally:
            await audio_queue.put(None)
            print("--- TWILIO RECEIVER TASK FINISHED ---")
            return stream_sid

    # Setup queues and tasks
    audio_queue = asyncio.Queue()
    transcription_queue = asyncio.Queue()
    text_to_speak_queue = asyncio.Queue()

    stream_sid = await receive_from_twilio(websocket, audio_queue)
    
    if stream_sid:
        tasks = [
            deepgram_sender(audio_queue, transcription_queue),
            llm_processor(transcription_queue, text_to_speak_queue),
            text_to_speech_sender(websocket, text_to_speak_queue, stream_sid)
        ]
        await asyncio.gather(*tasks)
    
    print("--- WEBSOCKET CONNECTION CLOSED ---")
