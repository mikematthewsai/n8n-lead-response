# The Lead Response system, in plain English

Written Sep 17, 2026, after building and testing it live.

## What it actually is

It is an assistant that lives between a small business's phone number and their customers, and its whole job is to make sure nobody who tries to reach that business gets ignored.

Here is what happens the moment a lead comes in, whether that lead filled out the website form or called and got no answer. Within a few seconds the customer gets a text from the business number that says something like "This is Mike's Plumbing, sorry we missed you. What's going on and what's the address?" At almost the same second the owner gets a text that says who it is, their number, and what they said. Then the owner's phone rings. When they pick up, a short recorded line tells them there is a new lead and to press one, and pressing one connects them straight to the customer, with the business number showing on the customer's phone rather than the owner's personal cell.

If the owner does not pick up, or picks up and does not press one, nothing is lost. The system waits ten minutes and texts the customer again. Fifty minutes after that, it tries once more. If there is still no answer it waits until nine the next business morning and sends one last note. Then it stops and tells the owner how it went.

The important part is what happens when the customer replies. The second they text anything back, the follow up sequence ends. No more automatic texts. The owner gets the customer's message forwarded to them and is now in a normal text conversation with a real person. The system gets out of the way, which is the thing most automated follow up gets wrong.

It also handles the legal and courtesy side by itself. Every text ends with "Reply STOP to opt out." If someone texts STOP they are marked as opted out and nothing is ever sent to them again, even if they come in as a brand new lead later. START puts them back. HELP sends back the business name and number. Nothing goes out before eight in the morning or after eight at night in the business's own time zone, with one exception: if someone just contacted the business thirty seconds ago, they get the immediate reply regardless of the hour, because that is a reply, not marketing.

Behind all of that it keeps a record. Every text in and out, who it was with, when, and whether it was delivered. Every contact with their status. Every follow up sequence and why it ended. And if any piece of it ever fails, it texts and emails the owner about it rather than failing quietly.

## Why a business owner would care

The pitch is not "automation." The pitch is that the first person to answer usually gets the job, and a plumber on a roof cannot answer. This answers in four seconds, every time, at two in the morning on a Sunday, and then it gets out of the way the moment a human takes over.

The second thing worth saying out loud is the stopping. Most owners have been burned by a marketing tool that kept texting a customer who had already booked. This one stops on the first reply, and I tested that.

## What it runs on

Two accounts, both in the business owner's name: n8n, which is where the workflows live, and Twilio, which is the phone and texting side. That matters for how it gets delivered, which is next.

## How to deliver it free

The constraint that shapes everything: n8n's license does not allow running other people's workflows on my own account without an enterprise license. So the clean way, which is also the honest way, is that every business gets their own n8n account and their own Twilio account. They own both. I set everything up inside them.

That makes the free offer easy to say: I build it in your account, you own it, and it is yours whether or not you ever pay me. Your only cost is the software itself, which is about twenty five dollars a month for n8n plus Twilio's charges for the number and the messages. Quote the Twilio side off your own bill, since you have real usage numbers and I do not want you guessing.

The delivery itself is about an hour with the owner, and most of that hour is waiting on account signups rather than anything technical.

First, they create the n8n account and the Twilio account while you are on the call. You cannot do this part for them and you should not want to, because the whole promise is that they own it.

Second, you import one file. All eight workflows come in at once.

Third, you run the workflow called Setup. It builds the four tables it needs and writes their business settings: their business name, their time zone, their cell, their number, their quiet hours, and the exact wording of all four customer texts. That one screen is the entire difference between a plumber and a roofer. Nothing else changes between businesses.

Fourth, they paste their own Twilio keys and click through the Google sign in. You never touch their credentials, and saying that out loud is worth something.

Fifth, you point their number at the system, one setting for texts and one for calls.

Sixth, and this is the part that makes it real, you run the tests with them while they hold their phone. They watch their own phone light up. That five minutes is the demo, the proof and the close all at once.

Last, you leave them a one page note on how to change what the texts say, so they never feel locked in.

Where free ends and paid begins is worth being clear about with yourself before you are asked. Free is the templates and the first setup. Paid is you running it for them: changing the wording when they want it changed, watching for failures, adding the other workflows, and being the person who fixes it at seven on a Friday. The free version is complete and genuinely works. What they are buying later is you, not the software.

