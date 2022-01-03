docker run -dit \
    --name=AnimeScrapper \
    --restart=unless-stopped \
    --network=host \
    -v /mnt/DISk/AppData/AnimeScrapper/config:/scrapper/config \
    -v /mnt/DISk/AppData/AnimeScrapper/logs:/scrapper/logs \
    anime-scrapper:mqtt