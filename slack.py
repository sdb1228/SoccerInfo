import slackweb

def draft_slack_message(location, status, error_message=None):
  message = "*" + location + "*: "
  if status == "success":
    message = message + "Succesfully ran scraper!"
  elif status == "failed":
    message = "<!channel> " + message
    message = message + "Failed to run scraper."
    if error_message is not None:
      message = message + "\n```" + error_message + "```"
  else:
    message = "<!channel> " + message
    message = message + "Unknown status of " + status
  notify_slack(message)

def notify_slack(message):
  token = "https://hooks.slack.com/services/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"
  notifier = slackweb.Slack(url=token)
  notifier.notify(text=message, channel="#scrapers", username="scraperbot")
