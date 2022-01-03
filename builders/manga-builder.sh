docker run -dit \
    --name=MangaScrapper \
    --restart=unless-stopped \
    --network=host \
    -v /mnt/DISk/AppData/MangaScrapper/config:/scrapper/config \
    -v /mnt/DISk/AppData/MangaScrapper/logs:/scrapper/logs \
    manga-scrapper:mqtt