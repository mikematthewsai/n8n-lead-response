# Standalone templates

The workflows in `workflows/` are a system: they share one send path, one owner alert and a set of data tables, which is what makes them reliable together and also why none of them can be imported on its own.

These are single workflows that stand alone. Each one needs nothing but its own credentials, so they can go in n8n's public template library and be imported in one step.

| Template | What it does | Tested |
| --- | --- | --- |
| [quote-chaser-sms-twilio.json](quote-chaser-sms-twilio.json) | Chases an unanswered quote with up to three SMS nudges and stops the moment the customer replies. No database: before each nudge it asks Twilio whether the customer has texted the business number since the quote went out | 2026-09-20, live, three runs below |

## Quote chaser, test runs on 2026-09-20

Run against a real Twilio number with the waits set to 0.002 days (about three minutes), then set back to the defaults of 2, 3 and 4 days before export.

| Run | Setup | Result |
| --- | --- | --- |
| A | Customer never replies | Passed. Start alert to the owner, three nudges about three minutes apart, then the closing alert. All three reply checks ran against the Twilio API without error |
| B | Customer replies after nudge 1 | Passed. The second reply check found the inbound text, the owner got "replied ... chase stopped", and nudge 2 never sent |
| C | Phone number is `123` | Passed. The webhook answered `{"ok":true}` and nothing was sent |

The exported file was checked against the tested workflow node by node: every node's parameters and the connections hash identically, ignoring generated ids and credential references.

What is not covered: both parties were the same handset, the default multi day waits were not run at full length, and the 10am landing time was not observed live because the test waits were under a day.
