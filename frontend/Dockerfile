FROM python:3.10

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

# copy frontend app files
COPY . .

EXPOSE 8501

# Use env var STREAMLIT_SERVER_ENABLECORS to avoid CORS issues in container
ENV STREAMLIT_SERVER_ENABLECORS=false
ENV STREAMLIT_SERVER_HEADLESS=true
ENV STREAMLIT_SERVER_PORT=8501
ENV STREAMLIT_SERVER_ADDRESS=0.0.0.0

CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]
