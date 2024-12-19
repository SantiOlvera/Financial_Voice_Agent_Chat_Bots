# Financial Voice Agent Chat Bots
Financial AI that interacts with you about the daily news from the Wall Street Journal and the related stock market.

<p align="center">
  <img src="https://github.com/user-attachments/assets/fc4d886c-4e30-4159-9f99-1241e990075a" alt="Financial Market Illustration">
</p>

<br>

## Team

- [Santiago Olvera Moreno](https://github.com/SantiOlvera), Data Science and Actuarial Science Double Bachelor Program student at ITAM.
- [Emiliano Bobadilla](https://github.com/BobadillaE), Data Science student at ITAM.

## Objective

The goal of this project is to develop a financial voice agent capable of providing:
- The most relevant information from the Wall Street Journal.
- Insights into the last 7 days of activity for the most important stocks.
- An overview of the daily market.

## Methodology

1. **Extract Relevant News**: Use the `Mistral 7B` large language model (LLM) to analyze the Wall Street Journal's front page and identify the sections containing the most important news.
2. **Locate News Details**: Apply regular expressions (regex) to search the entire newspaper and pinpoint the pages covering the identified news.
3. **Identify Related Stocks**: Ask the LLM to determine which stocks are mentioned in the identified news pages.
4. **Retrieve Stock Data**: Use the `yfinance` library to gather data for the related stocks over the past 7 days.
5. **Summarize Articles**: Generate detailed summaries of the identified articles.
6. **System Prompt Setup**: Compile all the information (summaries and stock data) into a system prompt, enabling the `Mistral 7B` LLM to contextualize its responses.
7. **Speech Integration**: Implement connections for Speech-to-Text (STT), Text-to-Text (TTT), and Text-to-Speech (TTS) functionalities using `Deepgram` and `Groq`.

## Usage

1. Install the required dependencies using the `requirements.txt` file.
2. Install `ffplay` via Homebrew:
   ```bash
   brew install ffmpeg
   ```
3. Obtain free API keys from:
   - [Deepgram](https://deepgram.com)
   - [Groq](https://console.groq.com/playground)
4. Add the API keys to your environment variables or configuration file.
5. Run the script to parse the system prompt:
   ```bash
   python3 parser_pdf.py
   ```
6. Run the application:
   ```bash
   streamlit run app.py
   ```

## Hugging Face Space

1. For Text-to-Text (TTT) usage only: [Finance Agent](https://huggingface.co/spaces/capi10/Finance_Agent).
2. For Speech-to-Text (STT), Text-to-Text (TTT), and Text-to-Speech (TTS) integration: [Finance Voice Agent](https://huggingface.co/spaces/capi10/finance_voice_agent) (Note: Hugging Face currently does not support Homebrew installations. That is why the microphone and audio does not work).

## Video Dashboard (Streamlit)

[Watch the video demonstration](https://www.dropbox.com/scl/fi/2gicgzr3ncvw3ethmbp3x/financial-voice-agent.mp4?rlkey=o24v4olm7xils5yac5xiwzmsq&st=nhs2cutk&dl=0)


