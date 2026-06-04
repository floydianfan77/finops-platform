# infra

Infrastructure-as-config for the FinOps platform. Grows over time.

## Planned layout

```
infra/
├── broker/     # Broker config (Kafka or Red Panda) + topic provisioning  [step 2]
├── docker/     # Shared Dockerfiles / base images
└── k8s/        # Kubernetes manifests / Helm charts                        [later]
```

For local development, the root [`docker-compose.yml`](../docker-compose.yml) is the
entry point. It already contains ready-to-enable blocks for both Red Panda and Kafka.
