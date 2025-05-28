#!/bin/bash
# infra/k8s/deploy.sh

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
NAMESPACE="trading-platform"
KUBE_CONFIG_PATH="${HOME}/.kube/config"

echo -e "${GREEN}Starting Kubernetes deployment for Multi-Client Trading Platform${NC}"

# Check if kubectl is installed
if ! command -v kubectl &> /dev/null; then
    echo -e "${RED}kubectl is not installed. Please install kubectl first.${NC}"
    exit 1
fi

# Check if cluster is accessible
if ! kubectl cluster-info &> /dev/null; then
    echo -e "${RED}Cannot connect to Kubernetes cluster. Please check your kubectl configuration.${NC}"
    exit 1
fi

echo -e "${YELLOW}Connected to Kubernetes cluster${NC}"

# Function to wait for deployment
wait_for_deployment() {
    local deployment_name=$1
    local namespace=$2
    echo -e "${YELLOW}Waiting for deployment ${deployment_name} to be ready...${NC}"
    kubectl wait --for=condition=available --timeout=300s deployment/${deployment_name} -n ${namespace}
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}Deployment ${deployment_name} is ready${NC}"
    else
        echo -e "${RED}Deployment ${deployment_name} failed to become ready${NC}"
        return 1
    fi
}

# Function to apply configuration
apply_config() {
    local file=$1
    echo -e "${YELLOW}Applying configuration: ${file}${NC}"
    kubectl apply -f ${file}
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}Successfully applied ${file}${NC}"
    else
        echo -e "${RED}Failed to apply ${file}${NC}"
        return 1
    fi
}

# Create namespace
echo -e "${YELLOW}Creating namespace...${NC}"
apply_config "namespace.yaml"

# Apply RBAC configuration
echo -e "${YELLOW}Setting up RBAC...${NC}"
apply_config "rbac.yaml"

# Deploy PostgreSQL
echo -e "${YELLOW}Deploying PostgreSQL...${NC}"
apply_config "postgres.yaml"
wait_for_deployment "postgres" "${NAMESPACE}"

# Deploy Redis
echo -e "${YELLOW}Deploying Redis...${NC}"
apply_config "redis.yaml"
wait_for_deployment "redis" "${NAMESPACE}"

# Deploy Backend
echo -e "${YELLOW}Deploying Backend...${NC}"
apply_config "backend.yaml"
wait_for_deployment "backend" "${NAMESPACE}"

# Deploy Frontend
echo -e "${YELLOW}Deploying Frontend...${NC}"
apply_config "frontend.yaml"
wait_for_deployment "frontend" "${NAMESPACE}"

# Apply Ingress configuration
echo -e "${YELLOW}Setting up Ingress...${NC}"
apply_config "ingress.yaml"

# Check deployment status
echo -e "${YELLOW}Checking deployment status...${NC}"
kubectl get pods -n ${NAMESPACE}
kubectl get services -n ${NAMESPACE}
kubectl get ingress -n ${NAMESPACE}

# Get external IP
echo -e "${YELLOW}Getting external access information...${NC}"
INGRESS_IP=$(kubectl get ingress trading-platform-ingress -n ${NAMESPACE} -o jsonpath='{.status.loadBalancer.ingress[0].ip}')
if [ -z "$INGRESS_IP" ]; then
    INGRESS_IP=$(kubectl get ingress trading-platform-ingress -n ${NAMESPACE} -o jsonpath='{.status.loadBalancer.ingress[0].hostname}')
fi

if [ ! -z "$INGRESS_IP" ]; then
    echo -e "${GREEN}Application is accessible at: http://${INGRESS_IP}${NC}"
    echo -e "${GREEN}API is accessible at: http://${INGRESS_IP}/api/v1${NC}"
else
    echo -e "${YELLOW}Ingress IP not yet assigned. Run 'kubectl get ingress -n ${NAMESPACE}' to check later.${NC}"
fi

# Show useful commands
echo -e "${GREEN}Deployment completed successfully!${NC}"
echo -e "${YELLOW}Useful commands:${NC}"
echo "  View pods: kubectl get pods -n ${NAMESPACE}"
echo "  View logs: kubectl logs -f deployment/backend -n ${NAMESPACE}"
echo "  View services: kubectl get services -n ${NAMESPACE}"
echo "  Scale deployment: kubectl scale deployment backend --replicas=3 -n ${NAMESPACE}"
echo "  Delete deployment: kubectl delete namespace ${NAMESPACE}"

# Health check
echo -e "${YELLOW}Performing health check...${NC}"
sleep 10
BACKEND_POD=$(kubectl get pods -n ${NAMESPACE} -l app=backend -o jsonpath='{.items[0].metadata.name}')
if [ ! -z "$BACKEND_POD" ]; then
    kubectl exec -n ${NAMESPACE} ${BACKEND_POD} -- curl -f http://localhost:8000/health
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}Backend health check passed${NC}"
    else
        echo -e "${YELLOW}Backend health check failed - application may still be starting${NC}"
    fi
fi

echo -e "${GREEN}Kubernetes deployment script completed!${NC}"