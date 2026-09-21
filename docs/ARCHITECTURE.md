# Architecture

How the fifteen workflows fit together, what each one promises the others, and
what happens when a piece fails.

## The shape

Three kinds of workflow. Entry points catch something from the outside world.
The spine decides what to do about it. Shared services are the only things
allowed to touch Twilio.

```
  ENTRY POINTS                 SPINE                    SHARED SERVICES
  ------------                 -----                    ---------------

  Lead Response A  ---\
  POST /lead           \
                        >--- Lead Pipeline ---------->  Core 1: Send SMS
  Lead Response B  ---/       dedupe                    every outbound text
  POST /voice-in              immediate reply           quiet hours, opt-out
  POST /voice-status          owner call                STOP footer, logging
  POST /bridge-connect        cadence: 10m, 50m, 9am         |
                                   |                         v
                                   |                    Twilio Messaging
  Core 2: Inbound SMS Router       |
  POST /sms-in  ------------------>|                    Core 3: Owner Alert
  STOP START HELP reply            |                    text, email fallback
  stops any active cadence         |                         ^
                                   \-------------------------/
  Quote Chaser     POST /quote-sent          -----------> Core 1 + Core 3
  Invoice Nudge    POST /invoice-sent                     Core 1 + Core 3
                   POST /invoice-paid
  Morning Brief    07:00 schedule            -----------> Core 3
  Appointment      POST /appointment-booked  -----------> Core 1 + Core 3
  Reminder         quiet hours resolved before the wait

  Entry forms      hosted n8n forms, one per action, POST to the three
                   webhooks above so a person can start one from a phone

  Core 0: Error Handler  <---- every workflow above points its error handler here
```

## Why shared services

`Core 1: Send SMS` is the only node path in the system that calls Twilio to
send a message. Everything that wants to text a customer calls it instead.
That is what makes the rules enforceable in one place rather than remembered in
nine:

- quiet hours in the business's own time zone
- the opt-out check, before the send rather than after
- the STOP footer on every message, because the registered A2P campaign
  description promises exactly that
- one row written to `messages` for every attempt, sent or refused

Add a tenth workflow tomorrow and it inherits all four by calling Core 1. That
is the whole reason for the indirection.

`Core 3: Owner Alert` is the same idea for the other direction. It is the only
way to reach the owner, and it owns the decision about text versus email.

## The contracts

These are stable. A change to any of them is a breaking change for every caller.

| Workflow | Called as | Inputs |
| --- | --- | --- |
| Core 1: Send SMS | sub-workflow | `phone`, `body`, `kind`, `skip_quiet_hours` |
| Core 3: Owner Alert | sub-workflow | `event`, `text`, `urgency`, `phone` |
| Lead Pipeline | sub-workflow | `phone`, `name`, `source`, `message` |
| Core 2: Inbound SMS Router | `POST /sms-in` | Twilio inbound webhook |
| Lead Response A | `POST /lead` | website form fields |
| Lead Response B | `POST /voice-in`, `/voice-status`, `/bridge-connect` | Twilio voice webhooks |
| Quote Chaser | `POST /quote-sent` | `phone`, `name`, `amount`, `quote_id` |
| Invoice Nudge | `POST /invoice-sent`, `/invoice-paid` | `phone`, `name`, `amount`, `invoice_id`, `invoice_url`, `due_date` |
| Morning Brief | 07:00 schedule | none |
| Appointment Reminder | `POST /appointment-booked` | `phone`, `name`, `when`, `job`, `address` |

`kind` on Core 1 is what separates a reply from marketing, which is what lets
one send path apply quiet hours correctly to both.

## The data model

Five tables. Every row gets `id`, `createdAt` and `updatedAt` from n8n, and
nothing in the system depends on a column a person has to remember to fill in.

| Table | Holds | Written by |
| --- | --- | --- |
| `config` | every setting, one row | Setup, read by all |
| `contacts` | one row per phone number, opt-out state | Core 1, Core 2, Pipeline |
| `messages` | every message in and out, with status | Core 1, Core 2, Core 3 |
| `cadences` | every running follow-up sequence | Pipeline, Quote Chaser, Invoice Nudge, closed by Core 2 |
| `reviews` | review asks and scores | the review workflow, read by Morning Brief |

## The coordination point

`cadences` is the only place the workflows talk to each other, and it is worth
understanding because it is the design decision the rest depends on.

When a follow-up sequence starts, whichever workflow started it writes a row:
phone, which workflow, what step, `status = active`.

When an inbound text arrives, `Core 2` closes **every** active cadence for that
number. It filters on `phone` and `status`, and deliberately not on `workflow`.

The consequence is that a customer replying to a quote nudge also stops an
invoice reminder and a lead follow-up, without the router knowing those
workflows exist. Quote Chaser and Invoice Nudge were added later and needed no
change to Core 2 at all. A workflow added next year will behave the same way.

The sleeping side of this matters as much. A pipeline waiting on a `Wait` node
does not trust what it knew when it went to sleep. It wakes, re-reads the
cadence row, and stands down if something closed it while it was asleep. This
is observable in the test log: a reply landed at 21:54:12, the pipeline woke six
seconds later to send nudge 2, re-checked, found the cadence stopped, and sent
nothing.

## Failure modes

The question for each piece is not whether it can fail but whether it fails
loudly.

| If this fails | What happens | How you find out |
| --- | --- | --- |
| Twilio refuses an outbound text | Core 1 logs the row as failed, the caller continues | `messages` row with a failed status |
| Twilio refuses the owner's alert text | Core 3 falls back to email even when the channel is set to sms-only | the email arrives |
| Any node throws | the workflow's error handler fires Core 0, which alerts the owner | a text, or an email if the text will not go |
| The owner does not answer the bridge call | the cadence continues, nothing is lost | the follow-up texts keep going |
| A duplicate lead arrives | the pipeline dedupes on phone inside the window | the second one is logged, not sent |
| A lead arrives for an opted-out number | the send is refused and logged, the owner is still told | owner alert, no customer text |

The one that was worth finding: owner alerts used to send from the business
number, so an owner who had ever texted STOP to their own line stopped
receiving alerts and nothing said so. It failed closed and quiet, which is the
worst available shape for this system. `docs/TEST-RESULTS.md` has the write-up.
That is why Core 3's fallback exists at all.

## Deliberate limits

**One business per n8n instance.** n8n's license does not allow running a
customer's workflows on your own instance, so multi-tenancy is not a feature
that was skipped, it is one that is not permitted. Every design choice here
assumes a single business, which is also why `config` is one row rather than a
table keyed by tenant.

**Quiet hours has one exception.** Someone who made contact thirty seconds ago
gets the immediate reply whatever the hour, because that is a reply and not
marketing. Every later message in the cadence respects quiet hours normally.

**HELP never reaches the workflow.** Twilio answers HELP itself for any number
inside a messaging service. The branch still exists for numbers that are not,
and the per-business wording is set in the messaging service opt-out settings.
This is in the setup guide because it is not discoverable.

## Changing anything

The bundle at `workflows/lead-response-workflows.json` is generated from
`workflows/individual/` and is never edited by hand. After changing a workflow:

```
python3 scripts/build_bundle.py     # regenerate the bundle
python3 scripts/validate.py         # check the repo still tells the truth
```

CI runs the same two commands on every push. `validate.py` checks that the
README's node counts match the files, that every data table used is created by
setup, that every placeholder is documented, that no connection points at a
node that does not exist, and that nothing shaped like a credential or a real
phone number made it in.
