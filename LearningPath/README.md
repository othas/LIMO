# Learning path: short manual

## The files

| File | What it is | Edit it? |
|---|---|---|
| `learningpath_source.txt` | The text of the learning path. | **Yes** |
| `page_AI_rules.txt` | The text of the AI rules page. | **Yes** |
| `build_learningpath.py` | The tool that turns the source into the web pages. | No |
| `learningpath/` | The folder with the finished web pages for the students. Generated, so changes made in it are lost at the next build. | No |
| `notes_sections.json` | The list of sections and exercises of the online notes, used to make the links. Generated. | No |
| `LearningPath.txt` | Your original draft. No longer used. | – |

In the folder `learningpath/`: `LearningPath.html` is the overview page (`index.html` is an identical copy, so that the address of the folder itself also works), `LearningPath_ch1.html`, `LearningPath_ch2.html`, ... are the chapters, and `LearningPath_AI_rules.html` is the AI rules page.

## The workflow

1. Edit `learningpath_source.txt` (or `page_AI_rules.txt`) in any text editor.
2. Open a terminal in this folder and run

   ```bash
   python3 build_learningpath.py
   ```

3. Open `learningpath/LearningPath.html` in a browser to check the result.
4. Publish the folder `learningpath` (see below).

If the online course notes have changed (new or renamed sections or exercises), run this instead, so that the list of sections is read again from https://othas.github.io/LIMO/ (needs an internet connection):

```bash
python3 build_learningpath.py --refresh
```

## Publishing on GitHub, next to the course notes

The pages go into the same repository as the course notes (`othas/LIMO`), in a folder `learningpath`.

1. Go to https://github.com/othas/LIMO and sign in.
2. Click **Add file**, then **Upload files**.
3. Drag the whole folder `learningpath` from Finder into the upload area. Drag the folder itself, not the files in it: GitHub then keeps the folder.
4. Click **Commit changes**.
5. After a minute or two the learning path is at https://othas.github.io/LIMO/learningpath/

To update later, do exactly the same; GitHub replaces the files that changed. In Blackboard you need a single web link to that address, set to open in a new window. Uploading a new version of the course notes (`index.html`) does not touch the folder `learningpath`, and the other way round.

## How to write the source file

Every item is a paragraph. **Paragraphs are separated by an empty line**; within an item there are no empty lines.

### Chapters and blocks

```
# Chapter 2: Simple Linear Regression Analysis

## Estimating the parameters
> Goal: estimate the parameters by least squares.
```

`#` starts a chapter, `##` starts a block of steps, and the optional `>` line gives the goal of the block.

Every chapter becomes its own page. The number in "Chapter 2" gives the file name (`LearningPath_ch2.html`), so keep "Chapter N" in the title.

### Steps

The first line says what kind of step it is; the lines below it are the explanation for the student (optional).

```
WATCH 19 min | 2.2
Here you learn how the parameters can be estimated...

READ 2.8
There is no video recording available...

DO exercise-blood-pressure
Make the exercise yourself...

NOTE
Section 2.3 is about the properties of...

AI AI as explainer
Ask the AI assistant to explain...

CHECK
You can move on when you can answer these questions.
- Which criterion is minimised by the least squares estimator?
- Did you need the normality assumption?
```

| Step | First line | Result on the page |
|---|---|---|
| `WATCH` | `WATCH length \| target \| url \| from \| to` | "Watch the video (*length*) on *Section …*" |
| `READ` | `READ target, target, ...` | "Read *Section …*" |
| `DO` | `DO target, target, ...` | "Make *Exercise: …*" |
| `NOTE` | `NOTE` | A piece of text without a link |
| `AI` | `AI short title` | An AI step with that title |
| `CHECK` | `CHECK` | Self-check questions; each question on a line starting with `- ` |

Put `OPTIONAL` in front of a step to mark it as optional: `OPTIONAL READ 2.3.4`.

### Targets: links to the course notes

A target is either

- a **section number** of the notes, e.g. `2.3.1`, or
- an **anchor**, for places without a number such as exercises and examples, e.g. `exercise-blood-pressure`.

To find an anchor: in the online notes, hover over the heading and click the link symbol that appears next to it. The address bar then ends with `#exercise-blood-pressure`; the part after `#` is the anchor. All anchors are also listed in `notes_sections.json`.

### Videos

For `WATCH`, only the label and the target are required. The rest can be added later:

```
WATCH 19 min | 2.2 | 1_lav8sk6t
```

The third field is the Kaltura entry id of the clip: the code after `entry_id=` in the embed code that Kaltura gives for the clip (Share, then Embed). The tool turns it into a link that opens the player in a new tab. A full web address works there too. The fields `from` and `to` (times such as `12:40`) are optional and only needed if a step should point to a part of a longer video.

### Boxes at the start and end of a chapter

```
BEFORE
This chapter builds on the following.
- Vectors and matrices.
- Basic R.

AFTER
- formulate the simple linear regression model;
- fit the model in R.
```

`BEFORE` gives the box "Before you start" (place it directly under the chapter title), `AFTER` gives the box "After this chapter you can" (place it at the end of the chapter).

### Extra pages, such as the AI rules

A file named `page_<name>.txt` in this folder becomes its own page `learningpath/LearningPath_<name>.html`, listed at the top of the overview page, above the chapters. The AI rules are in `page_AI_rules.txt`. Such a file has a `# title`, `## headings`, paragraphs separated by an empty line, and lists with lines starting with `- `.

Anywhere in the source you can link to a page with `[the rules on AI](LearningPath_AI_rules.html)`, or to any web address in the same way, and make text bold with `**bold**`.

### Maths and comments

- Maths goes between dollar signs, in LaTeX: `$\hat\beta_1$`, `$E(Y \mid x)$`. So do not use a dollar sign for anything else.
- A line starting with `//` is a comment for yourself and does not appear on the page.

## When something goes wrong

- **`Unknown section or anchor in the notes: '...'`**: the target does not exist in the notes. Check the spelling, or run with `--refresh` if the notes were changed recently.
- **`Cannot read this part of the source file:`** followed by a piece of text: that paragraph does not start with one of the keywords above, or it comes before the first `##` block. Often an empty line has slipped into the middle of a step.
- **Formulas show as plain text**: the page loads MathJax from the internet, so formulas need an internet connection. Also check that every `$` has a partner.

## Good to know

- The ticks of the students are stored in their own browser, on their own device. Nobody else sees them.
- You can add, remove or move steps during the semester without disturbing the ticks students already made. A tick belongs to the target of its step (the section, exercise or AI title), so only when you change the target of a step, or the title of an AI step or of a block, do the ticks of that step start again as not done.
- The tool needs only Python 3; no extra packages.
