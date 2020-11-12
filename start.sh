ready=true

if [ ! -f  ./docker/web/.env.dev.web ] 
then
    $ready = false
    echo "Missing ./docker/web/.env.dev.web file"
fi

if [ ! -f  ./docker/db/.env.dev.db ] 
then
    $ready = false
    echo "Missing ./docker/db/.env.dev.db file"
fi

if [ ! -f  ./docker/worker/.env.dev.worker ] 
then
    $ready = false
    echo "Missing ./docker/worker/.env.dev.worker file"
fi

if [ ! $ready ]
then
    exit 0
fi

# run docker
docker-compose -f ./docker/docker-compose.yml up --build --detach
echo "You can now access the web server at http://127.0.0.1:8000/"