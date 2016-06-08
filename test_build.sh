docker kill postgres
docker rm postgres

docker kill test_soccer
docker rm test_soccer

docker pull postgres
docker build -t test_soccer .
docker run --name postgres -e POSTGRES_USER=dburnett -e POSTGRES_PASSWORD=doug1 -e POSTGRES_DB=Soccer_Games -d postgres
docker run --name test_soccer --link postgres:postgres -e TEST=1 -d test_soccer tail -f /dev/null

# not working for some reason...  You will need to manually run this create_tables.py file before running.
#docker exec test_soccer python create_tables.py

## You may now run 'docker exec -it test_soccer /bin/bash' to perform local testing against the empty db.
