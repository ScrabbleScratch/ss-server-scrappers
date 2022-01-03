docker run -dit \
    --name=CharacterScrapper \
    --restart=unless-stopped \
    --network=host \
    -v /mnt/DISk/AppData/CharacterScrapper/config:/scrapper/config \
    -v /mnt/DISk/AppData/CharacterScrapper/logs:/scrapper/logs \
    character-scrapper:mqtt