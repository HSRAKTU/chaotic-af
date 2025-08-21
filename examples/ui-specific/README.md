# Software Development Team Demo - 7 Agent Coordination

## Overview

This demo showcases a realistic **software development team** building an e-commerce platform. All 7 agents operate in **chaos mode** with full cross-team coordination capabilities.

## Team Structure

### Core Team (7 Agents)
1. **Product Manager** (8001) - Central coordinator, business requirements
2. **Backend Developer** (8002) - APIs, databases, server logic
3. **Frontend Developer** (8003) - UI/UX, customer experience
4. **DevOps Engineer** (8004) - Infrastructure, deployment, monitoring
5. **QA Tester** (8005) - Quality assurance, testing strategies
6. **Security Specialist** (8006) - Security reviews, compliance
7. **Tech Lead** (8007) - Technical architecture, oversight

### Network Topology (Hybrid Business Structure)

```
                    Product Manager (Hub)
                           |
                    ┌──────┼──────┐
                    │      │      │
               Tech Lead    │   Security
                │  │       │      │
            ┌───┼──┼───────┼──────┼───┐
            │   │  │       │      │   │
        Backend  │  │   Frontend  │   │
            │    │  └───────┼──────┘   │
            │    │          │          │
            └────┼──────────┼──────────┘
                 │          │
              DevOps ←──→ QA Tester
```

**Coordination Patterns:**
- **Star from PM**: Product Manager coordinates with everyone
- **Dev Cluster**: Backend ↔ Frontend collaboration
- **Integration Mesh**: DevOps, QA, Security integrated with developers
- **Technical Oversight**: Tech Lead oversees all technical work

## Quick Start

### 1. Setup Demo
```bash
cd examples/ui-specific
chmod +x setup_dev_team.sh
./setup_dev_team.sh
```

### 2. Start UI Monitor
```bash
pip install -r requirements-ui.txt
python ui_server.py
```

### 3. Open Dashboard
Open http://localhost:8080

## Impressive Test Scenarios

### Scenario 1: New Feature Development
```
Message to Product Manager:
"We need to implement user authentication with social login (Google, Facebook, Apple). This affects frontend UX, backend APIs, security policies, deployment infrastructure, and testing strategies. Coordinate with the entire team to create an implementation plan."
```

**Expected Coordination:**
- PM → Backend: API requirements
- PM → Frontend: UX design needs  
- PM → Security: Authentication security requirements
- Backend ↔ Frontend: API contract discussions
- Security → Backend: Authentication implementation security
- DevOps → Backend: Infrastructure for social providers
- QA → Frontend: Testing social login flows

### Scenario 2: Critical Security Issue
```
Message to Security Specialist:
"Critical vulnerability discovered in payment processing system. Customer credit card data may be exposed. This requires immediate coordination with backend team for patches, frontend team for user communication, DevOps for emergency deployment, QA for validation testing, and Product Manager for customer communication strategy."
```

### Scenario 3: Performance Crisis
```
Message to DevOps Engineer:
"Production system experiencing 10x traffic spike. Backend APIs are timing out, frontend is showing errors, payment processing is failing. Need immediate coordination with entire team for emergency scaling and fixes."
```

### Scenario 4: Complex Feature Request
```
Message to Tech Lead:
"CEO wants real-time inventory updates across mobile app, web frontend, and admin dashboard with live notifications. This requires backend real-time architecture, frontend WebSocket integration, mobile API changes, security review for new endpoints, testing strategy for real-time features, and DevOps infrastructure for WebSocket scaling."
```

## What You'll See

### Real-Time Animations
- **Flowing message dots** traveling along connections during tool calls
- **Connection pulse animations** when agents communicate
- **Agent node highlighting** when active (green for sending, blue for receiving)
- **Connection line glow** during active communication

### Complex Coordination Patterns
- Multi-hop discussions between specialists
- Parallel coordination across multiple team members
- Realistic business workflow automation
- Cross-functional team collaboration

### Network Topology Features
- **Hybrid structure**: Star (PM hub) + mesh (dev cluster) + integration points
- **Bidirectional connections** showing real team communication patterns
- **Dynamic scaling** - add more team members anytime
- **Visual status** - see which agents are active/thinking/responding

## Business Value Demonstration

This demo shows how the Chaotic AF framework can automate complex business workflows:
- **Realistic team coordination** patterns
- **Multi-department decision making** 
- **Crisis response coordination**
- **Feature development workflows**
- **Cross-functional collaboration**

Perfect for demonstrating enterprise automation capabilities!
