from common import print_ok, require_env, require_package

require_package("requests", "pip install -r requirements.txt")

from app.services.providers.authkey_client import AuthkeyClient


authkey = require_env("AUTHKEY_API_KEY")
result = AuthkeyClient(authkey).get_balance()
if not result.sent:
    raise RuntimeError(f"Authkey balance check failed: {result.status_code} {result.error}")

print_ok("Authkey balance API responded")
