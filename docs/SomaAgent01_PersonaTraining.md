⚠️ WE DO NOT MOCK we DO NOT IMITATE, WE DO NOT USE BYPASSES OR GIVE FAKE OR UNREAL VALUES TO PAST TESTS, we use MATH perfect math TO surpass any problem and we only abide truth and real serveres real data.

# SomaAgent 01 Persona Training Helper

`scripts/persona_training.py` provides a CLI for starting/closing training sessions until the full UI is implemented.

## Commands
- Start training session:
  ```bash
  python scripts/persona_training.py start --persona biology_researcher
  ```
  Sends a message through the gateway noting training mode.

- Close training session and store notes:
  ```bash
  python scripts/persona_training.py close --persona biology_researcher --notes "Trainer summary"
  ```
  Persists notes via the settings service (TRAINING profile) so reviewers can synthesize persona packs.

This CLI does not create persona packages automatically; it is a helper until the dedicated training service/UI is built.
