FROM mcr.microsoft.com/vscode/devcontainers/python:3.11

# Expose the port used by your application (if it's 8000)
EXPOSE 8000

# Set the working directory
WORKDIR /workspace
ENV PYTHONPATH="/workspace/plombery/examples"

RUN if [ "20" != "none" ]; then su vscode -c "umask 0002 && . /usr/local/share/nvm/nvm.sh && nvm install 20 2>&1"; fi

RUN mkdir -p /workspace/examples 
COPY . /workspace
RUN cd /workspace/examples && pip3 install -r requirements.txt && cd /workspace/frontend && yarn && yarn build
CMD ["/bin/bash", "-c", "cd", "/workspace/plombery/examples", "&&", "./run.sh"]
