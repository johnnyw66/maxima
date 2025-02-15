FROM debian:latest

# Install Maxima and dependencies
RUN apt-get update && apt-get install -y \
    maxima \
    maxima-doc \
    gnuplot \
    texlive \
    imagemagick \
    python3 \
    python3-flask \
    && rm -rf /var/lib/apt/lists/*

# Create a basic Maxima web server script
WORKDIR /app
COPY maxima_web.py .

# Expose the web server port
EXPOSE 5000

# Run the web server on container start
CMD ["python3", "/app/maxima_web.py"]


