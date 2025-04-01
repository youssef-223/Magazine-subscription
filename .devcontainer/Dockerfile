FROM mcr.microsoft.com/vscode/devcontainers/python:3

ENV PYTHONUNBUFFERED 1

RUN apt-get update && export DEBIAN_FRONTEND=noninteractive \
    && apt-get -y install --no-install-recommends postgresql-client

# Set the working directory inside the container
WORKDIR /workspace/src