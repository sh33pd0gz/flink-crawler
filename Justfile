version := 'dev'

build:
  docker buildx build --platform linux/arm64 -t flink-crawler:latest .

load:
  kind load docker-image flink-crawler:latest --name flink-local

deploy:
  kubectl apply -f example.yaml
