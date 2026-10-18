# TraceGuard demo video: Maya's story (final narration)

**Audience:** hackathon judges. **Story:** Maya, a fictional fraud analyst, works three synthetic cases with TraceGuard.
**Length:** 3:35 · voice-over: Kokoro-82M `af_heart` (AI-generated, credited on the closing card).
Captions show the same text. On-screen actions are anchored to each line's start (see `video/record.py`).
Labels on screen: "Fictional analyst scenario · illustration" on Maya's scenes; "live app · synthetic demo data" on app footage.

## 0:00.0 · 1 · Meet Maya (illustration · fictional analyst scenario)

| Time | Line |
|---|---|
| 0:01.2 | This is Maya. She reviews flagged transactions at a fintech. |
| 0:05.2 | A new alert lands in her queue. Several wallets have sent money into one account. Soon after, a large payment moves out. |
| 0:13.2 | Maya has a question to answer: what happened here, and what does the evidence actually support? |

## 0:20.1 · 2 · Her difficulty (illustration)

| Time | Line |
|---|---|
| 0:20.8 | She starts with the individual records. But the important details sit between them: who paid whom, in what order, and which accounts share a device. |
| 0:29.9 | A connection may matter. It may also have an ordinary explanation. Maya needs to separate what she can observe from what she can only suspect. |

## 0:39.0 · 3 · TraceGuard enters her workflow (illustration)

| Time | Line |
|---|---|
| 0:39.4 | She opens the case in TraceGuard. |

## 0:43.2 · 4 · Follow the evidence: C-1 graph and timeline (live app · synthetic demo data)

| Time | Line |
|---|---|
| 0:43.9 | The graph brings the relationships into view. Maya can follow the transfers in order, inspect the timing, and see the records behind each connection. |
| 0:53.6 | Four wallets send five transfers into A-07: seventeen thousand pesos over thirty minutes. |
| 1:00.5 | Thirty minutes after the final incoming transfer, fifteen thousand five hundred pesos moves onward to A-08. |
| 1:07.8 | One earlier payment, out of A-09, isn't part of this trail. Maya can see why: it happened before the money reached A-09. |
| 1:16.2 | The sequence gives her a specific pattern to investigate. It does not establish anyone's intent. |

## 1:22.5 · 5 · An explanation she can inspect: brief, checks, citation, counterevidence, export (live app, real Gemini)

| Time | Line |
|---|---|
| 1:23.1 | Maya runs the investigation. A fixed workflow executes the graph tools, and Gemini on Vertex AI explains their results. |
| 1:32.6 | Before the brief appears, TraceGuard checks that every cited record exists in the retrieved evidence, that every figure matches the tool output, and that the wording makes no accusation. That makes each claim checkable, not automatically true. |
| 1:48.0 | She reads the brief, then follows a citation back to its supporting records. |
| 1:52.9 | She also checks what complicates the picture: two senders are not linked to the shared device, and the outgoing amount is lower than the incoming total. |

## 2:03.2 · 5b · Maya's review (illustration, text from the real exported brief)

| Time | Line |
|---|---|
| 2:03.8 | She needs those details in her review too, so the next analyst can see both sides. |

## 2:09.4 · 6 · A connection she should question: Maya's next case, C-2 (live app)

| Time | Line |
|---|---|
| 2:10.0 | Her next case looks connected too: three accounts share one device. She runs the investigation and reads what the tools found. |
| 2:18.2 | But this time, no configured rule matches. The available evidence is insufficient. |
| 2:23.8 | Maya can document the connection without turning it into an accusation. Sharing a device alone does not establish wrongdoing. |

## 2:32.1 · 7 · A question she cannot answer: Maya's final case, C-3 follow-up (live app)

| Time | Line |
|---|---|
| 2:32.7 | In her final case, the available trail ends at A-22. She runs the investigation to see what the records cover, and what they leave open. |
| 2:42.5 | Maya asks who owns the account. The dataset cannot tell her. |
| 2:47.2 | TraceGuard states the limit. The owner, the next recipient, and the intent remain unknown. |
| 2:53.4 | So Maya knows what further evidence she would need, rather than accepting an answer the system cannot support. |

## 3:00.1 · 8 · How it works (motion graphic)

| Time | Line |
|---|---|
| 3:00.7 | TraceGuard runs on Cloud Run with Gemini on Vertex AI. Graph tools compute the paths and rule matches. Gemini explains the retrieved evidence. Maya makes the judgment. |

## 3:13.3 · 9 · Resolution: Maya beside the real case brief, then end card (illustration)

| Time | Line |
|---|---|
| 3:13.9 | Maya began with an alert and a question. |
| 3:16.8 | She now has a brief she can explain: the pattern that warrants review, the records supporting it, and the limits of the available evidence. |
| 3:28.7 | TraceGuard. Follow the connections. Keep the judgment human. |
