#!/bin/bash

echo "🏢 Setting up Realistic Software Development Team Hierarchy"
echo "=========================================================="

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

echo "🏗️ Creating realistic business hierarchy network..."

# === STRATEGIC LAYER ===
echo "📋 Strategic Coordination (Product ↔ Tech Leadership)..."
python -m agent_framework.cli.commands connect product_manager tech_lead -b

# === TECHNICAL OVERSIGHT ===  
echo "🎯 Technical Leadership Oversight..."
python -m agent_framework.cli.commands connect tech_lead backend_dev -b
python -m agent_framework.cli.commands connect tech_lead frontend_dev -b
python -m agent_framework.cli.commands connect tech_lead devops_engineer -b
python -m agent_framework.cli.commands connect tech_lead security_specialist -b
python -m agent_framework.cli.commands connect tech_lead qa_tester -b

# === DEVELOPMENT COLLABORATION ===
echo "💻 Core Development Team Collaboration..."
python -m agent_framework.cli.commands connect backend_dev frontend_dev -b

# === FEATURE COORDINATION ===
echo "🚀 Product-Development Direct Coordination..."
python -m agent_framework.cli.commands connect product_manager backend_dev -b
python -m agent_framework.cli.commands connect product_manager frontend_dev -b

# === DEPLOYMENT WORKFLOW ===
echo "📦 DevOps Integration Workflow..." 
python -m agent_framework.cli.commands connect devops_engineer backend_dev -b
python -m agent_framework.cli.commands connect devops_engineer frontend_dev -b

# === QUALITY ASSURANCE WORKFLOW ===
echo "🧪 QA Testing Workflow..."
python -m agent_framework.cli.commands connect qa_tester backend_dev -b
python -m agent_framework.cli.commands connect qa_tester frontend_dev -b
python -m agent_framework.cli.commands connect qa_tester devops_engineer -b

# === SECURITY REVIEW WORKFLOW ===
echo "🔒 Security Review Workflow..."
python -m agent_framework.cli.commands connect security_specialist backend_dev -b
python -m agent_framework.cli.commands connect security_specialist frontend_dev -b
python -m agent_framework.cli.commands connect security_specialist devops_engineer -b

echo ""
echo "✅ Realistic Software Development Team Hierarchy Ready!"
echo "======================================================"
echo ""
echo "🏗️ NETWORK TOPOLOGY:"
echo "                    Product Manager"
echo "                    ↙      ↓      ↘"
echo "               Backend  Tech Lead  Frontend"
echo "                 ↓        ↓         ↓"
echo "              DevOps ←→ Security ←→ QA"
echo ""
echo "🎨 Start UI Monitor:"
echo "   pip install -r requirements-ui.txt"  
echo "   python ui_server.py"
echo "   Open: http://localhost:8080"
echo ""
echo "🎯 RECOMMENDED TEST PROMPTS:"
echo ""
echo "1. TO PRODUCT MANAGER (Multi-team coordination):"
echo "   'We need to implement user authentication with social login'"
echo ""
echo "2. TO TECH LEAD (Technical crisis):"
echo "   'Backend performance is degraded, affecting frontend UX and customer checkout'"
echo ""
echo "3. TO SECURITY SPECIALIST (Security review):"
echo "   'Please review the new payment API for security vulnerabilities'"
echo ""
echo "4. TO BACKEND DEV (Feature development):"
echo "   'Implement real-time inventory updates that frontend and mobile can consume'"
echo ""
echo "👀 Watch realistic business hierarchy coordination!"
