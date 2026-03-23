FROM python:3.10-slim

WORKDIR /app

COPY . .

# RUN pip install --no-cache-dir -r requirements.txt
RUN pip install flask

EXPOSE 5001

CMD ["python", "payment.py"]