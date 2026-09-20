# Test plan: Quote Chaser and Review Engine

Nothing in this file is a claim that these passed. They are generated, structurally validated against the eight working workflows, and untested on a live instance. This is the script to run at the keyboard.

Replace `YOUR-HOST` with your n8n host and `+1XXXXXXXXXX` with a phone you can read.

## Before you start

1. Import `09-quote-chaser.json` and `10-review-engine.json`.
2. In each, open Settings and set the error workflow to **Core 0: Error Handler**.
3. In each, open every **Execute Workflow** node and repoint it. `__WF_SENDSMS__` is **Core 1: Send SMS**, `__WF_ALERT__` is **Core 3: Owner Alert**.
4. Publish both.
5. Optional but recommended for testing: in the `config` table set `quote_wait_1_days`, `quote_wait_2_days` and `quote_wait_3_days` to `0`, and `review_delay_hours` to `0`. Without these the first nudge is two days out and you will be waiting. Put them back afterwards.
6. Review Engine needs `review_link` set in `config` or it will deliberately refuse and alert you instead.

These workflows read their timing and copy from `config` with fallbacks, so they run on your existing install without re-running Setup. Any key you do not add just uses the default.

## Quote Chaser

```
curl -X POST https://YOUR-HOST/webhook/quote-sent \
  -H "Content-Type: application/json" \
  -d '{"phone":"+1XXXXXXXXXX","name":"Test Customer","amount":"1850","job":"water heater replacement","quote_url":"https://example.com/q/1"}'
```

| # | Check | Expect |
| --- | --- | --- |
| 1 | Response | `{"ok":true}` immediately |
| 2 | `contacts` table | A row for that phone, stage `quoted` |
| 3 | `cadences` table | A row, workflow `quote_chaser`, step 0, status `active` |
| 4 | Owner alert | You get a text saying the quote chase started, with name, number and amount |
| 5 | Nudge 1 | Arrives after the configured wait, at 10am local if the wait is a day or more. Ends with the STOP footer |
| 6 | `cadences` step | Goes to 1 |
| 7 | **Reply STOP behaviour** | Send any reply from the test phone. Cadence status should flip to `stopped_reply` and nudge 2 should never send. This is the one worth watching, because it proves the inbound router stops a cadence it was never told about |
| 8 | Bad phone | Post with `"phone":"123"`. Should respond and do nothing else. No contact row, no cadence |
| 9 | Full run, no reply | Let all three nudges send. Cadence closes as `finished_no_reply` and you get the summary alert |

## Review Engine

```
curl -X POST https://YOUR-HOST/webhook/job-complete \
  -H "Content-Type: application/json" \
  -d '{"phone":"+1XXXXXXXXXX","name":"Test Customer","job":"the water heater"}'
```

| # | Check | Expect |
| --- | --- | --- |
| 1 | Response | `{"ok":true}` immediately |
| 2 | No review link | Blank `review_link` in config, post the webhook. You get an owner alert telling you to set it, and the customer gets nothing |
| 3 | With review link | Contact row stage `done`, cadence workflow `review_engine` status `active` |
| 4 | The ask | Arrives after the delay. Contains the review link and the line inviting a reply if something was wrong |
| 5 | **The gate** | Reply to it. Cadence stops, the reminder never sends, and the owner gets the reply forwarded by the existing router. This is the whole point: an unhappy customer reaches a person instead of a review form |
| 6 | Quiet hours | Set `review_delay_hours` so the ask lands inside quiet hours. Core 1 should defer it rather than send |
| 7 | Reminder | With no reply, the reminder sends after the configured days and the cadence closes |

## What to write down

For each numbered check: pass or fail, the timestamp, and what you actually saw. That log is what turns this from a template into evidence, and it is the thing that made the Lead Response repo worth reading.

If something fails, the useful detail is which node threw and what the input JSON was at that node, not just that it broke.
