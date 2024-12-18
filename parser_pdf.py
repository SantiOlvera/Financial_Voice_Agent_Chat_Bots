from PyPDF2 import PdfReader
from groq import Groq
import re
from langchain_core.prompts import ChatPromptTemplate
from langchain_groq import ChatGroq
from dotenv import load_dotenv
import os
import yfinance as yf
import datetime
import pandas as pd
from langchain_groq import ChatGroq


load_dotenv()

# Función para extraer texto de PDFs
def extract_text_from_pdf(pdf_path):
    reader = PdfReader(pdf_path)
    text = ''
    for page in reader.pages:
        text += page.extract_text()
    return text

path='pdf/cover.pdf'

text0 = extract_text_from_pdf(path)

path='pdf/wall_street.pdf'

text=extract_text_from_pdf(path)

# In[ ]:

##Parte para extrer los articulos mas relevantes de la portada del wall street journal
chat = ChatGroq(temperature=0, model_name="mixtral-8x7b-32768",max_tokens=256, timeout=None, max_retries=3, groq_api_key=os.getenv("GROQ_API_KEY"))

messages = [
    (
        "system",
        "You are an expert in stocks. So you have to find the most interesting articles of the new york times There are a lot of small fragments of news that they are later explained in the article. I need to have the top 3 better articles related to the stock market and u have to indicate how I can identify them. This is baisically by a letter and a number. For example, A2, A3, B1, B2, B3, etc. Be careful with the number of the articles",
    ),
    ("human", "Find the most interesting articles of the financial times related to the stock market in this text."),
    ("human", text0)]

ai_msg = chat.invoke(messages)
ai_msg.content

##Parte para refinar la extracción de los articulos en formato de array ['A1', 'A2', 'B1']
messages2 = [
    (
        "system",
        "You are an expert identifiying where to find the article of a related topic. U will hace 3 articles and I can find them by a letter and a number. For example, A1, A2, A3, B1, B2, B3, etc.. The output have to be an array. For example, ['A1', 'B2', 'C3']",
    ),
    ("human", "Find how to identify the articles of the financial times related to the stock market in this text."),
    ("human", ai_msg.content)]

ai_msg2 = chat.invoke(messages2)
ai_msg2.content
aux=ai_msg2.content[ai_msg2.content.find('['):ai_msg2.content.find(']')+1]

## get the array of the articles from this format "['A1', 'A6', 'B11']"

aux=aux.replace('[','')
aux=aux.replace(']','')
aux=aux.replace('\'','')
aux=aux.replace(' ','')
aux=aux.split(',')

##Un pequeño fix en el que si hay un A1 lo cambia por A2, pues A1 es la portada, sin embargo, A2 es el primer articulo
for i in range(len(aux)):
    if aux[i]=='A1':
        aux[i]='A2'

# In[67]:


# Código para poder identifcar las páginas de los articulos preseleccionados
pattern = r'(?:[AB]\d+\s*\|\s*)?[A-Z][a-z]+,\s(?:January|February|March|April|May|June|July|August|September|October|November|December)\s(?:[1-9]|[12][0-9]|3[01]),\s2024(?:\s*\|\s*[AB]\d+)?'

# Encontrar todos los encabezados en el texto
matches = list(re.finditer(pattern, text))

# Extraer el contenido de cada sección correspondiente a las páginas en `aux`
sections = {}
for i, match in enumerate(matches):
    # Obtener el encabezado actual
    header = match.group(0)
    
    # Verificar si el encabezado incluye una página relevante de `aux`
    if any(page in header for page in aux):
        # Encontrar el inicio y final de la sección
        start = match.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)

        #print(f"Header: {header}\nContent: {text[start:end].strip()}\n{'-'*40}")
        
        # Extraer el contenido entre este encabezado y el siguiente
        sections[header] = text[start:end].strip()

# In[93]:

