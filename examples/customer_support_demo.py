"""Industrial Use Case: Customer Support Automation System

This demo shows how Chaotic AF can be used to build a multi-agent customer support system
with specialized agents handling different aspects of customer queries.
"""

import asyncio
from agent_framework import AgentSupervisor, AgentConfig

async def main():
    supervisor = AgentSupervisor()
    
    # Customer Service Agent - First point of contact
    customer_service = AgentConfig(
        name="customer_service",
        llm_provider="google",
        llm_model="gemini-1.5-pro",
        role_prompt="""You are a friendly customer service representative. 
        Your job is to understand customer issues and route them to the right specialist.
        Available specialists: tech_support (technical issues), billing (payment/subscription), shipping (order tracking).
        Always be polite and empathetic. Ask clarifying questions if needed.""",
        port=9001
    )
    
    # Technical Support Specialist
    tech_support = AgentConfig(
        name="tech_support",
        llm_provider="google",
        llm_model="gemini-1.5-pro",
        role_prompt="""You are a technical support specialist. You help with:
        - Software installation and configuration
        - Bug reports and error messages
        - Performance issues
        - Integration problems
        Provide clear, step-by-step solutions. If you need more info, ask specific technical questions.""",
        port=9002
    )
    
    # Billing Specialist
    billing = AgentConfig(
        name="billing",
        llm_provider="google",
        llm_model="gemini-1.5-pro",
        role_prompt="""You are a billing specialist. You handle:
        - Payment issues and failed transactions
        - Subscription upgrades/downgrades
        - Refund requests
        - Invoice questions
        Be precise with numbers and dates. Always confirm customer details before making changes.""",
        port=9003
    )
    
    # Shipping & Logistics Specialist
    shipping = AgentConfig(
        name="shipping",
        llm_provider="google",
        llm_model="gemini-1.5-pro",
        role_prompt="""You are a shipping specialist. You handle:
        - Order tracking and delivery status
        - Lost or damaged packages
        - Address changes
        - Delivery scheduling
        Provide tracking numbers and estimated delivery dates when available.""",
        port=9004
    )
    
    # Add all agents
    supervisor.add_agent(customer_service)
    supervisor.add_agent(tech_support)
    supervisor.add_agent(billing)
    supervisor.add_agent(shipping)
    
    try:
        print("🏢 Customer Support System Starting...")
        await supervisor.start_all(monitor=False)
        await asyncio.sleep(3)
        
        # Connect customer service to all specialists
        await supervisor.connect("customer_service", "tech_support", bidirectional=True)
        await supervisor.connect("customer_service", "billing", bidirectional=True)
        await supervisor.connect("customer_service", "shipping", bidirectional=True)
        
        # Connect specialists to each other for complex cases
        await supervisor.connect("tech_support", "billing", bidirectional=True)
        await supervisor.connect("billing", "shipping", bidirectional=True)
        
        print("✅ Customer Support System Ready!")
        print("\nAgent Network:")
        print("- customer_service (Port 9001) - First point of contact")
        print("- tech_support (Port 9002) - Technical issues")
        print("- billing (Port 9003) - Payment & subscriptions")
        print("- shipping (Port 9004) - Orders & delivery")
        print("\nTest the system:")
        print("python -m agent_framework.cli.commands chat customer_service -v \"My order hasn't arrived and I was charged twice!\"")
        print("\nOr interactive mode:")
        print("python -m agent_framework.cli.commands chat customer_service -i -v")
        
        # Keep running
        await asyncio.Event().wait()
        
    except KeyboardInterrupt:
        print("\n\n🛑 Shutting down Customer Support System...")
    finally:
        await supervisor.stop_all()
        print("✅ System stopped")

if __name__ == "__main__":
    asyncio.run(main())
