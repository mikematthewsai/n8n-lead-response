# Test results

Run against the live system on 2026-09-17, on a real Twilio number with a real handset, not in a simulator. Every result below has a timestamp in the original log.

## Passed, 11 of 13

| # | Test | Result |
| --- | --- | --- |
| 1 | Instant text to the customer on a new lead | Passed. About one second from lead to Twilio accepting. Delivered status confirmed on the handset |
| 2 | Owner alert fires on a new lead | Passed |
| 4 | Follow-up cadence opens on the lead record | Passed |
| 5 | Nudge 1 fires at exactly ten minutes | Passed |
| 6 | Customer reply stops the cadence | Passed, and this is the one worth reading. The reply landed at 21:54:12. The sleeping pipeline woke six seconds later to send nudge 2, re-checked the cadence, found it stopped, and stood down. Nudge 2 was never sent |
| 7 | STOP marks the contact opted out | Passed |
| 8 | START clears the opt-out | Passed |
| 9 | Quiet hours hold and reschedule | Passed |
| 10 | Error path raises an alert | Passed |
| 11 | Duplicate lead guard | Passed |
| 12 | Lead arriving for an opted-out number is refused and logged, owner still told | Passed |
| 13 | Missed call end to end | Passed at 23:01. Voice webhook fired, dial to owner returned no-answer, the workflow said its line and hung up, pipeline ran with source missed_call, customer texted and owner alerted, callback bridge correctly skipped |

## Not fully verified, 2

**Test 3, a true press-1 connect.** Closed as an accepted risk rather than run, because there was no second phone available. Everything up to the last inch is proven: the call placed, the whisper played, the digit received, the correct branch taken, the right customer number and caller ID handed to Twilio, and Twilio placing the second leg as its own call log entry. What is unverified is only two live parties hearing each other. The failure mode here would be loud rather than silent. Run it once with any second phone before demonstrating to a prospect.

**HELP.** Resolved differently than expected. Twilio answers HELP itself on a number inside a messaging service and never forwards it, so the customer is served but the workflow never sees the message. The reply wording is Twilio's generic unsubscribe line unless it is set per business in the messaging service opt-out settings, which is now a step in the setup guide. The workflow keeps its own HELP branch for numbers that are not in a messaging service.

## One real bug, found and fixed

The owner alert was being sent from the business number. When the owner's own cell was opted out of that number, Twilio refused the message and the entire lead errored, firing two error alarms and leaving the owner untold.

This was not just a test artifact. Any owner who texts STOP to their own line while experimenting would have silently stopped receiving lead alerts, which is the worst possible failure for this system because it fails closed and quiet.

Fix: in Core 3 Owner Alert, a refused text is now non-fatal. It is logged as failed and falls back to email automatically, even when the channel setting is sms-only. Re-tested and passed. Carried into template version 1.1.

## Design decisions worth knowing

The STOP footer goes on every customer text, not only the first, because the registered A2P campaign description promises exactly that.

The owner is not treated as a customer, but only where it matters. An owner texting their own business line still stops a running cadence and updates the record. It just does not send them an alert about their own message. The first version of this guard short-circuited everything from the owner's cell, which was wrong, and was replaced.

---

# Test results: the three add ons

Run against the live system on 2026-09-20, on the same real Twilio number and handset as
above. Every result below was checked by reading the `contacts`, `cadences` and `messages`
tables and the n8n execution log directly, not by trusting the text that arrived. Where a
text is cited, it was confirmed delivered on the handset.

Waits were set to 0 in `config` so a three step cadence runs in one sitting. They were
restored to 2, 3, 4 and 3, 4 afterwards.

## Two real bugs, found by running it

**Every filtered data table node used a match type n8n rejects.** All 20 filtered nodes in
Quote Chaser and Invoice Nudge carried `matchType: "allFilters"`. n8n accepts only
`allConditions` or `anyCondition`. It failed in the worst available way: n8n imported the
nodes without complaint, silently discarded the per-condition comparison operators because
the match type was unrecognised, and then threw `unexpected match type` at runtime. The
webhook had already answered `{"ok":true}` by then, because `Respond` sits before the
cadence, so from the outside the call looked like a success while the workflow died at the
first contact lookup and sent nothing.

