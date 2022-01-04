docker stop AnimeScrapper && docker rm AnimeScrapper
docker stop CharacterScrapper && docker rm CharacterScrapper
docker stop MangaScrapper && docker rm MangaScrapper
docker rmi anime-scrapper character-scrapper manga-scrapper
docker rmi anime-scrapper:mqtt character-scrapper:mqtt manga-scrapper:mqtt
docker build -t anime-scrapper AnimeScrapper
docker build -t character-scrapper CharacterScrapper
docker build -t manga-scrapper MangaScrapper
