FROM python:3.12-alpine3.21
WORKDIR /usr/src/app
COPY . .
RUN pip install -r requirements.txt
CMD ["python", "-m", "amulet_discord_bot"] 
