#!/bin/bash

set -e

echo "🚀 Deploying SEO Health Report Enterprise Infrastructure"

# Configuration
ENVIRONMENT=${1:-production}
AWS_REGION=${AWS_REGION:-us-east-1}
CLUSTER_NAME="seo-health-cluster"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

log() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')] $1${NC}"
}

warn() {
    echo -e "${YELLOW}[$(date +'%Y-%m-%d %H:%M:%S')] WARNING: $1${NC}"
}

error() {
    echo -e "${RED}[$(date +'%Y-%m-%d %H:%M:%S')] ERROR: $1${NC}"
    exit 1
}

# Check prerequisites
check_prerequisites() {
    log "Checking prerequisites..."
    
    command -v docker >/dev/null 2>&1 || error "Docker is required"
    command -v aws >/dev/null 2>&1 || error "AWS CLI is required"
    command -v terraform >/dev/null 2>&1 || error "Terraform is required"
    command -v kubectl >/dev/null 2>&1 || error "kubectl is required"
    
    # Check AWS credentials
    aws sts get-caller-identity >/dev/null 2>&1 || error "AWS credentials not configured"
    
    log "Prerequisites check passed"
}

# Deploy infrastructure with Terraform
deploy_infrastructure() {
    log "Deploying infrastructure with Terraform..."
    
    cd infrastructure/terraform
    
    terraform init
    terraform plan -var="environment=$ENVIRONMENT"
    terraform apply -auto-approve -var="environment=$ENVIRONMENT"
    
    cd ../..
    log "Infrastructure deployed successfully"
}

# Build and push Docker images
build_and_push_images() {
    log "Building and pushing Docker images..."
    
    # Get ECR repository URI
    ECR_URI=$(aws ecr describe-repositories --repository-names seo-health-report --query 'repositories[0].repositoryUri' --output text 2>/dev/null || echo "")
    
    if [ -z "$ECR_URI" ]; then
        log "Creating ECR repository..."
        aws ecr create-repository --repository-name seo-health-report
        ECR_URI=$(aws ecr describe-repositories --repository-names seo-health-report --query 'repositories[0].repositoryUri' --output text)
    fi
    
    # Login to ECR
    aws ecr get-login-password --region $AWS_REGION | docker login --username AWS --password-stdin $ECR_URI
    
    # Build and tag image
    docker build -t seo-health-report:latest .
    docker tag seo-health-report:latest $ECR_URI:latest
    docker tag seo-health-report:latest $ECR_URI:$(git rev-parse --short HEAD)
    
    # Push images
    docker push $ECR_URI:latest
    docker push $ECR_URI:$(git rev-parse --short HEAD)
    
    log "Images pushed to ECR: $ECR_URI"
}

# Deploy to ECS
deploy_ecs() {
    log "Deploying to ECS..."
    
    # Update ECS service
    aws ecs update-service \
        --cluster $CLUSTER_NAME \
        --service seo-health-app \
        --force-new-deployment \
        --region $AWS_REGION
    
    # Wait for deployment to complete
    log "Waiting for deployment to complete..."
    aws ecs wait services-stable \
        --cluster $CLUSTER_NAME \
        --services seo-health-app \
        --region $AWS_REGION
    
    log "ECS deployment completed"
}

# Deploy monitoring stack
deploy_monitoring() {
    log "Deploying monitoring stack..."
    
    # Deploy Prometheus and Grafana
    docker-compose -f infrastructure/docker-compose.monitoring.yml up -d
    
    # Wait for services to be ready
    sleep 30
    
    # Import Grafana dashboards
    curl -X POST \
        -H "Content-Type: application/json" \
        -d @infrastructure/monitoring/dashboards/seo-health-dashboard.json \
        http://admin:${GRAFANA_PASSWORD}@localhost:3001/api/dashboards/db
    
    log "Monitoring stack deployed"
}

# Setup SSL certificates
setup_ssl() {
    log "Setting up SSL certificates..."
    
    # Request SSL certificate via ACM
    CERT_ARN=$(aws acm request-certificate \
        --domain-name "*.seo-health.com" \
        --validation-method DNS \
        --query 'CertificateArn' \
        --output text)
    
    log "SSL certificate requested: $CERT_ARN"
    warn "Please validate the certificate via DNS before proceeding"
}

# Health check
health_check() {
    log "Performing health check..."
    
    # Get load balancer DNS name
    LB_DNS=$(aws elbv2 describe-load-balancers \
        --names seo-health-alb \
        --query 'LoadBalancers[0].DNSName' \
        --output text)
    
    # Check health endpoint
    if curl -f "http://$LB_DNS/health" >/dev/null 2>&1; then
        log "Health check passed: http://$LB_DNS/health"
    else
        error "Health check failed"
    fi
    
    # Check metrics endpoint
    if curl -f "http://$LB_DNS/metrics" >/dev/null 2>&1; then
        log "Metrics endpoint accessible"
    else
        warn "Metrics endpoint not accessible"
    fi
}

# Main deployment flow
main() {
    log "Starting deployment for environment: $ENVIRONMENT"
    
    check_prerequisites
    deploy_infrastructure
    build_and_push_images
    deploy_ecs
    deploy_monitoring
    setup_ssl
    health_check
    
    log "🎉 Deployment completed successfully!"
    log "Load Balancer: $(aws elbv2 describe-load-balancers --names seo-health-alb --query 'LoadBalancers[0].DNSName' --output text)"
    log "Monitoring: http://localhost:3001 (Grafana)"
    log "Metrics: http://localhost:9090 (Prometheus)"
}

# Run main function
main "$@"