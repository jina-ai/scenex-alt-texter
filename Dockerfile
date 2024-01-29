FROM python:3.8

ARG GHOST_API_KEY
ARG GHOST_BLOG_URL
ARG SCENEX_API_KEY
#RUN apt-get update && \
#apt-get install -y git

#RUN git clone git@github.com:jina-ai/scenex-ghost-blog-alt-tagger.git /usr/src/app

# Set the working directory in the container
WORKDIR /usr/src/app

# Copy the current directory contents into the container at /usr/src/app
COPY . .

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Set environment variables
ENV GHOST_API_KEY=${GHOST_API_KEY}
ENV GHOST_BLOG_URL=${GHOST_BLOG_URL}
ENV SCENEX_API_KEY=${SCENEX_API_KEY}

# Run script.py when the container launches
CMD ["python", "./app.py"]
