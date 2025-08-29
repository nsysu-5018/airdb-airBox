# airdb-model_airBox

## Build and Run

Build the Docker image:

```bash
docker build -t airbox .
```

Run the container:

```bash
docker run -p 8001:8000 --name airbox-container --rm airbox
```

The backend will now be available at: http://127.0.0.1:8001

## API Usage

Example: send a request to the /run endpoint:

```bash
curl -X POST "http://127.0.0.1:8001/run" \
  -H "Content-Type: application/json" \
  -d '{"address": "target_address"}'
```

## Development

To enter the running container for debugging:

```bash
docker exec -it airbox-container /bin/bash
```
