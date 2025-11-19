# DeepSeek R1 - Web UI - Docker

This project sets up a Docker-based environment for running the DeepSeek model using Ollama and a web UI.

## Prerequisites

- Docker
- Docker Compose

## Getting Started

1. Clone the repository:
    ```sh
    git clone https://github.com/gabrielalmir/deepseek-r1-webui-docker
    cd deepseek
    ```

2. Build and start the services:
    ```sh
    docker-compose up --build
    ```

3. Access the web UI:
    Open your browser and go to `http://localhost:3000`.

## Project Structure

- `entrypoint.sh`: Script to start the Ollama service and download the DeepSeek model.
- `Dockerfile`: Dockerfile to set up the Ollama environment.
- `compose.yaml`: Docker Compose file to define and run multi-container Docker applications.

## Services

- **Ollama**: Serves the DeepSeek model.
- **Web UI**: Provides a user interface to interact with the DeepSeek model.

## Volumes

- `ollama`: Stores Ollama-related data.
- `open-webui`: Stores data for the web UI.

## Networks

- `deepseek`: Network for communication between the Ollama and web UI services.

## Environment Variables

- `OLLAMA_KEEP_ALIVE`: Keeps the Ollama service alive for 24 hours.
- `OLLAMA_HOST`: Sets the host for the Ollama service.

## Ports

- `11434`: Port for the Ollama service.
- `3000`: Port for the web UI.

## Deployment

The `compose.yaml` file includes deployment configurations, such as resource reservations for GPU capabilities.

## Acknowledgements

- [Ollama](https://ollama.com)
- [Open Web UI](https://github.com/open-webui/open-webui)
