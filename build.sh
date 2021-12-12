docker rmi anime-scrapper:mqtt character-scrapper:mqtt manga-scrapper:mqtt
docker build -t anime-scrapper:mqtt AnimeScrapper
docker build -t character-scrapper:mqtt CharacterScrapper
docker build -t manga-scrapper:mqtt MangaScrapper
