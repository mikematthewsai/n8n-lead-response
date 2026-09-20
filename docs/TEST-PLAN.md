# Test plan: Quote Chaser, Invoice Nudge, Morning Brief

Nothing in this file is a claim that these passed. They are generated, structurally validated against the eight working workflows, and untested on a live instance. This is the script to run at the keyboard.

Replace `YOUR-HOST` with your n8n host and `+1XXXXXXXXXX` with a phone you can read.

## Before you start

1. Import `09-quote-chaser.json`, `10-invoice-nudge.json` and `11-morning-brief.json`.
2. In each, open Settings and set the error workflow to **Core 0: Error Handler**.
3. In each, open every **Execute Workflow** node and repoint it. `__WF_SENDSMS__` is **Core 1: Send SMS**, `__WF_ALERT__` is **Core 3: Owner Alert**.
4. Publish all three.

### About config

These three read their timing and their copy from the `config` table, and every key has a default in code. `config` is a data table with fixed columns, so adding a setting means adding a column to that table. You do not have to add any of them. Skip the lot and the defaults apply.

The settings they look for:

| Key | Default | Used by |
| --- | --- | --- |
| `quote_wait_1_days` / `_2_` / `_3_` | 2 / 3 / 4 | Quote Chaser |
| `quote_nudge_1_text` / `_2_` / `_3_` | built in | Quote Chaser |
| `invoice_due_days` | 7 | Invoice Nudge, only when the caller sends no `due_date` |
| `invoice_wait_2_days` / `_3_` | 3 / 4 | Invoice Nudge, days after the due date |
| `invoice_nudge_1_text` / `_2_` / `_3_` | built in | Invoice Nudge |
| `invoice_receipt_text` | built in, set to `off` to send none | Invoice Nudge |
| `brief_lookback_hours` | 24 | Morning Brief |
| `brief_skip_if_empty` | no | Morning Brief |

Numbers are read so that a configured `0` is honoured. That matters here: setting the waits to `0` is how you test a three step cadence in one sitting instead of over nine days. A wait of a day or more lands at 10am local. A shorter wait fires as soon as it is due.

Message templates accept `{name}`, `{business}`, `{owner}`, `{amount}`, `{link}`, and `{job}` or `{due}` depending on the workflow.

---

## Quote Chaser

```
curl -X POST https://YOUR-HOST/webhook/quote-sent \
  -H "Content-Type: application/json" \
  -d '{"phone":"+1XXXXXXXXXX","name":"Test Customer","amount":"1850","job":"water heater replacement","quote_url":"https://example.com/q/1"}'
```

| # | Check | Expect |
| --- | --- | --- |
| 1 | Response | `{"ok":true}` immediately, before any texting happens |
| 2 | `contacts` table | A row for that phone, stage `quoted` |
| 3 | `cadences` table | A row, workflow `quote_chaser`, step 0, status `active` |
| 4 | Owner alert | You get a text saying the quote chase started, with name, number and amount |
| 5 | Nudge 1 | Arrives after the configured wait, at 10am local if the wait is a day or more. Ends with the STOP footer |
| 6 | `cadences` step | Goes to 1 |
| 7 | **Reply STOP behaviour** | Send any reply from the test phone. Cadence status should flip to `stopped_reply` and nudge 2 should never send. This is the one worth watching, because it proves the inbound router stops a cadence it was never told about |
| 8 | Bad phone | Post with `"phone":"123"`. Should respond `{"ok":true}` and do nothing else. No contact row, no cadence |
| 9 | Full run, no reply | Let all three nudges send. Cadence closes as `finished_no_reply` and you get the summary alert |

---

## Invoice Nudge

Two entry points in one workflow. One for sending an invoice, one for marking it paid.

