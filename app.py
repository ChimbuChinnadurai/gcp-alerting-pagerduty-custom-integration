import base64
import json
import os
import requests
import logging
import google.cloud.logging


def get_pagerduty_payload(pubsub_message, event_timestamp, event_action):
    json_payload = {
        "payload": {
            "summary": pubsub_message["incident"]["policy_name"].replace("📳 ", ""),
            "timestamp": event_timestamp,
            "source": pubsub_message["incident"]["condition"]["name"],
            "severity": pubsub_message["incident"]["policy_user_labels"]["severity"],
            "component": pubsub_message["incident"]["policy_user_labels"]["service_name"],
            "custom_details": {
                "service_name": pubsub_message["incident"]["policy_user_labels"]["service_name"],
                "gcp_incident_id": pubsub_message["incident"]["incident_id"],
                "gcp_project_id": pubsub_message["incident"]["scoping_project_id"],
                "documentation": pubsub_message["incident"]["documentation"]["content"].replace("`", "").replace("*",
                                                                                                                 ""),
            }
        },
        "links": [
            {
                "href": pubsub_message["incident"]["url"],
                "text": "Google Cloud Console"
            }
        ],
        "dedup_key": pubsub_message["incident"]["incident_id"],
        "event_action": event_action
    }
    return json_payload


def send_alerts_pagerduty(event, context):
    if os.getenv('CLOUD_LOGGING_ENABLED') == "true":
        client = google.cloud.logging.Client()
        client.setup_logging()
    try:
        logging.info("""This Function was triggered by messageId {} published at {}""".format(context.event_id,
                                                                                              context.timestamp))
        gcp_pagerduty_event_action_mappings = {
            "open": "trigger",
            "closed": "resolve"
        }
        pubsub_message = json.loads(base64.b64decode(event["data"]).decode("utf-8"))
        print(pubsub_message)
        event_action = gcp_pagerduty_event_action_mappings[(pubsub_message["incident"])["state"]]
        pd_json_payload = get_pagerduty_payload(pubsub_message, context.timestamp, event_action)
        print(pd_json_payload)
        for key,value in pubsub_message["incident"]["resource"]["labels"].items():
            print(key,value)

        if pubsub_message["incident"]["policy_user_labels"]["severity"]:
            pd_json_payload = get_pagerduty_payload(pubsub_message, context.timestamp, event_action)
            print(pd_json_payload)
            response = requests.post(
                            os.environ['PAGERDUTY_ENDPOINT'],
                            json=pd_json_payload,
                            headers={"x-routing-key": os.environ.get('PAGERDUTY_INTEGRATION_KEY')}
                        )
                        if response.status_code == 202:
                            logging.info("Alert details are successfully sent to Pagerduty")
                        else:
                            logging.error(
                                "Failed to send the alert details to pagerduty Status Code = {}, Response Message = {}".format(
                                    response.status_code, response.text
                                ))
                            raise Exception(response.status_code, response.text)
            response = requests.post(
                os.environ['PAGERDUTY_ENDPOINT'],
                    response = requests.post(
                            os.environ['PAGERDUTY_ENDPOINT'],
                            json=pd_json_payload,
                            headers={"x-routing-key": os.environ.get('PAGERDUTY_INTEGRATION_KEY')}
                        )
                        if response.status_code == 202:
                            logging.info("Alert details are successfully sent to Pagerduty")
                        else:
                            logging.error(
                                "Failed to send the alert details to pagerduty Status Code = {}, Response Message = {}".format(
                                    response.status_code, response.text
                                ))
                            raise Exception(response.status_code, response.text)
                json=pd_json_payload,
                headers={"x-routing-key": os.environ.get('PAGERDUTY_INTEGRATION_KEY')}
            )
            if response.status_code == 202:
                logging.info("Alert details are successfully sent to Pagerduty")
            else:
                logging.error(
                    "Failed to send the alert details to pagerduty Status Code = {}, Response Message = {}".format(
                        response.status_code, response.text
                    ))
                raise Exception(response.status_code, response.text)

    except Exception as exception:
        logging.error(f"Failed to process GCP incident message '{event}'")
        logging.error(exception)


if __name__ == "__main__":
    send_alerts_pagerduty(event1, context1)
