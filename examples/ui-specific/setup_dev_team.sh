#!/bin/bash

echo "🏗️ Setting up Software Development Team Demo (7 Agents)"
echo "======================================================="

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

echo "🔗 Creating hybrid network topology..."

# Product Manager (Hub) - Connected to everyone
echo "📋 Connecting Product Manager to all team members..."
python -m agent_framework.cli.commands connect product_manager backend_dev -b
python -m agent_framework.cli.commands connect product_manager frontend_dev -b  
python -m agent_framework.cli.commands connect product_manager devops_engineer -b
python -m agent_framework.cli.commands connect product_manager qa_tester -b
python -m agent_framework.cli.commands connect product_manager security_specialist -b
python -m agent_framework.cli.commands connect product_manager tech_lead -b

# Developer Collaboration Cluster
echo "💻 Connecting development cluster..."
python -m agent_framework.cli.commands connect backend_dev frontend_dev -b

# DevOps Integration Points
echo "🚀 Connecting DevOps to development workflow..."
python -m agent_framework.cli.commands connect devops_engineer backend_dev -b
python -m agent_framework.cli.commands connect devops_engineer frontend_dev -b

# QA Testing Integration
echo "🧪 Connecting QA to testing workflow..."
python -m agent_framework.cli.commands connect qa_tester backend_dev -b
python -m agent_framework.cli.commands connect qa_tester frontend_dev -b
python -m agent_framework.cli.commands connect qa_tester devops_engineer -b

# Security Review Integration  
echo "🔒 Connecting Security to review workflow..."
python -m agent_framework.cli.commands connect security_specialist backend_dev -b
python -m agent_framework.cli.commands connect security_specialist frontend_dev -b
python -m agent_framework.cli.commands connect security_specialist devops_engineer -b

# Tech Lead Oversight
echo "🎯 Connecting Tech Lead oversight..."
python -m agent_framework.cli.commands connect tech_lead backend_dev -b
python -m agent_framework.cli.commands connect tech_lead frontend_dev -b
python -m agent_framework.cli.commands connect tech_lead devops_engineer -b
python -m agent_framework.cli.commands connect tech_lead qa_tester -b
python -m agent_framework.cli.commands connect tech_lead security_specialist -b

echo ""
echo "✅ Software Development Team Demo Ready!"
echo "========================================"
echo ""
echo "🎨 Start UI Monitor:"
echo "   pip install -r requirements-ui.txt"  
echo "   python ui_server.py"
echo "   Open: http://localhost:8080"
echo ""
echo "🌪️ Test Complex Scenarios:"
echo "   'We need to implement user authentication with social login'"
echo "   'Critical security vulnerability found in payment system'"
echo "   'Backend API performance issues affecting frontend UX'"
echo "   'New feature requires coordination between all team members'"
echo ""
echo "👀 Watch the beautiful network topology animations!"
echo "   See agents coordinate in real-time with flowing message dots"
echo "   Network connections pulse and glow during communication"
echo "   Agent nodes highlight when active"
