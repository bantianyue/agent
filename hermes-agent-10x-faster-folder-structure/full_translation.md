# I Made My Hermes Agent 10x Faster Without Changing the Model

By @wandermist

---

Last week I read about an AI that designed a vaccine fighting coronaviruses we haven’t even encountered yet (ScienceDaily). Cambridge ran the first human trial, and 39 volunteers received the antigen.

It’s crazy to think that an algorithm analyzed the entire genetic family of a virus and engineered protection against members still circulating in animals and waiting to jump. But when I ask it to fetch my latest brief from a list of docs, it can spend nearly two minutes opening the wrong files in my vault just to show me a brief from three months ago.

And I know Cambridge uses a custom trained AI, but what I want to show you is that the gap between what AI can do and what a setup lets it do is what makes or breaks your workflow and productivity.

I never built scaffolding on purpose, until recently. It piled up around the agent by accident, folder by folder, until the agent lost its way inside a mess I shaped for myself.

So I spent a day timing every failure, and a pattern showed up. In this edition I show you why your agent keeps tripping over the easy stuff while the world calls it a genius, and the fix that puts it back on your side.

In this piece:

- Folder structure failed my agent because my folders were organized for how I think, not for how an agent navigates

- One index file at the root of every major folder turned slow searches into thirty-second reads

- The invisible scaffolding around your agent matters more than the agent’s own capability, and here’s how to build it

- A diagnostic test you can run in five minutes to see whether your folder structure is the real problem

## The Structure Your Agent Can’t See

I organized my vault the way most people do. Articles, research, assets, strategy docs, each got their own folder. That structure felt clean because I think in content types. Folders map to my categories and I never think about where to look. Drafts are articles, notes are research, the filing system runs on autopilot.

But an agent doesn’t think in categories. When I ask Hermes to plan a product launch, the task pulls from strategy notes, brand guidelines, and previous launches scattered across different folders.

Those pieces of context live in different places in my content-type structure. My agent has to search everywhere every time, without knowing which draft is current versus which one is archived, or which research note is from this month versus from six months ago.

Content-type organization works perfectly for humans. You’ve spent your whole life filing things under categories, and your brain does the cross-referencing automatically. It’s only natural to expect AI to work the same, when in fact an agent has to do that cross-referencing manually, and that’s where the structure breaks down.

> The structure around your agent does more work than the agent’s own capability.

Once I saw the pattern, the cause was obvious: I had built my vault for a human brain that remembers where things live, then handed it to an agent that has to search from scratch every time, and that exposed the real issue underneath the folder mess.

A searcher needs a map, because without one the agent is walking through the dark and treating every file like it might be the answer.

## What Capability Wastes On

Hermes kept opening a bunch of files before landing on the right one, or grabbing an archived version when the current file was somewhere else. Worse, it would ask which file to use when the answer should have been obvious from context. This happened with every model I used, including Opus, GPT 5.5, Qwen, and GLM.

The pattern kept repeating, and I was stuck watching the same slow searches play out across task after task.

Even though my agent was capable enough to find things, the folder structure had become the main bottleneck before it ever reached the actual work.

I hit the breaking point the day I timed the failures. I tracked how many files Hermes opened before it reached the right one, and how long it took to get there. Five common tasks looked like this before I changed anything.

Before I changed anything:

- Find the current article brief: 7 files opened, 2:00 to the correct file;

- Find brand color definitions: 5 files opened, it took 1:12;

- Look up the article queue for planning: 4 files opened, it took 0:48;

- Find previous articles on the same topic: 6 files opened, it took 1:36;

- Pull promotion strategy for a launch: 3 files opened, it took 0:34.

Every task crossed multiple folders. Most of them opened archived versions before finding the active ones. My agent was burning capability on navigation instead of doing its job. One launch plan needed three files that lived in three different folders, and I watched it make three wrong attempts before landing on the right ones.

> An agent that writes articles, codes, and plans shouldn’t be spending most of its time looking for things.

## The Smallest Cage That Works

One folder per concern, numbered for order, with an INDEX.md at the root that maps everything. That’s the whole fix, and the details live in three rules that work together.

INDEX.md at the root of each major folder is a map. It lists every subfolder and canonical file, plus where my agent should start. My agent reads this first and knows what’s inside before touching anything else. Think of it as a soft approval gate where the agent isn’t allowed to start work until it knows what it’s working with.

My brand folder structure looks like this after the reorganization.

This structure organizes by concern instead of content type. Each concern gets its own folder, so brand work stays with brand work and strategy stays with strategy. My agent doesn’t cross boundaries looking for something that doesn’t belong there.

Numbers on folders make reading order explicit instead of relying on alphabetical sorting. 01. Brand System gets read before 02. Editorial Strategy. My agent doesn’t guess. Numbers inside folders do the same thing for files, so my agent knows 01. Articles is the starting point before 02. Previous Articles.

I lead folder names with a number because it’s easier for me to remember as well.

This is how my full $30 Hermes stack stays easy to move across dozens of folders without my agent ever getting lost.

Archived stuff lives in 06.Archived, where old briefs and retired plans go to wait. My agent knows not to look there unless I specifically ask for historical context. That separation is what keeps the active folders clean and the searches fast.

> Once my agent was told not to cross that boundary by default, every task inside the active folders ran faster.

My INDEX.md looks like this.