Worth carrying: on these workflows a 200 means the webhook answered, not that the run
succeeded.

Second-order trap found while fixing it: patching an **active** workflow through the API
does not reload it. n8n kept executing the cached old version, so a run seven minutes after
the fix failed identically. It needs a deactivate and reactivate.

`scripts/validate.py` now checks every data table filter for a match type n8n accepts and a
comparison operator on every condition, and CI runs it on every push.

**Morning Brief could never report a quiet day.** Every count in the brief is windowed
except two: conversations waiting on you, and follow ups still running. Both are standing
backlog and can be non-empty for weeks. The quiet-day test counted them anyway, so the brief
was never empty and `brief_skip_if_empty` could never fire. Proven with the window set to 36
seconds and the setting on: it still sent. Quiet is now decided on activity inside the
window only, and a quiet brief still names anyone outstanding.

## Quote Chaser: 9 of 9

| # | Check | Result |
| --- | --- | --- |
| 1 | `{"ok":true}` before any texting | Passed |
| 2 | `contacts` row, stage `quoted` | Passed |
| 3 | `cadences` row, `quote_chaser`, step 0, active | Passed |
| 4 | Owner alert with name, number and amount | Passed. "Quote chase started for Test Customer (303) 961-7720 at $1850 for water heater replacement." |
| 5 | Nudge 1 with the STOP footer | Passed |
| 6 | Cadence step advances | Passed, reached step 3 |
| 7 | **Reply stops the cadence** | Passed, and this is the one worth reading. Reply landed 21:38:08. Cadence flipped to `stopped_reply` at 21:38:10. Nudge 2 was due 21:40:02; the sleeping execution woke, re-read the cadence, found it stopped and stood down. Status success, not error. No nudge 2 in `messages` |
| 8 | Bad phone writes nothing | Passed. `{"ok":true}`, and cadences, contacts and messages all unchanged |
| 9 | Full run, no reply | Passed. Whole cadence 21:33:16 to 21:33:18, closed `finished_no_reply`, summary alert sent. All five texts confirmed delivered on the handset |

## Invoice Nudge: 18 of 18

| # | Check | Result |
| --- | --- | --- |
| 1 | `{"ok":true}` immediately | Passed |
| 2 | `contacts` stage `invoiced` | Passed |
| 3 | `cadences` row, `invoice_nudge`, active | Passed |
| 4 | Owner alert names customer, amount, invoice id, due date | Passed |
| 5 | Due date in words, not an ISO string | Passed. "due Thursday Jan 1", not "2026-01-01" |
| 6 | **Due date already past clamps to now** | Passed. Reminder 1 fired immediately rather than never |
| 7 | **No due date uses `invoice_due_days`** | Passed. `waitTill` came back `2026-09-27T14:00:00Z`, which is seven days out landing at 10am local |
| 8 | Reminders 2 and 3 at the configured gaps | Passed |
| 9 | **Reply stops it** | Passed. Inbound 22:01:29, cadence `stopped_reply` at 22:01:32 |
| 10 | Bad phone writes nothing | Passed |
| 11 | Full run, no reply | Passed, closed `finished_no_reply` with summary |
| 12 | `invoice-paid` responds ok | Passed |
| 13 | Cadence goes `stopped_paid` with a timestamp | Passed |
| 14 | **Paid stops only the invoice cadence** | Passed, and this is the check the whole design rests on. A `quote_chaser` cadence and an `invoice_nudge` cadence were opened on the same number, then `invoice-paid` was posted. The invoice cadence went `stopped_paid`; the quote cadence was still `active` |
| 15 | `contacts` stage `paid` | Passed |
| 16 | Receipt text to the customer | Passed |
| 17 | `invoice_receipt_text` set to `off` | Passed. No customer receipt written, owner alert still sent |
| 18 | Owner alert on payment | Passed. "Payment received from Scope Test (303) 961-7720 for $640. Reminders stopped." |

## Morning Brief: 8 of 9, one partial

