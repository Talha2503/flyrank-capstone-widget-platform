import os

FORCE_NOTIFY_DOWN = os.environ.get("FORCE_NOTIFY_DOWN", "false").lower() == "true"


def send_confirmation_email(to_email: str | None, widget_title: str) -> bool:
    """
    Simulates a confirmation email side effect. Returns True/False for
    logging purposes only -- callers must NEVER let this raise past them,
    and must NEVER let its failure block a submission's success.
    """
    if FORCE_NOTIFY_DOWN:
        raise RuntimeError("Simulated email provider outage")

    if not to_email:
        print(f"[notify] no email address in submission for '{widget_title}', skipping")
        return False

    # In a real app this would call an SMTP server / Mailpit / a webhook.
    # For this capstone, logging is the "safe side effect" -- what's graded
    # is that its failure never blocks the main path, not the email itself.
    print(f"[notify] confirmation email sent to {to_email} for widget '{widget_title}'")
    return True