# SoccerInfo
To run a scraper you first need to install docker from `https://docs.docker.com/mac/step_one/`.  After installed migrate to the directory where the scrapers live
and run `docker build .`. From there you should see an image that was built at the end.  You can then run `docker run {imageId}` to run the docker container.
For more advanced commands see docker.com


Current production run for soccer_city scraper
docker build -t scraper .
docker run --net="host" scraper python -c 'import soccer_city; soccer_city.lets_play_run()