| # | Check | Result |
| --- | --- | --- |
| 1 | Runs clean, each table read once | Passed. All nine nodes ran exactly 1x, so `executeOnce` is doing its job |
| 2 | Sends through Core 3 | Passed |
| 3 | Names the number waiting on you | **Partial.** The number was named, but third in the list rather than first. The waiting list is emitted in table order, not newest first. Cosmetic, not fixed |
| 4 | An answered number drops off the list | Passed |
| 5 | Counts match the tables | Passed. Recounted independently: 3 texts in from 1 number, 8 follow ups started, closed 2 `finished_no_reply`, 2 `stopped_reply`, 3 `stopped_paid`. All matched |
| 6 | Review numbers | Passed by absence. Four review rows exist but all fall outside the 24 hour window, and the review lines were correctly not shown |
| 7 | Quiet day reads as quiet | Failed first, fixed, then passed. "Morning Mike. Quiet 0.01 hours, nothing new came in. 2 conversations are still waiting on you: ..." |
| 8 | `brief_skip_if_empty` suppresses the send | Failed first, fixed, then passed. Run completed, message count unchanged |
| 9 | `brief_lookback_hours` shrinks the counts | Passed |

## Known behaviour worth knowing

The brief **counts itself**. It reported 20 texts sent, and the moment it sends, it is 21.
And because it goes to the owner's own cell, sending it takes the owner's number off the
next brief's waiting list. Neither is wrong, both surprise you once.

The waiting list is not ordered by recency (check 3 above).

## Still not covered

Nothing in the three add ons has been run against a second live handset, so every "customer"
text above landed on the owner's own phone. The messages are distinguishable by wording and
every one was confirmed delivered, but a true two-party test has not been done.

---

# Appointment Reminder, run live on 2026-09-20

Built, run against the live system and the owner's own handset the same evening, and
changed twice because of what the run showed. Config was returned to defaults afterwards.

Test setup: the reminder offsets are config driven, so they were shortened for the sitting
(`appt_reminder_1_hours` 0.15 and `appt_reminder_2_hours` 0.02, about nine minutes and one
minute) and the appointment was booked eleven minutes out. Quiet hours were temporarily
moved from 20:00 to 23:30 for the third run, for the reason below, and restored afterwards.

| # | Check | Result |
| --- | --- | --- |
| 1 | `POST /appointment-booked` responds | Passed. `{"ok":true}` immediately, before anything sends |
| 2 | Owner alert | Passed. "Appointment booked: Reminder Test ... Reminders set." with the time in words |
| 3 | Contact and cadence rows | Passed. Contact stage `booked`, cadence `appointment_reminder` step 0 status active |
| 4 | Reminder 1 | Passed on the second run. See the quiet hours finding below |
| 5 | Reminder 2 | Passed on the third run. See the two findings below |
| 6 | Cadence closes | Passed on the third run, `finished` at step 2, with the owner summary |
| 7 | Run completes clean | Passed, execution status success |

## Finding 1: quiet hours made the reminder useless

First run, at 21:26 local. Reminder 1 was written to the messages table as
`deferred_quiet_hours` and the send path parked it until 08:00 the next morning.

That is correct behaviour for a nudge and wrong for a reminder. A reminder deferred to the
morning can arrive after the appointment it was reminding about. The send path cannot know
that, because it does not know there is an appointment.

Fixed in the workflow rather than in the send path. Reminder times are now resolved against
quiet hours before the wait: a reminder inside quiet hours moves to the moment quiet hours
end, and is dropped entirely if that is not before the appointment. The send path is then
told not to defer it again.

## Finding 2: a skipped reminder left the cadence open forever

Second run. The two shortened offsets were less than five minutes apart, so the second
reminder was correctly suppressed as a duplicate. But the branch that suppresses it ended
the flow without touching the cadence row, which stayed `active` with no execution left to
close it.

A cadence stuck open is not harmless. It is what the brief counts as a follow up still
running, and it is what the inbound router looks for.

Fixed by adding a tidy step that both suppressed branches run into. It closes the row only
if it is still `active`, so a cadence already stopped by a customer reply keeps
`stopped_reply` rather than being overwritten with `finished`.

## What is not covered

Both reminders landed on the owner's own handset, so a true two party test has not been
done. The default offsets of 24 and 2 hours have not been run at full length, only the
shortened ones. The path where an appointment is booked inside quiet hours for a time
before quiet hours end, which should drop both reminders, was reasoned through but not run.
