# Contributing to Cybersecurity Roadmap 2026

Thanks for wanting to improve this roadmap. It is maintained in the open, and the most useful contributions are small and specific: a better free resource, a fixed link, or an exercise that finally explains something clearly.

## The rule that matters most

**Every suggestion must be true and checkable.** This roadmap deliberately avoids statistics, prices, pass rates and outcome promises it cannot verify today. If your suggestion adds a number, link the source for that number.

## Suggesting a resource

Open an issue with the [suggest a resource](https://github.com/tariqsumatri82/cybersecurity-roadmap-2026/issues/new?template=suggest-a-resource.md) template. A suggestion is accepted when it meets all of these:

- **Free, or free enough.** The resource is free, or its free tier covers the exercise it supports. Paid-only courses are not added.
- **You have actually used it.** Say what you did with it in one sentence — "I ran the four Nmap exercises against my own lab" is enough; a marketing summary is not.
- **It loads today.** Paste the link as it is, without tracking parameters. Every URL in the README is checked with `tools/check_links.py`.
- **It fills a named gap.** Say which phase it belongs to and which checkpoint item or exercise it improves. Resources that duplicate something already listed are declined, however good they are.
- **It is likely to stay up.** Official vendor documentation, established open projects, or platforms that have been running for years and do not expire.
- **No undisclosed self-promotion, no affiliate links, no referral codes.** If it is your own project, say so and make the case like anyone else.
- **No unverifiable claims.** No "guaranteed job", no "X% of learners hired", no salary figures, no exam prices that will be stale in a month.

## Suggesting a new phase or a better exercise

Phases are deliberately broad and ordered. To change the structure, explain in the issue: what the current sequence gets wrong, what you would move or add, and what the learner can do afterwards that they cannot do now. Structural changes are the slowest to accept, because every phase after the change has to stay coherent.

## Fixing a broken link

Open an issue with the [broken link](https://github.com/tariqsumatri82/cybersecurity-roadmap-2026/issues/new?template=broken-link.md) template, or send a pull request. Include the URL, where it appears, and what you see instead of the page.

## Sending a pull request

1. Fork the repository and work on a branch.
2. Keep the phase structure: **Why it matters**, **What you will learn**, **Hands-on exercises**, **Free resources**, **Checkpoint**. If you add an exercise, say exactly what to run and what to look for in the output.
3. Run the link checker before you push:

   ```bash
   python3 tools/check_links.py
   ```

   It must report zero dead links. Links that a site blocks from automated clients are reported separately — check those by hand.
4. Keep the English plain and direct. No hype, no promises, no invented numbers.
5. Say in the pull request what you changed and how you verified it.

## Review and timing

This is a personal project, maintained alongside other work, so there is no guaranteed turnaround. Straightforward fixes usually land quickly; structural proposals may sit until there is time to think them through. Silence is not a rejection — a polite nudge on the issue is fine.

## Licence

By contributing you agree that your contribution is licensed under [CC BY 4.0](LICENSE), the same licence as the rest of the repository.