## What they will ask, and what to say

**"Is this going to spam my customers?"**

No. It only ever texts somebody who contacted you first, and it stops the second they answer. Worst case, if a person never replies at all, they get three texts over about a day and then it never contacts them again. Every message tells them how to opt out, and if they do, they are out permanently.

**"What does it cost me?"**

The software is about twenty five dollars a month for the workflow account, plus your phone number and the texts on Twilio, which is pennies. You pay those directly, not to me. I am not marking anything up.

**"Why are you doing this for free?"**

Honestly, because I need businesses actually using it, and because most people find out after a month that they want somebody else to own the upkeep. If that ends up being you, we can talk then. If it does not, you keep it and we are square.

**"What if I'm already on the phone with the customer when it calls me?"**

It rings once and if you do not pick up or do not press one, it just moves on and keeps texting them for you. You never have to do anything to cancel it.

**"Does it replace my receptionist?"**

No, and it does not try to. It does not talk to anyone. It texts, it rings you, and it hands the conversation to you. If you want something that actually answers the phone and holds a conversation, that is a different thing I build.

**"Can I change what it says?"**

Yes, and it is one screen with the four messages on it in plain text. Change the words, save, done. No code, and you do not have to call me to do it.

**"What if it texts somebody at two in the morning?"**

It will not. It holds anything outside eight to eight until morning, on your local time. The only thing it sends at any hour is the immediate reply to somebody who just called or filled out your form thirty seconds earlier, and that one is what they are expecting.

**"How do I know it's working?"**

You will see it working, because you get a text every time a lead comes in. Beyond that there is a log of every message in and out with times. And if the system itself ever breaks, it tells me automatically, so you are not the one who discovers it.

**"Is my customer information safe?"**

It is in your account, not mine. The phone numbers and messages sit in your own workflow account, and your Twilio keys are yours and never leave it. If we part ways I do not take a copy of your customer list with me, because I never had one.

**"What happens if somebody replies STOP?"**

They are marked opted out immediately and permanently. Even if that same person fills out your form again six months later, the system logs the lead and tells you about it, but it will not text them. You can still call them yourself. That is the law and it is also just correct.

**"What if I want to stop using it?"**

You turn it off, or you cancel the account. Your phone number is yours, it goes right back to whatever it was doing before, and your records are still in your own account. There is nothing to claw back and no contract.

## What has actually been proven

This is not a description of something that ought to work. Eleven of thirteen checks were run against the live system on a real phone on Sep 17, with timestamps kept for all of them.

Proven: a lead turns into a text to the customer and an alert to the owner within about a second. The owner's phone rings and pressing one is picked up correctly. The follow up fires at exactly ten minutes. A customer reply stops the sequence, and it stopped with six seconds to spare against a follow up that was already waking up to send. STOP opts a person out, START puts them back, and a lead arriving for an opted out person is refused and logged rather than sent. The same lead arriving twice does not double text anybody. Quiet hours hold a message and schedule it for the morning. When something breaks, the alert text and email go out naming the workflow, the error and the failing node.

Two are still unrun and both need a second phone: a full press one connect where somebody else plays the customer, and a genuine missed call into the business line.

One thing worth knowing because it changes what you tell people. When a customer texts HELP, Twilio answers that itself before the workflow ever sees it, and out of the box its reply is a generic unsubscribe line with no business name in it. That wording is set in Twilio, per business, and it is now a step in the setup guide. The workflow has its own HELP answer too, which is what runs for a shop whose number is not inside a Twilio messaging service.

## One bug worth telling you about

Testing the opted out case found a real fault, not a test artifact. The alert to the owner was sent from the business number, so when the owner's own cell was opted out of that number, Twilio refused the alert and the whole lead errored. In practice that meant any owner who ever texted STOP to their own line while poking around would silently stop receiving lead alerts, and would not find out until they lost a job.

It is fixed. A refused alert no longer stops anything, it gets recorded as failed, and the alert falls back to email automatically even when the setting says text only. That was re-tested and passed. The fix is in the handover file, so nobody you set this up for inherits it.
