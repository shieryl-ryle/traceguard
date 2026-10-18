# TraceGuard — Pre-submission checklist

**Internal submit target:** Sun Oct 18, 10:00 PM Manila · **Portal closes:** Mon Oct 19, 2:29 AM Manila
**Live app:** https://traceguard-343683630064.asia-southeast1.run.app
**Repo:** https://github.com/shieryl-ryle/traceguard
**Feature freeze:** now. Only fixes for broken behaviour after this point; every deploy gets the checks in step 1 again.

Tick each box and write the time. If a step fails, stop and fix it before moving on.

---

## 1. App is ready for judges (Dzelle, by 12 PM)
- [ ] Incognito window (no Google login) opens the live URL in under 10 s; queue shows C-1, C-2, C-3 and the "Synthetic data" badge
- [ ] C-1 → Run AI investigation: "Live AI output", Verified panel, both rule flags "Pattern warrants review", counterevidence quotes both contrasts
- [ ] Click `RULE-FWD-01`: graph highlights beside the brief; cited records listed
- [ ] Export downloads `traceguard-C-1-brief.md`
- [ ] Follow-up "Why is A-08 relevant?" answered with citations; "Who owns A-22?" shows "Not answerable from this data"
- [ ] C-2: no rule matches, counterevidence explains why · C-3: forwarding flag, unknown past A-22
- [ ] Phone check (390 px): nothing cut off or unclickable (cosmetic issues: note only, don't fix)
- [ ] `python -m pytest -m "not live"` → 168 passed · `python -m pytest -m live` → passed

## 2. Demo video (Shieryl, 12 PM – 5 PM)
- [ ] One dry run against the live URL with `submission/video-script.md` open; time it (≤ 4:00)
- [ ] Before recording: run each case once to warm up; browser zoom 110%; notifications off; incognito
- [ ] Record: problem → C-1 graph and trace → AI brief, Verified panel, citation click, follow-up refusal → C-2 and C-3 → architecture → close
- [ ] Only live output on screen; no accusatory words in narration ("pattern warrants review", never "fraudster" or a percentage)
- [ ] Upload (YouTube unlisted or as the rules require); **open the link in incognito** to confirm it plays publicly
- [x] Video length 3:56, within the portal's 3–4 minute range

## 3. Proposal deck (Shieryl, by 7 PM)
- [x] Video link on slide 13 (Drive file link, opens without sign-in; label "3–4 Minutes")
- [ ] Upload `submission/TraceGuard-proposal.pptx` to Drive → Open with Google Slides (or *File → Import slides* into the template)
- [ ] Skim all 15 slides in Google Slides: fonts render, nothing overflows, three links on slide 13 are clickable
- [ ] Re-check slide 5 (revision, IAM) and slide 11 (timings, test count) still match the live app
- [ ] *File → Download → PDF* from Google Slides; open the PDF and skim it

## 4. Repository (Shieryl + Dzelle, by 8 PM)
- [ ] Merge PR #5 (deck, script, screenshots, this checklist) into `main`
- [ ] No open PRs left that change the app
- [ ] Dzelle agrees to the commit-author emails becoming public (or both accept; rewriting history is not worth the risk now)
- [ ] Settings → General → Danger zone → **Change visibility → Public**
- [ ] Open the repo in an incognito window: README loads, `docs/` and `submission/` visible
- [ ] Do **not** deploy again after this unless something is broken

## 5. Submission form (Shieryl, 9 – 10 PM)
- [ ] Category field: pick BFSI if offered; otherwise the closest option and name "BFSI: Intelligent Risk, Fraud & Financial Experiences" in the description (Q1)
- [ ] Team name Chilli · leader Shieryl Tendilla · both members listed
- [ ] Links: public GitHub repo · public video · live app URL; open each from the form in incognito
- [ ] Upload the proposal PDF
- [ ] Check every other module on the portal for its own countdown (proposal, video)
- [ ] **Submit by 10 PM**; screenshot the confirmation page

## 6. After submitting (until results)
- [ ] Leave the Cloud Run service running and **don't redeploy**: judges may open it at any time
- [ ] Dzelle keeps an eye on budget alerts; if quota errors appear, check Diagnostics → Call Gemini and Cloud Run logs
- [ ] After results: delete the `traceguard-2026` project (Dzelle) to stop all charges

---

**If something breaks close to the deadline**
- Gemini errors on the live URL → Diagnostics → Call Gemini; check `gcloud logging read` for the Cloud Run service. The graph and timeline still work, so the demo can show them while you investigate.
- A deploy fails → the previous revision keeps serving; don't roll forward under time pressure.
- The video upload is slow → submit the form with the other links first if the portal allows editing, then add the video.
