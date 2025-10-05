.PHONY: help install setup test deploy destroy monitor logs status clean gcp-auth

# Colors
RED=\033[0;31m
GREEN=\033[0;32m
YELLOW=\033[1;33m
NC=\033[0m

help:
	@echo "$(YELLOW)Agentic AI Cloud Run Deployer$(NC)"
	@echo ""
	@echo "$(GREEN)Available commands:$(NC)"
	@echo "  install     - Install Python dependencies"
	@echo "  setup       - Setup environment and GCP authentication"
	@echo "  test        - Run tests"
	@echo "  deploy      - Start the deployment agent"
	@echo "  destroy     - Destroy deployed infrastructure"
	@echo "  monitor     - Open Cloud Run monitoring dashboard"
	@echo "  logs        - View application logs"
	@echo "  status      - Check deployment status"
	@echo "  clean       - Clean generated files"

install:
	@echo "$(YELLOW)Installing dependencies...$(NC)"
	pip install -r requirements.txt
	@echo "$(GREEN)✓ Dependencies installed$(NC)"

setup:
	@echo "$(YELLOW)Setting up environment...$(NC)"
	@if [ ! -f .env ]; then \
		cp .env.example .env; \
		echo "$(GREEN)✓ Created .env file - please configure your GCP credentials$(NC)"; \
	else \
		echo "$(YELLOW)✓ .env file already exists$(NC)"; \
	fi
	@echo "$(YELLOW)Please make sure you have Google Cloud SDK installed and authenticated$(NC)"

gcp-auth:
	@echo "$(YELLOW)Setting up GCP authentication...$(NC)"
	gcloud auth login
	@read -p "Enter your GCP project ID: " project_id; \
	gcloud config set project $$project_id
	gcloud services enable run.googleapis.com
	gcloud services enable sqladmin.googleapis.com
	gcloud services enable cloudbuild.googleapis.com
	gcloud services enable artifactregistry.googleapis.com
	gcloud services enable cloudresourcemanager.googleapis.com
	@echo "$(GREEN)✓ GCP services enabled$(NC)"

test:
	@echo "$(YELLOW)Running tests...$(NC)"
	python -m pytest tests/ -v
	@echo "$(GREEN)✓ Tests completed$(NC)"

deploy: install setup
	@echo "$(YELLOW)Starting Agentic AI Deployment Agent...$(NC)"
	@echo "$(GREEN)🚀 The agent will prompt for your .NET repository and deploy to Cloud Run$(NC)"
	python -m agent.main

deploy-auto: install setup
	@echo "$(YELLOW)Starting automated deployment...$(NC)"
	python -m agent.main --auto

destroy:
	@echo "$(RED)Destroying Cloud Run infrastructure...$(NC)"
	@if [ -d "outputs/terraform" ]; then \
		cd outputs/terraform && terraform destroy -auto-approve; \
	else \
		echo "$(YELLOW)No terraform outputs found - nothing to destroy$(NC)"; \
	fi

monitor:
	@echo "$(YELLOW)Opening Cloud Run dashboard...$(NC)"
	@read -p "Enter your GCP project ID: " project_id; \
	open "https://console.cloud.google.com/run?project=$$project_id"

logs:
	@echo "$(YELLOW)Fetching Cloud Run logs...$(NC)"
	gcloud logging read "resource.type=cloud_run_revision" --limit=20 --format="table(timestamp,logName,textPayload)"

status:
	@echo "$(YELLOW)Cloud Run services status:$(NC)"
	gcloud run services list --platform=managed --format="table(service.name,status.url,status.conditions[0].type)"

clean:
	@echo "$(YELLOW)Cleaning generated files...$(NC)"
	rm -rf outputs/
	rm -rf __pycache__/
	rm -rf agent/__pycache__/
	rm -rf clouds/__pycache__/
	rm -rf tests/__pycache__/
	rm -rf agent/config/__pycache__/
	rm -rf clouds/gcp/__pycache__/
	@echo "$(GREEN)✓ Clean completed$(NC)"

cost-estimate:
	@echo "$(YELLOW)Cloud Run Cost Estimation:$(NC)"
	@echo "  • First 2 million requests: Free"
	@echo "  • Memory: \$0.00002400 per GiB-second"
	@echo "  • CPU: \$0.00002400 per vCPU-second"
	@echo "  • Cloud SQL PostgreSQL (db-f1-micro): ~\$8/month"
	@echo "  • Estimated monthly cost for 2 services: ~\$15-25"

.PHONY: help install setup test deploy destroy monitor logs status clean gcp-auth cost-estimate