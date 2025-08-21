#!/bin/bash

echo "🌱 Setting up Organic Software Development Workflow"
echo "=================================================="

# Navigate to project root
cd "$(dirname "$0")/../.."

echo "🚀 Starting 7-agent software development team..."

# Start all agents
python -m agent_framework.cli.commands start \
  examples/ui-specific/product_manager.yaml \
  examples/ui-specific/backend_dev.yaml \
  examples/ui-specific/frontend_dev.yaml \
  examples/ui-specific/devops_engineer.yaml \
  examples/ui-specific/qa_tester.yaml \
  examples/ui-specific/security_specialist.yaml \
  examples/ui-specific/tech_lead.yaml

echo "⏳ Waiting for agents to be ready..."
sleep 5

echo "🌱 Creating organic peer-to-peer workflow network..."

# === PRODUCT-TECH STRATEGIC LAYER (Minimal Hub) ===
echo "📋 Strategic Leadership Coordination..."
python -m agent_framework.cli.commands connect product_manager tech_lead -b

# === DEVELOPMENT CLUSTER (Peer Collaboration) ===
echo "💻 Development Peer Cluster..."
python -m agent_framework.cli.commands connect backend_dev frontend_dev -b
python -m agent_framework.cli.commands connect backend_dev tech_lead -b
python -m agent_framework.cli.commands connect frontend_dev tech_lead -b

# === DEPLOYMENT WORKFLOW CHAIN ===
echo "📦 Deployment Workflow Chain..."
python -m agent_framework.cli.commands connect backend_dev devops_engineer -b
python -m agent_framework.cli.commands connect frontend_dev devops_engineer -b

# === QUALITY WORKFLOW CHAIN ===
echo "🧪 Quality Assurance Workflow..."
python -m agent_framework.cli.commands connect backend_dev qa_tester -b
python -m agent_framework.cli.commands connect frontend_dev qa_tester -b
python -m agent_framework.cli.commands connect qa_tester devops_engineer -b

# === SECURITY REVIEW CHAIN ===
echo "🔒 Security Review Workflow..."
python -m agent_framework.cli.commands connect backend_dev security_specialist -b
python -m agent_framework.cli.commands connect security_specialist devops_engineer -b

# === ESCALATION PATHS ===
echo "⚡ Escalation and Crisis Communication..."
python -m agent_framework.cli.commands connect tech_lead security_specialist -b
python -m agent_framework.cli.commands connect qa_tester security_specialist -b

# === PRODUCT COORDINATION (Limited) ===
echo "🎯 Product-Development Coordination..."
python -m agent_framework.cli.commands connect product_manager backend_dev -b

echo ""
echo "✅ Organic Software Development Workflow Ready!"
echo "=============================================="
echo ""
echo "🌱 NETWORK TOPOLOGY (Organic Peer-to-Peer):"
echo ""
echo "    Product Manager ←→ Tech Lead"
echo "         ↓               ↓ ↓ ↓"
echo "    Backend Dev ←→ Frontend Dev"
echo "         ↓ ↓           ↓"
echo "      DevOps ←→ QA ←→ Security"
echo "         ↓           ↓"
echo "      Security ←→ Tech Lead"
echo ""
echo "🎯 KEY WORKFLOW PATTERNS:"
echo "• Development: Backend ↔ Frontend peer collaboration"
echo "• Deployment: Dev → DevOps → Security workflow"
echo "• Quality: Dev → QA → DevOps → Security chain"
echo "• Crisis: Any agent → Tech Lead escalation"
echo "• Strategy: Product Manager ↔ Tech Lead decisions"
echo ""
echo "🌪️ RECOMMENDED TEST PROMPTS:"
echo ""
echo "1. TO BACKEND DEV (Peer-to-peer development):"
echo "   'Need to implement new API endpoint for user profiles - coordinate with frontend for UI integration'"
echo ""
echo "2. TO QA TESTER (Quality workflow chain):"
echo "   'Found critical bug in checkout flow - coordinate with developers and DevOps for fix and deployment'"
echo ""
echo "3. TO SECURITY SPECIALIST (Security review chain):"
echo "   'Review new payment integration security - coordinate with backend for implementation and DevOps for deployment'"
echo ""
echo "4. TO DEVOPS ENGINEER (Deployment workflow):"
echo "   'Production deployment failing - coordinate with developers for fixes and QA for validation'"
echo ""
echo "🎨 Start UI Monitor to see organic peer coordination:"
echo "   python ../../ui_server.py"
echo "   Open: http://localhost:8080"
