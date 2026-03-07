# Flink Web Crawler

### Kubernetes Cluster Setup

`colima start --cpu 4 --memory 8 --disk 50 --runtime docker`
`kind create cluster --name flink-local`
`kubectl config set-cotext kind-flink-local `

### Terraform Initialization

`cd infra`
`terraform init`
`terraform apply`

