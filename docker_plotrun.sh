echo "running web service on http://localhost:5050"
docker run -p 5050:5000 -v $(pwd):/app -it maxima-web
#docker run -p 5050:5000 -v $(pwd):/app -d  maxima-web