```
curl -X POST https://YOUR-HOST/webhook/invoice-sent \
  -H "Content-Type: application/json" \
  -d '{"phone":"+1XXXXXXXXXX","name":"Test Customer","amount":"640","invoice_id":"INV-1042","invoice_url":"https://example.com/i/1042","due_date":"2026-09-21"}'
```

| # | Check | Expect |
| --- | --- | --- |
| 1 | Response | `{"ok":true}` immediately |
| 2 | `contacts` table | A row for that phone, stage `invoiced` |
| 3 | `cadences` table | A row, workflow `invoice_nudge`, step 0, status `active` |
| 4 | Owner alert | A text naming the customer, the amount, the invoice id and the due date |
| 5 | Reminder 1 | Lands 10am on the due date. Names the amount and the due date in words, not an ISO string |
| 6 | **Due date already past** | Post again with `"due_date":"2026-01-01"`. Reminder 1 should fire straight away rather than never, because a date in the past clamps to now |
| 7 | **No due date** | Post with no `due_date`. Reminder 1 should be `invoice_due_days` out, default seven days |
| 8 | Reminder 2 and 3 | Land at the configured gaps after the due date, each one only if the cadence is still `active` |
| 9 | **Reply stops it** | Reply from the test phone. Status flips to `stopped_reply`, no further reminders |
| 10 | Bad phone | Post with `"phone":"123"`. Responds `{"ok":true}`, writes nothing |
| 11 | Full run, no reply | Cadence closes `finished_no_reply` and you get the summary alert |

Then mark it paid:

```
curl -X POST https://YOUR-HOST/webhook/invoice-paid \
  -H "Content-Type: application/json" \
  -d '{"phone":"+1XXXXXXXXXX","name":"Test Customer","amount":"640"}'
```

| # | Check | Expect |
| --- | --- | --- |
| 12 | Response | `{"ok":true}` immediately |
| 13 | `cadences` | The `invoice_nudge` row for that phone goes to `stopped_paid` with a `stopped_at` |
| 14 | **Scope of the stop** | Start a Quote Chaser for the same number first, then post invoice-paid. The quote cadence must still be `active`. Only invoice reminders stop |
| 15 | `contacts` | Stage goes to `paid` |
| 16 | Receipt text | The customer gets a short thank you naming the amount |
| 17 | Receipt off | Set `invoice_receipt_text` to `off`, post again, no customer text but the owner alert still fires |
| 18 | Owner alert | A text saying payment was received and reminders stopped |

---

## Morning Brief

This one is on a schedule, not a webhook. It runs at 7am in the n8n instance time zone, not the `timezone` value in config. Check the instance setting if it arrives at the wrong hour.

To test it now, open the workflow and use **Execute workflow** rather than waiting for 7am.

| # | Check | Expect |
| --- | --- | --- |
| 1 | It runs | One execution, no errors, four table reads each returning the whole table once rather than once per row |
| 2 | The text | You get one message through Core 3, so it follows whatever `alert_channel` is set to |
| 3 | Waiting on you | Text in from a number that you do not reply to. The next brief should name that number first |
| 4 | Answered | Reply to that number. It should drop off the waiting list |
| 5 | Counts | New contacts, texts in and out, follow ups started and still running should match what the tables say |
| 6 | Review numbers | If the Review Engine is installed, asks and scores from the window show up with an average |
| 7 | Quiet day | With nothing in the window, the text reads as a quiet day rather than a list of zeros |
| 8 | `brief_skip_if_empty` | Set it to `yes` on a quiet day. The run should complete and send nothing |
| 9 | `brief_lookback_hours` | Set it to 1. Counts should shrink to the last hour |

The brief reads the `createdAt` that every data table row carries, so none of these counts depend on a column anyone has to remember to fill in.

---

## What to write down

For each numbered check: pass or fail, the timestamp, and what you actually saw. That log is what turns this from a template into evidence, and it is the thing that made the Lead Response repo worth reading.

If something fails, the useful detail is which node threw and what the input JSON was at that node, not just that it broke.