##Función para poder econtrar los stocks relacionados con los articulos
res=[]
for i in sections.items():
    ##tomar el contenido de i[1] y dividirlo en el len entre 4 luego tomar 

    ## se pone la condición de no superar los 5000 tokens, pues es lo máximo que sopoorta el modelo
    if len(i[1])/3.2>5000:
        texto=i[1][:int(len(i[1])*5000/len(i[1])/3.2)]
    else:
        texto=i[1]

    ##numero
    messages3 = [
    (
        "system",
        "You are an expert identifying relevant the top 3 stocks from the articles provided by the financial times. You have to find the most relevant stocks in the articles. The output has to be an array. For example, ['NVDA', 'AAPL', 'TSLA']",
    ),
    ("human", "Find the most relevant stocks in the articles provided by the financial times."),
    ("human", texto)]
    ai_msg3 = chat.invoke(messages3)
    res.append(ai_msg3.content)

# In[ ]:

##Función para poder econtrar los stocks relacionados con los articulos y me lo de en formato de array y con la notación de bloomberg
stocks=[]
for i in res:
    messages4 = [
    (
        "system",
        "You are an expert identifiying the stocks of a text. U need to put in an array the top 3 stocks of the text. The output has to be like this, ['NVDA', 'AAPL', 'TSLA'], the name of the companies has to be in the bloomberg format.",),
    ("human", "Find the stocks from the following text an give to me in an array."),
    ("human", i)]
    ai_msg4 = chat.invoke(messages4)
    ai_msg4.content
    aux2=ai_msg4.content[ai_msg4.content.find('['):ai_msg4.content.find(']')+1]
    aux2=aux2.replace('[','')
    aux2=aux2.replace(']','')
    aux2=aux2.replace('\'','')
    aux2=aux2.replace(' ','')
    aux2=aux2.split(',')
    stocks.append(aux2)

stock=[]
for i in stocks:
    for j in i:
        stock.append(j)
    
stock = list(dict.fromkeys(stock))

# In[119]:


# Función para extraer los precios de las acciones de yahoo finance de los últimos 7 días
date_today = datetime.date.today()

stock_data = {}

for i in stock:
    # Download the data
    data = yf.download(i, start=date_today - datetime.timedelta(days=7), end=date_today)
    stock_data[i] = data[['Open', 'Low', 'Close']]


# In[122]:

##Modelo que me va a hacer los reusmenes de las partes de los articulos preseleccionados
chat2 = ChatGroq(temperature=0, model_name="mixtral-8x7b-32768",max_tokens=1500, timeout=None, max_retries=3, groq_api_key=os.getenv("GROQ_API_KEY"))

res2=[]
for i in sections.items():
    ##tomar el contenido de i[1] y dividirlo en el len entre 4 luego tomar 


    if len(i[1])/3.2>5000:
        texto=i[1][:int(len(i[1])*5000/len(i[1])/3.2)]
    else:
        texto=i[1]

    ##numero
    messages6 = [
    (
        "system",
        "You are an expert in finance, so you have to make a summary of the following text, dont miss the details."),
    ("human", "Give mi the summary of the following text."),
    ("human", texto)]
    ai_msg6 = chat2.invoke(messages6)
    res2.append(ai_msg6.content)


# In[127]:

##Función para poner en un archivo de texto los resumenes de los articulos y los precios de las acciones
date_today = datetime.date.today()


with open(f"news_{date_today}.txt", "w") as f:
    f.write("You are a financial expert specializing in investment banking, trading, and market analysis. Your task is to provide an overview of the market today and identify potential market opportunities based on the latest news and stock data provided. Analyze the key events, stock movements, and economic indicators to guide trading strategies and investment decisions.\n\n")
    f.write("The news of todays market are the following\n")
    for item in res2:
        f.write("%s\n" % item)
    f.write("\n")
    f.write("The stocks related to the news are the following\n")
    for ticker, df in stock_data.items():
        f.write(f"Prices for {ticker}:\n")
        f.write(f"{df}\n")
