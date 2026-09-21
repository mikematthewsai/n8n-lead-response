# Standalone templates

The workflows in `workflows/` are a system: they share one send path, one owner alert and a set of data tables, which is what makes them reliable together and also why none of them can be imported on its own.

These are single workflows that stand alone. Each one needs nothing but its own credentials, so they can go in n8n's public template library and be imported in one step.

| Template | What it does | Tested |
| --- | --- | --- |
| [quote-chaser-sms-twilio.json](quote-chaser-sms-twilio.json) | Chases an unanswered quote with up to three SMS nudges and stops the moment the customer replies. No database: before each nudge it asks Twilio whether the customer has texted the business number since the quote went out | 2026-09-20, live, three runs below |
| [owner-brief-sms-twilio.json](owner-brief-sms-twilio.json) | Texts the owner a short summary every morning at 7: customer texts in, texts out, anything undelivered, and who is still waiting on a reply, newest first. No database: it reads the Twilio message log directly | 2026-09-20, live, three runs below |
| [appointment-reminders-sms-quiet-hours.json](appointment-reminders-sms-quiet-hours.json) | Sends a booking confirmation and reminders 24 hours and 2 hours before each appointment, and never texts during quiet hours. Every send time, quiet hours included, is planned the moment the booking arrives, so the waits never have to re-check anything | 2026-09-21, live, four runs plus eleven scheduling cases below |

## Quote chaser, test runs on 2026-09-20

Run against a real Twilio number with the waits set to 0.002 days (about three minutes), then set back to the defaults of 2, 3 and 4 days before export.

| Run | Setup | Result |
| --- | --- | --- |
| A | Customer never replies | Passed. Start alert to the owner, three nudges about three minutes apart, then the closing alert. All three reply checks ran against the Twilio API without error |
| B | Customer replies after nudge 1 | Passed. The second reply check found the inbound text, the owner got "replied ... chase stopped", and nudge 2 never sent |
| C | Phone number is `123` | Passed. The webhook answered `{"ok":true}` and nothing was sent |

The exported file was checked against the tested workflow node by node: every node's parameters and the connections hash identically, ignoring generated ids and credential references.

What is not covered: both parties were the same handset, the default multi day waits were not run at full length, and the 10am landing time was not observed live because the test waits were under a day.

## Owner brief, test runs on 2026-09-20

Run against the same Twilio number, triggered by hand instead of waiting for 7am.

| Run | Setup | Result |
| --- | --- | --- |
| A | First draft, 24 hour lookback | Found a bug. The only texts that day were between the owner's cell and the business number, and the brief said "5 texts in from 0 numbers. 42 sent." The owner's own texts were counted as traffic but not as a person |
| B | Owner texts excluded from the counts, 24 hour lookback | Passed, but it listed two waiting customers with no line about traffic. Quiet was still judged on all texts rather than customer texts. Fixed so quiet means no customer texts either way |
| C | Same fix, 24 hour lookback | Passed. "Quiet, nothing came in or went out. Still waiting on you:" followed by the two customers whose last text had no reply |
| D | Lookback set to 168 hours to pull in real customer traffic | Passed. "2 texts in from 2 numbers. 1 sent. Waiting on you, newest first:" with day and time on each |

After testing, the lookback went back to 24 hours and both phone numbers went back to placeholders. The exported file hashes identically to the workflow in n8n, apart from credential references, which are removed.

What is not covered: the 7am schedule itself was not observed firing, a day with undelivered texts did not come up, and the list was never long enough to show the "plus N more" ending.

## Appointment reminders, test runs on 2026-09-21

Live runs against the same Twilio number, with the reminder hours shrunk to minutes so each run finished in under 25 minutes.

| Run | Setup | Result |
| --- | --- | --- |
| A | Appointment 16 minutes out, reminders at 12 and 6 minutes before | Passed. Confirmation sent at once. Reminder 1 was correctly skipped because it would have landed within 5 minutes of booking. Reminder 2 sent on time and the run ended |
| B | Appointment 20 minutes out, reminders at 12 and 6 minutes before | Passed. Confirmation, reminder 1 and reminder 2 all sent at their planned times |
| C | Phone number is `123` | Passed. The webhook answered with the reason, the owner got a text saying why, and nothing went to the customer |
| D | Booked at 11:30 PM inside a live quiet window of 11:00 to 11:45 PM, appointment at 11:58 PM | Passed. The confirmation waited and went out at 11:45:00, the moment quiet hours ended. Reminder 1 fell inside quiet hours, moved earlier, landed in the past and was skipped. Reminder 2 sent at 11:52 |

The planning code also went through eleven scheduling cases in a local harness with the clock frozen, using the real defaults (24 and 2 hours, quiet 8 PM to 8 AM):

| Booked | Appointment | Planned |
| --- | --- | --- |
| Mon 10:00 | Thu 14:00 | Confirmation Mon 10:00, reminders Wed 14:00 and Thu 12:00 |
| Mon 10:00 | Tue 09:00 | Confirmation now. The 24 hour reminder is already past, so it is skipped. The 2 hour reminder falls at 7 AM, inside quiet hours, so it moves to Mon 19:30 |
| Mon 10:00 | Thu 08:30 | Reminders Wed 08:30 and, moved out of quiet hours, Wed 19:30 |
| Mon 10:00 | Thu 07:00 | Both reminders fall inside quiet hours and move to 19:30 the evening before each |
| Mon 23:00 | Tue 09:00 | Confirmation waits until 8:00 AM. Both reminders would be past or inside quiet hours, so only the confirmation goes |
| Mon 23:00 | Tue 07:30 | Nothing is sent: the confirmation would arrive after quiet hours end, which is after the appointment |
| Mon 21:00 | Wed 21:30 | Confirmation Tue 08:00, reminders Tue 19:30 and Wed 19:30 |
| Mon 10:00 | Yesterday | Refused: the appointment time has already passed |
| Mon 10:00 | "next tuesday" | Refused: not an ISO date and time |
| Mon 10:00 | Phone written as 1 (404) 555-0123 | Accepted as +14045550123 |
| Mon 10:00 | Thu 15:00, daytime quiet window 1 to 2 PM | 2 hour reminder moves from 13:00 to 12:30 |

After testing, every setting went back to its default and the business details to placeholders. The exported file hashes identically to the workflow in n8n, apart from credential references, which are removed.

What is not covered: the full 24 hour wait was not run end to end, a number that has texted STOP was not tried (the Twilio nodes are set to carry on if a send fails), and daylight saving changes between booking and appointment were not tested live. A booking that lands too late for any text to fit before the appointment sends nothing and does not alert the owner.
