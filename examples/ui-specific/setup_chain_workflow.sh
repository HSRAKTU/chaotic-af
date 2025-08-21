#!/bin/bash

echo "🔗 Setting up True Chain-Based Workflow (Sequential Discussions)"
echo "=============================================================="

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

echo "🔗 Creating TRUE CHAIN network (minimal connections)..."

# === PRIMARY DEVELOPMENT CHAIN ===
echo "💻 Primary Development Chain: PM → Backend → Frontend → QA..."
python -m agent_framework.cli.commands connect product_manager backend_dev
python -m agent_framework.cli.commands connect backend_dev frontend_dev
python -m agent_framework.cli.commands connect frontend_dev qa_tester

# === DEPLOYMENT CHAIN ===
echo "📦 Deployment Chain: QA → DevOps → Security..."
python -m agent_framework.cli.commands connect qa_tester devops_engineer
python -m agent_framework.cli.commands connect devops_engineer security_specialist

# === LEADERSHIP CHAIN ===
echo "🎯 Leadership Chain: Security → Tech Lead → PM..."
python -m agent_framework.cli.commands connect security_specialist tech_lead
python -m agent_framework.cli.commands connect tech_lead product_manager

# === EMERGENCY ESCALATION (ONE-WAY ONLY) ===
echo "⚡ Emergency Escalation Paths..."
python -m agent_framework.cli.commands connect backend_dev tech_lead
python -m agent_framework.cli.commands connect devops_engineer tech_lead

echo ""
echo "✅ True Chain Workflow Network Ready!"
echo "===================================="
echo ""
echo "🔗 NETWORK TOPOLOGY (True Sequential Chain):"
echo ""
echo "Product Manager → Backend Dev → Frontend Dev → QA Tester"
echo "       ↑                                         ↓"
echo "   Tech Lead ←←← Security ←←← DevOps Engineer ←←←←"
echo "       ↑ (emergency escalation)"
echo "   Backend Dev"
echo "   DevOps"
echo ""
echo "📋 CHAIN BEHAVIOR ENCOURAGEMENT:"
echo "• Each agent primarily connected to NEXT in chain"
echo "• Limited bidirectional connections"
echo "• Emergency escalation to Tech Lead only"
echo "• Forces sequential discussions"
echo ""
echo "🔗 CHAIN-OPTIMIZED PROMPTS (Use these specific prompts):"
echo ""
echo "1. TO PRODUCT MANAGER (Chain initiator):"
echo "   'New critical feature: Multi-factor authentication. Please pass this requirement down the development chain for implementation and get back to me with the final plan.'"
echo ""
echo "2. TO BACKEND DEV (Chain propagator):"
echo "   'Payment API needs rate limiting implementation. Please discuss with the next team member in the workflow and pass along the coordination chain.'"
echo ""
echo "3. TO QA TESTER (Chain coordinator):"
echo "   'Security vulnerability found in user session management. Please coordinate this through the deployment and security review chain before escalation.'"
echo ""
echo "🎯 These prompts specifically encourage PASSING ALONG rather than broadcasting!"
echo ""
echo "🎨 Start UI Monitor to see true chain coordination:"
echo "   python ../../ui_server.py"
echo "   Open: http://localhost:8080"