"""Module seed_lago."""

import os
import sys
import time

from lago_python_client.client import Client
from lago_python_client.models import Customer, Plan

# Add project root to path
sys.path.append(os.getcwd())

# Configuration (Real configuration from env or defaults)
LAGO_API_KEY = os.environ.get("LAGO_API_KEY", "")
LAGO_API_URL = "http://localhost:20600/api/v1"


def seed_lago():
    """Execute seed lago."""

    print(f"🌱 Seeding Lago at {LAGO_API_URL}...")

    client = Client(api_key=LAGO_API_KEY, api_url=LAGO_API_URL)

    # 1. Check connectivity
    try:
        # Simple verify by listing customers
        client.customers.find_all()
        print("✅ Connected to Lago API")
    except Exception as e:
        print(f"❌ Failed to connect: {e}")
        return

    # 2. Create a 'Pro' Plan
    try:
        plan_code = "plan_pro_tier"
        plan_name = "Pro Tier"

        # Check if exists (idempotency)
        # Note: Client doesn't have simple 'exists', so we try create or ignore error in a real script,
        # or list and filter. For simplicity in this seed script, we just try to create.

        plan_input = Plan(
            code=plan_code,
            name=plan_name,
            interval="monthly",
            amount_cents=5000,  # $50.00
            amount_currency="USD",
            trial_period=0,
            pay_in_advance=True,
        )

        try:
            client.plans.create(plan_input)
            print(f"✅ Created Plan: {plan_name}")
        except Exception as e:
            if "already exists" in str(e) or "code" in str(e):
                print(f"ℹ️  Plan {plan_name} likely already exists")
            else:
                print(f"⚠️ Could not create plan: {e}")

    except Exception as e:
        print(f"❌ Plan Error: {e}")

    # 3. Create a Test Customer (Tenant)
    try:
        customers = [
            {"name": "Acme Corp", "id": "t-acme-corp", "email": "admin@acme.com"},
            {"name": "Cyberdyne Systems", "id": "t-cyberdyne", "email": "skynet@cyberdyne.io"},
            {"name": "Wayne Enterprises", "id": "t-wayne-ent", "email": "bruce@wayne.com"},
        ]

        for c in customers:
            cust_input = Customer(external_id=c["id"], name=c["name"], email=c["email"])
            try:
                client.customers.create(cust_input)
                print(f"✅ Created Customer: {c['name']}")
            except Exception as e:
                if "already exists" in str(e) or "external_id" in str(e):
                    print(f"ℹ️  Customer {c['name']} likely already exists")
                else:
                    print(f"⚠️ Could not create customer {c['name']}: {e}")

    except Exception as e:
        print(f"❌ Customer Error: {e}")

    print("\n✨ Seeding Complete. Dashboard should now show real data.")


if __name__ == "__main__":
    # Wait for services to be fully fully up if run immediately after docker up
    time.sleep(2)
    seed_lago()
