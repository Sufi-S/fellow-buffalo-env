FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 7860

# Run Gradio app instead of FastAPI for better UI
CMD ["python", "gradio_app.py"]