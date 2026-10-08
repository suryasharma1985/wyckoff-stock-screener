**Subject: Update on our stock-screener research — honest findings + decision we need to make together**

Hey Mity,

I wanted to give you a full, honest rundown of where our Wyckoff stock-screener research stands, because we've reached a real decision point and want your input before we go further. This is a long one, but it matters — and I've kept it in plain English.

**What the project is**
We built a tool that scans ~1,900 Indian (NSE) stocks and tries to flag the moments when a stock's trend might be turning up. It's based on the Wyckoff idea that you can read a stock's behavior from its price and volume. It looks for specific "events":
- **Spring** – price dips below a support level then snaps back (temporary shakeout).
- **Selling Climax (SC)** – a huge, panicky drop on massive volume (sellers exhausted).
- **Sign of Strength (SOS)** – a strong breakout on heavy volume (buyers in control).
- And a few others like LPS and UTAD.

The idea: spot these patterns and buy the stocks they point to.

**What we originally thought**
Our first big historical backtest showed this thing making money — around +8% per trade over a 3-month hold in a strong period, and +3.7% over the full test. It looked promising. We got excited.

**But then we asked the hard question: is this real skill, or is it just luck?**
That's the part that matters. When you test a strategy you have to check whether it actually *beats picking stocks at random*. So we ran a proper statistical test. Here's what it found, and I'll be straight with you because this is important:

- **Spring and Selling Climax — our two main events — do NOT beat random selection over a 3-month period.** Statistically, picking those stocks was no better than picking the same number of stocks blindly. That's a big deal, because our whole strategy was built on these two.
- **The ONE event that genuinely beats random is SOS (Sign of Strength)** — the breakout-on-volume signal. It's the only one that held up as truly better-than-random.
- **LPS turned out to be a negative signal** — stocks flagged by it actually did *worse* than average. Right now our screener treats LPS as a good thing, which the data says is backwards.
- **The +8% illusion mostly came from the market going up** (Indian stocks rallied hard in that period) and from a handful of huge winners that were likely data glitches (splits/bonuses), not genuine trades.

**The tests I actually ran to get here** (in the order I did them):

1. **Full-history backtest (Phase 17)** – I ran the screener across all ~1,900 stocks over June 2023 – Aug 2026, at monthly checkpoints. That's when I got the impressive-looking number (+3.7% average net per trade over 3 months, ~68,000 signals). This is what got us hopeful in the first place.

2. **Pre-discovery backtest (Phase 22)** – To check it wasn't a fluke of that one period, I ran the *same* strategy on the 12 months *before* the main test (June 2022 – May 2023). It held up — even stronger (+8% per 3-month trade). But I noticed two problems: (a) I had to drop 403 of the ~1,900 stocks because they didn't exist yet, and (b) only stocks that still exist today were included. That's "survivorship bias" — the backtest is blind to the stocks that went bust and disappeared, so it looks better than reality.

3. **Diagnostic breakdown (Phase 23)** – This was the turning point. I broke the results down event-by-event and ran a *statistical* (permutation) test that answers "is this event better than randomly picking stocks in the same month?" This is where I first saw the red flags, but I also made a mistake here: I applied the correction for testing many things at once incorrectly, and the summary labeled everything "supported." When I looked closer at the raw numbers, they didn't support that.

4. **Honest re-check (Phase 27)** – I re-ran that statistical test properly, with the full multi-testing correction applied correctly. This is the definitive answer:
   - Only **SOS** is genuinely better-than-random (the one positive, statistically solid signal).
   - **Spring and SC** are NOT better than random at the 3-month horizon.
   - **LPS** is significantly WORSE than random.
   Everything I'm telling you now rests on this corrected test.

5. **Some extra stress-tests I ran along the way** (these all confirmed the warning signs):
   - I pulled out the top 5% biggest winners — and the edge nearly *vanished*. Roughly 80% of the profit came from a tiny handful of huge winners. That's not a steady edge; that's a lottery ticket.
   - I checked a bunch of those huge winners and ~56 of the top 100 look like **data errors** (stock splits/bonuses mis-recorded), not real 1,000% runs.
   - I compared two versions of the "market filter." The number you've heard (+8%) came from the LOOSER setting; the actual tradeable version is stricter and weaker (+7.5%). So the headline was flattering us.
   - I checked how much of the profit survives if the market *isn't* going up — and in sideways markets the strategy lost money. Strongly suggests the "edge" was mostly just being long during a bull run.

So the biggest lesson: **our first exciting backtest number was real, but it was mostly market beta (being long in a bull market) + survivorship bias (ignoring dead stocks) + a few lucky data-error winners — NOT a repeatable skill.** When you properly correct for all that, only the SOS signal stands up.

**Another thing we found**
Our validation was also measuring the *wrong* setting. We have two versions of the "market filter" logic. The historical +8% number came from the looser version, but the version we'd actually trade is stricter and weaker (about +7.5%). So even our own test was flattering us.

**So where does that leave us?**
The honest summary:
- The software itself is solid and trustworthy — it doesn't cheat or leak future info. That part is genuinely good, and most people never get that.
- The **event selection** is the problem. The two events we bet on don't actually outperform random. The one that does (SOS) isn't even in our strategy.
- We have NOT proven we can make money with this yet. Real money is still off the table.

**The decision I want your input on**
I think the most promising path is to **pivot our research toward SOS as the main signal**, and **stop treating LPS as a bullish signal** (the data says it's actually bad). But that's a change to the strategy, so I don't want to just silently switch it. I want us to design a proper test for SOS first, then decide together.

So my questions for you:
1. Do you agree we should investigate SOS as the primary event?
2. Should we remove LPS from the "good signals" list given it's showing negative?
3. Or do you want to step back and reconsider whether the whole approach is worth pursuing?

I've put everything in a file called `PROGRESS.md` in the project folder — it's our shared memory, updated after every step, so either of us (or an AI) can pick up where we left off.

No rush — this is exactly the point where we decide together whether to keep going and in which direction. Let me know your thoughts.

Best,
[Your name]
