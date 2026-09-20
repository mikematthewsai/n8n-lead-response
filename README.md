# Lead Response

[![checks](https://github.com/mikematthewsai/n8n-lead-response/actions/workflows/validate.yml/badge.svg)](https://github.com/mikematthewsai/n8n-lead-response/actions/workflows/validate.yml)

Eleven n8n workflows that make sure a small business never loses a lead to a missed call, and then keeps following up after it.

This is not a demo. It was extracted from a live production install running on n8n Cloud against a real Twilio number, tested on real handsets, and it found a real bug in the process. Credentials are stripped and identifiers are replaced with placeholders.

## What it does

A lead arrives, either from a website form or from someone calling and getting no answer.

Within about a second the customer gets a text from the business number. At the same time the owner gets a text saying who it is, their number and what they said. Then the owner's phone rings, a short recorded line says there is a new lead, and pressing 1 connects them straight to the customer with the business number showing as caller ID rather than the owner's personal cell.

If the owner does not pick up, nothing is lost. The system texts the customer again at ten minutes, again fifty minutes after that, and once more at nine the next business morning. Then it stops and tells the owner how it went.

The moment the customer replies, the whole sequence ends. No more automatic texts. The owner gets the message forwarded and is in a normal conversation with a real person. Getting out of the way is the thing most automated follow-up gets wrong.

STOP, START and HELP are handled. Quiet hours are enforced in the business's own time zone, with one deliberate exception: someone who just made contact thirty seconds ago gets the immediate reply regardless of the hour, because that is a reply, not marketing.

## The eight workflows

Import in this order. Each one refers to the ones before it.

| # | Workflow | Nodes | What it is |
| --- | --- | --- | --- |
| 1 | Setup: tables and settings | 11 | Creates the five data tables and writes the config row |
| 2 | Core 0: Error Handler | 5 | Every other workflow points its error handler here |
| 3 | Core 1: Send SMS | 16 | The single send path. Quiet hours, opt-out check, STOP footer, delivery logging |
| 4 | Core 3: Owner Alert | 9 | Alerts the owner. Falls back to email if the text is refused |
| 5 | Lead Pipeline | 32 | The spine. Dedupe, immediate reply, owner call, the follow-up cadence |
| 6 | Core 2: Inbound SMS Router | 19 | Inbound texts. STOP, START, HELP, reply detection, cadence stop |
| 7 | Lead Response A: Website form | 3 | Webhook entry point for a form |
| 8 | Lead Response B: Phone line | 13 | Voice entry point. Missed call detection and the press-1 bridge |

108 nodes total. Five data tables: contacts, messages, cadences, config, reviews.
The first four are used by the eight below. `reviews` is created here so that Morning Brief works on a clean install.

## The three add ons

These sit on top of the eight. Each one is self contained, reuses Core 1, Core 3 and the `cadences` table, and needs no change to anything above it. A reply to any of them stops it, because the inbound router closes every active cadence for a number without caring which workflow opened it.

| # | Workflow | Nodes | What it is |
| --- | --- | --- | --- |
| 9 | Quote Chaser | 28 | A quote goes out and nobody answers. Three nudges, then it gives up and tells the owner |
| 10 | Invoice Nudge | 38 | Same shape for money owed, keyed off the due date. A second entry point marks it paid, stops the reminders and sends a receipt |
| 11 | Morning Brief | 9 | One text at 7am. What came in, what is still waiting on a reply, what follow ups are running, what the review scores did |

Morning Brief reads the `reviews` table, which setup creates and which the review workflow in the paid version writes to. On an install without it the review lines are simply absent from the brief.

They are generated rather than extracted from a live install, and they have not been run yet. [docs/TEST-PLAN.md](docs/TEST-PLAN.md) is the script to run at the keyboard, written before the results exist rather than after. Every setting they read has a default, so they run on an existing install without touching the config table.

## Install

Read [docs/SETUP.md](docs/SETUP.md). It is the runbook from the first real install, written from what happened rather than from a plan, and it budgets an hour, most of it waiting on signups.

You need an n8n instance with Data Tables, a Twilio account, and a number that is already A2P registered. A brand new number cannot text until A2P clears, which takes days. That is the single most common thing that delays a launch, so check it first.

`workflows/lead-response-workflows.json` is the importable bundle of all eleven. It is generated from `workflows/individual/` by `scripts/build_bundle.py` and never edited by hand, so the two can never drift apart.

After import, four cross references need repointing. They appear in the bundle as `__WF_ERROR__`, `__WF_SENDSMS__`, `__WF_ALERT__` and `__WF_PIPELINE__`.

Four values need filling in: `__OWNER_CELL__`, `__BUSINESS_NUMBER__`, `__OWNER_EMAIL__`, `__N8N_HOST__`.

## Does it work

[docs/TEST-RESULTS.md](docs/TEST-RESULTS.md) has the log. 11 of 13 tests passed on the live system with timestamps. Two are not fully verified and both are written up there rather than quietly left out, including exactly which last inch of the press-1 connect is unproven and why.

The bug that was found is written up too. The owner alert was being sent from the business number, so an owner who had ever texted STOP to their own line would have silently stopped receiving lead alerts. It failed closed and quiet, which is the worst way for this particular system to fail. Fixed in Core 3 and re-tested.

## Docs

- [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md), how the pieces fit, the contracts between them and what happens when each one fails
- [docs/HOW-IT-WORKS.md](docs/HOW-IT-WORKS.md), plain English, written for a business owner rather than a developer
- [docs/SETUP.md](docs/SETUP.md), the install runbook plus a single page to leave with the owner
- [docs/TEST-RESULTS.md](docs/TEST-RESULTS.md), what was tested, what passed, what did not, and the bug
- [docs/TEST-PLAN.md](docs/TEST-PLAN.md), the unrun script for the three add ons

## Limits

This is built for one business per instance. n8n's license does not allow running a customer's workflows on your own instance, so each business needs their own.

HELP is answered by Twilio itself on any number inside a messaging service, so the workflow never sees it. Set the wording in the messaging service opt-out settings.

The press-1 bridge is proven up to the point where two live parties hear each other. Run it once with a second phone before you demo it.

## License

MIT. Use it, sell it, change it.

Built by [Mike Matthews](https://github.com/mikematthewsai).
