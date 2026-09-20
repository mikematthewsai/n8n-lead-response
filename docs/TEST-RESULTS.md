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
