# Deployment Guide

This guide covers deployment options for the Multi-Client Trading Platform.

## Development Deployment

```bash
docker-compose up -d
```

## Production Deployment

```bash
docker-compose -f docker-compose.prod.yml up -d
```

## Kubernetes Deployment

```bash
kubectl apply -f infra/k8s/
```