INDEX.md went through three versions. My first version listed every single file inside the brand folder and ran to forty lines. It was technically complete but my agent had to parse it every time and the length was its own overhead. My second version was too short, around fifteen lines, and my agent still asked questions I hadn’t answered. This third version lists only subfolders and canonical files, with a short “Where To Go” section that tells my agent its starting points.

When I ask my agent to pull promotion strategy for a launch, it reads 05.Brand/INDEX.md, opens 03.Promotion/01. Promotion Strategy.md, and gets to work. Timing after the reorganization looks like this.

After the reorganization:

- Find the current article brief: 1 file opened, 0:10

- Find brand color definitions: 3 files opened, 0:22

- Look up the article queue for planning: 1 file opened, 0:10

- Find previous articles on the same topic: 2 files opened, 0:18

- Pull promotion strategy for a launch: 1 file opened, 0:12

The slowest task dropped from 2 minutes to 26 seconds, and the fastest runs landed around 10 seconds. My agent opens the INDEX.md, follows the starting point it needs, and gets to work without wandering. No capability changed on my agent’s side. Folder structure stopped wasting most of it before the task even started.

> Folder structure is a cage I built that constrains how my agent moves without constraining what my agent can do. Inside the cage, my agent runs freely. Without it, Hermes tends to wander off and I have to waste my time pointing it at the right file.

Moving to Hermes let me build that kind of system across files, providers, and memory all at once, and the INDEX.md pattern is the smallest piece that made the biggest difference day-to-day.

## Every Cage Has a Lock

My first mistake was adding INDEX.md to every subfolder. Too many maps means my agent spends its time reading indexes instead of doing work. I keep INDEX.md only at the root of major folders like Brand and Editorial Strategy, where there are enough subfolders to need a map. Inside a small subfolder with four or five files, Hermes navigates directly without any map at all.

Keep in mind that numbering gets tedious when you add new folders. I’ve got to decide where a new folder fits in the sequence, and sometimes I append it at the end instead of renumbering everything. That’s fine. Numbers don’t have to be perfect as long as they’re directional. Perfectly ordered folders aren’t the goal, and treating them as one turns a practical fix into a cosmetic project.

A bigger mistake is building structure before your agent shows any confusion. Most people over-engineer their agent setup because they think it needs proper infrastructure.

My current rule follows the same principle behind choosing MCPs versus CLIs versus your own tool. It uses the smallest interface that gets the job done. Add structure only when your agent gets lost, and add only enough structure to fix that specific problem.

Another failure I ran into was nesting structure inside structure. I added subfolders inside subfolders to make everything perfectly categorized, which turned a two-level hierarchy into a five-level one. My agent then had to read multiple INDEX files and parse multiple numbering sequences to reach a single file. I collapsed those extra levels back into flat subfolders and navigation sped up again.

> Depth is the enemy of fast file lookup, and most reorganizations add depth thinking it’s precision.

## Measure Before You Reorganize

Before touching a single folder, run this test on three real tasks your agent handles most often. Time each one, and note how many files it opens before finding the right one. Track how often it picks the wrong file or stops to ask you which one to use.

Any task that takes your agent more than thirty seconds or opens three or more wrong files points to a folder behind that task that’s broken.

Pick the one failure that happens most often. Open that folder and write an INDEX.md that lists every subfolder and important file, plus where your agent should start. Save it. Run the same task again.

If your agent finds the right file in under thirty seconds, the fix worked and you now know the pattern. Apply it to the next broken folder. If it still fails, the problem is likely numbering or one-concern-per-folder, and those are the next two things to fix.

> Start with the one folder that wastes the most time, fix it, and move to the next only when you’re ready.

## Where the Bars Still Bends

Archived content still gets referenced sometimes when I need an old brief for context. My agent has to know to look in 06.Archived instead of the active folders, and I mention this in the INDEX.md so it knows where historical material lives. Without that note my agent assumes archived content doesn’t exist.

Also, Obsidian Sync creates occasional problems when it does not catch up cleanly across devices. If I update a file on my laptop but the older version is still sitting on my VPS, Hermes loads the VPS copy and treats it like the current source of truth. That is a sync problem more than a folder-structure problem, but it shows up inside the folder system because the agent only sees the files in front of it.

Numbering breaks down when you’ve got so many folders that the sequence becomes meaningless. Past ten or twelve numbered items at one level, the numbers start being arbitrary.

I try to keep major categories below that threshold and nest deeper structure inside instead of expanding the top level.

Renaming is another source of friction. When I reorganize I sometimes rename folders to better match their purpose, and any INDEX.md reference to the old name breaks until I update it. I now try to set folder names once and leave them alone, because a slightly awkward name is cheaper than a broken reference.

This structure works best for content-heavy workflows and planning-heavy ones. Pure code or data-heavy setups might need different organization principles entirely, and the INDEX.md pattern doesn’t solve every navigation problem.

Everything I’ve written about in this article traces back to one instinct. Own the layer that matters. I built my stack so no company controls my tools. I built my vault so no mess controls my agent. Same principle from providers to folders to whatever comes next.

Capability is cheap when the scaffolding around it is broken. Build the scaffolding, and the capability takes care of itself. One index file and a few numbers in front of your folder names is the difference between an agent that wanders and an agent that works.

If this was useful - follow @wandermist for more content like this!

---
