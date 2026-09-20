# Test plan: Quote Chaser

Nothing in this file is a claim that this passed. It is generated, structurally validated against the eight working workflows, and untested on a live instance. This is the script to run at the keyboard.

Replace `YOUR-HOST` with your n8n host and `+1XXXXXXXXXX` with a phone you can read.

## Before you start

1. Import `09-quote-chaser.json`.
2. Open Settings and set the error workflow to **Core 0: Error Handler**.
3. Open every **Execute Workflow** node and repoint it. `__WF_SENDSMS__` is **Core 1: Send SMS**, `__WF_ALERT__` is **Core 3: Owner Alert**.
4. Publish it.
5. Optional but recommended for testing: in the `config` table set `quote_wait_1_days`, `quote_wait_2_days` and `quote_wait_3_days` to `0`. Without these the first nudge is two days out and you will be waiting. Put them back afterwards.

This workflow reads its timing and copy from `config` with fallbacks, so it runs on your existing install without re-running Setup. Any key you do not add just uses the default.

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

## What to write down

For each numbered check: pass or fail, the timestamp, and what you actually saw. That log is what turns this from a template into evidence, and it is the thing that made the Lead Response repo worth reading.

If something fails, the useful detail is which node threw and what the input JSON was at that node, not just that it broke.
