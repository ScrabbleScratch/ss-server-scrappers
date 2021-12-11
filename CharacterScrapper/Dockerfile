FROM python:3
WORKDIR /scrapper
ADD . .
RUN pip install -r requirements.txt
VOLUME ["/scrapper/config", "/scrapper/logs"]
CMD ["python3", "CharacterScrapperMQTT.py"]