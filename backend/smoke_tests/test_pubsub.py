from common import optional_env, print_ok, require_env, require_package

require_package("google.cloud.pubsub_v1", "pip install -r requirements.txt")

from google.cloud import pubsub_v1


project = require_env("GOOGLE_CLOUD_PROJECT")
topic_name = optional_env("PUBSUB_ALERT_TOPIC", "kisan-alerts")
publisher = pubsub_v1.PublisherClient()
topic_path = publisher.topic_path(project, topic_name)
publisher.get_topic(request={"topic": topic_path})
print_ok(f"Pub/Sub topic exists: {topic_path}")
