"""Module seed_lago."""

import os
import sys
import time

from lago_python_client.client import Client
from lago_python_client.models import Customer, Plan

# Add project root to path
sys.path.append(os.getcwd())

# Import Django settings for centralized configuration
try:
    from django.conf import settings

    LAGO_API_URL = settings.LAGO_API_URL
    LAGO_API_KEY = settings.LAGO_API_KEY
except ImportError:
    LAGO_API_URL = os.environ.get("SA01_LAGO_API_URL")
    LAGO_API_KEY = os.environ.get("SA01_LAGO_API_KEY", "")


def seed_lago():
    """Execute seed lago."""

    if not LAGO_API_URL or not LAGO_API_KEY:
        print("❌ LAGO_API_URL or LAGO_API_KEY not configured")
        print("Set SA01_LAGO_API_URL and SA01_LAGO_API_KEY environment variables")
        return

    print(f"🌱 Seeding Lago at {LAGO_API_URL}...")

    client = Client(api_key=LAGO_API_KEY, api_url=LAGO_API_URL)

    # 1. Check connectivity
    try:
        client.customers.find_all()
        print("✅ Connected to Lago API")
    except Exception as e:
        print(f"❌ Failed to connect: {e}")
        return

    # 2. Create a 'Pro' Plan
    try:
        plan_code = "plan_pro_tier"
        plan_name = "Pro Tier"

        plan_input = Plan(
            code=plan_code,
            name=plan_name,
            interval="monthly",
            amount_cents=5000,
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
    time.sleep(2)
    seed_lago()
