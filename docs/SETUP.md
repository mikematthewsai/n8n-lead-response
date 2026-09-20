# Lead Response: setup guide

Two parts. The first is your runbook for installing it in a business's account. The second is the single page you leave with the owner.

Written from what actually happened during the first live install on Sep 17, 2026, not from a plan.

---

# Part one: your install runbook

Budget an hour. Most of it is waiting on their signups, not on you.

## Before the call

Have ready: the workflow bundle (lead-response-workflows.json), their business name, their time zone, the cell number that should get the lead alerts, and the four message texts if they want anything other than the defaults.

## On the call

**1. They create an n8n account.** app.n8n.cloud, Starter plan. It is their card, their login. Do not use your own account, because n8n's license does not allow you to run their workflows on your instance, and because the promise is that they own this.

**2. They create a Twilio account and get a number,** or you use the number they already have if it can be pointed at a webhook. A brand new number needs A2P registration before it can text, and that takes a few days to clear, so if they are in a hurry use a number that is already registered. This is the single most common thing that will delay a launch, so ask about it first, not last.

**3. Import the workflows,** in this order, because each one refers to the ones before it: Setup, Error Handler, Send SMS, Owner Alert, Lead Pipeline, Inbound Router, Website form, Phone line.

After import, four references need repointing to the workflows you just created, wherever the bundle shows a placeholder: __WF_ERROR__, __WF_SENDSMS__, __WF_ALERT__, __WF_PIPELINE__. In the n8n screen these are the Execute Workflow nodes and the error workflow in each workflow's settings. Pick the right one from the dropdown. If you are doing this often, drive it through the instance API instead and rewrite the IDs on the way in, which is what was done on the first build.

**4. Open the workflow called Setup,** edit the one node called "Your business settings", and put in their real details. Business name, time zone, quiet hours, owner name, owner cell, business number, whether alerts go by text or email or both, owner email, and the four customer messages. Then run it once. It creates the four tables and writes the settings row. It is safe to run again later when they want to change something.

**5. They paste their Twilio Account SID and Auth Token** into a new Twilio credential, and click through the Google sign in for the Gmail credential. You do not type these and you do not need to see them.

**6. Attach the credentials** to the Twilio nodes (Error Handler, Send SMS, Owner Alert, Lead Pipeline) and the Gmail nodes (Error Handler, Owner Alert). Then publish all seven, in the same order as the import. n8n will refuse to publish anything whose credentials are missing or whose sub-workflows are not published yet, which is a useful check rather than an obstacle.

**7. Point the phone number at it,** in the Twilio console:
- Messaging, "a message comes in": POST to their n8n address followed by /webhook/sms-in
- Voice, "a call comes in": POST to their n8n address followed by /webhook/voice-in

If the number sits inside a Twilio Messaging Service, check the service's inbound setting. If it is set to send a webhook, that overrides the number's own setting and your number will never see its traffic. Either set the service to defer to the number's own webhook, or point the service itself at n8n. Getting this wrong is silent, and it is the thing that will waste your afternoon.

While you are in the messaging service, open its opt-out settings and fix the HELP reply. A number inside a messaging service never passes HELP through to the workflow, because Twilio answers it first, so whatever is written there is what the customer actually reads. Out of the box it is a generic unsubscribe line with no business name in it. Put their business name and their phone number in it, and make it match the help text in the Setup workflow so the two never disagree. On a number with no messaging service the workflow answers HELP instead, which is why both exist.

**8. Run the tests with them holding their phone.** Submit a test lead with their own cell as the customer. They should get the instant text, the new lead alert, and a call. Then have them text back, and watch the follow up stop. Then STOP, then START. That five minutes is the demo, the proof and the close.

**9. Leave them part two below.**

## If something goes wrong later

Everything failed is visible in Executions inside their n8n. The Error Handler texts and emails on any failure, so point that at yourself during the first week if they will let you.

---

# Part two: the page you leave with the owner

## What this does for you

When somebody fills out your form or calls and you miss it, three things happen straight away. They get a text from your business number. You get a text telling you who it is and what they want. Your phone rings, and if you press one, you are talking to them.

If nobody answers them, it texts them again after ten minutes, again about an hour later, and one last time the next morning. The moment they text back, all of that stops and you take over.

## Changing what it says

Open your n8n, open the workflow called Setup, click the box called "Your business settings", and change the wording. Then click the play button once to save it. That is the whole thing. You are changing:

- the first text they get
- the ten minute follow up
- the one hour follow up
- the next morning follow up
- the line that plays in your ear when it rings you

You can also change your quiet hours and which cell gets the alerts in the same place.

## Things it does on its own that you should know about

It will not text anyone before eight in the morning or after eight at night, your time. The only exception is somebody who contacted you seconds ago, because that reply is what they are waiting for.

Every text ends with the opt out line. If someone texts STOP, they are out for good and nothing will ever text them again, even if they come back through your form later. You will still be told they came in, so you can call them yourself. If they text HELP they get your business name and number back.

If the same person comes in twice within a few minutes, it does not start over and it does not double text them. You just get told it was the same lead again.

## If it stops working

You will usually know because you stop getting the lead alerts. Everything that has happened is listed in your n8n under Executions, including anything that failed and why. If something breaks, it sends an alert automatically, so somebody knows without you having to notice.
