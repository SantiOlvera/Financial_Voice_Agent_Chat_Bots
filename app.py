import asyncio
import time
import os
import shutil
import subprocess
import requests
import streamlit as st
from dotenv import load_dotenv
import datetime

from langchain_core.prompts import ChatPromptTemplate
from langchain_groq import ChatGroq
from langchain.memory import ConversationBufferMemory
from langchain.prompts import (
    ChatPromptTemplate,
    MessagesPlaceholder,
    SystemMessagePromptTemplate,
    HumanMessagePromptTemplate,
)
from langchain.chains import LLMChain

from deepgram import (
    DeepgramClient,
    DeepgramClientOptions,
    LiveTranscriptionEvents,
    LiveOptions,
    Microphone,
)

# Cargar las variables de entorno
load_dotenv()

class LanguageModelProcessor:
    def __init__(self):
        self.llm = ChatGroq(temperature=0, model_name="mixtral-8x7b-32768", groq_api_key=os.getenv("GROQ_API_KEY"))
        self.memory = ConversationBufferMemory(memory_key="chat_history", return_messages=True)

        with open('system_prompt_en.txt', 'r') as file:
            system_prompt = file.read().strip()
        
        self.prompt = ChatPromptTemplate.from_messages([
            SystemMessagePromptTemplate.from_template(system_prompt),
            MessagesPlaceholder(variable_name="chat_history"),
            HumanMessagePromptTemplate.from_template("{text}")
        ])

        self.conversation = LLMChain(
            llm=self.llm,
            prompt=self.prompt,
            memory=self.memory
        )

    def process(self, text):
        self.memory.chat_memory.add_user_message(text)

        start_time = time.time()

        response = self.conversation.invoke({"text": text})
        end_time = time.time()

        self.memory.chat_memory.add_ai_message(response['text'])

        elapsed_time = int((end_time - start_time) * 1000)
        return response['text']

class TextToSpeech:
    DG_API_KEY = os.getenv("DEEPGRAM_API_KEY")
    MODEL_NAME = "aura-asteria-en"

    @staticmethod
    def is_installed(lib_name: str) -> bool:
        return shutil.which(lib_name) is not None

    def speak(self, text):
        if not self.is_installed("ffplay"):
            raise ValueError("ffplay no encontrado, necesario para reproducir audio.")

        DEEPGRAM_URL = f"https://api.deepgram.com/v1/speak?model={self.MODEL_NAME}"
        headers = {
            "Authorization": f"Token {self.DG_API_KEY}",
            "Content-Type": "application/json"
        }
        payload = {
            "text": text
        }

        player_command = ["ffplay", "-autoexit", "-", "-nodisp"]
        player_process = subprocess.Popen(
            player_command,
            stdin=subprocess.PIPE,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )

        with requests.post(DEEPGRAM_URL, stream=True, headers=headers, json=payload) as r:
            for chunk in r.iter_content(chunk_size=1024):
                if chunk:
                    player_process.stdin.write(chunk)
                    player_process.stdin.flush()

        player_process.stdin.close()
        player_process.wait()

class TranscriptCollector:
    def __init__(self):
        self.reset()

    def reset(self):
        self.transcript_parts = []

    def add_part(self, part):
        self.transcript_parts.append(part)

    def get_full_transcript(self):
        return ' '.join(self.transcript_parts)

transcript_collector = TranscriptCollector()

async def get_transcript(callback):
    transcription_complete = asyncio.Event()

    try:
        config = DeepgramClientOptions(options={"keepalive": "true"})
        deepgram = DeepgramClient("", config)

        dg_connection = deepgram.listen.asynclive.v("1")

        async def on_message(self, result, **kwargs):
            sentence = result.channel.alternatives[0].transcript
            
            if not result.speech_final:
                transcript_collector.add_part(sentence)
            else:
                transcript_collector.add_part(sentence)
                full_sentence = transcript_collector.get_full_transcript()
                if len(full_sentence.strip()) > 0:
                    full_sentence = full_sentence.strip()
                    callback(full_sentence)
                    transcript_collector.reset()
                    transcription_complete.set()

        dg_connection.on(LiveTranscriptionEvents.Transcript, on_message)

        options = LiveOptions(
            model="nova-2",
            punctuate=True,
            language="en",
            encoding="linear16",
            channels=1,
            sample_rate=16000,
            endpointing=300,
            smart_format=True,
        )

        await dg_connection.start(options)

        microphone = Microphone(dg_connection.send)
        microphone.start()

        await transcription_complete.wait()

        microphone.finish()

        await dg_connection.finish()

    except Exception as e:
        print(f"No se pudo abrir el socket: {e}")
        return

class ConversationManager:
    def __init__(self):
        self.transcription_response = ""
        self.llm = LanguageModelProcessor()

    async def main(self, transcription_display_callback, response_display_callback):
        def handle_full_sentence(full_sentence):
            self.transcription_response = full_sentence
            transcription_display_callback(full_sentence)  # Actualiza el texto de la transcripción

        while True:
            await get_transcript(handle_full_sentence)
            
            if "goodbye" in self.transcription_response.lower():
                break

            llm_response = self.llm.process(self.transcription_response)
            response_display_callback(llm_response)  # Actualiza el texto de la respuesta del modelo
            tts = TextToSpeech()
            tts.speak(llm_response)

            self.transcription_response = ""

def run_conversation(transcription_display_callback, response_display_callback):
    manager = ConversationManager()
    asyncio.run(manager.main(transcription_display_callback, response_display_callback))

# Streamlit UI Configuration
today = datetime.date.today()

##Put the title of the app Finace agent of todays market and put the variable of today
st.title(f'{today} Finance Agent of Today Market')

transcription_text_area = st.empty()  # Área para mostrar la transcripción
response_text_area = st.empty()  # Área para mostrar la respuesta del modelo

if st.button("Start Conversation"):
    transcription_text_area.text_area("Text Received", height=200)
    response_text_area.text_area("Model Response", height=200)

    # Llama a la función que ejecutará la conversación
    run_conversation(
        transcription_display_callback=lambda text: transcription_text_area.text_area("Text Received", value=text, height=200),
        response_display_callback=lambda text: response_text_area.text_area("Model Response", value=text, height=200)
    )
