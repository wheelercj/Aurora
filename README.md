# zk-ssg

This is a static site generator (SSG) for [zettelkastens](https://blog.viktomas.com/posts/slip-box/), which means it converts markdown-based zettelkastens into fully functional HTML and CSS files that can be immediately published as a website. Most of the files in the site folder get overwritten each time this program runs. This program **never** makes any changes to the files in the zettelkasten; it only copies the relevant files to the site folder and works with those copies.

[Here's a site that was built with this program](https://wheelercj.github.io/notes/)

[Comparisons to other methods for publishing a zettelkasten](https://wheelercj.github.io/notes/20210510123255.html)

## Current requirements with this SSG
* The user must know how to run Python code (not necessarily how to code in Python).
* Each of the zettels that are to be published contain the tag `#published`.
* All the zettels that are to be published are in the same folder (the "zettelkasten folder").
* There are zettels named `index.md` and `about.md` (that contain `#published`) in the zettelkasten folder.
* There are not files named `alphabetical-index.md` and/or `chronological-index.md` (that contain `#published`) in the zettelkasten folder.
* The name of each zettel file (except index.md and about.md) is the zettel's 14-digit ID followed by `.md`, e.g. `20201221140928.md`.
* The zettelkasten-style internal links are delimited by double square brackets and are composed of a numerical 14-digit zettel ID, e.g. `[[20201221140928]] note title usually goes here`.
* Almost all of the website's files will end up in the same folder (the site folder) when the site is generated, and many of the files that were already there will be overwritten or deleted (details below).

## What gets overwritten or deleted?
### Short answer
* site files with the same name as zettelkasten files get overwritten
* all markdown files in the site folder that do not get overwritten get deleted
* the program will ask to delete HTML files that were not overwritten

### Detailed answer
When the site files are being generated, all currently existing markdown and HTML files in the site folder that happen to have the same name as any markdown files in the zettelkasten folder that contain the `#published` tag will be overwritten. The program will not overwrite `style.css` and will create it only if it does not already exist. Any markdown files in the site folder that do not get overwritten will be deleted. If there are HTML files in the site folder that do not get overwritten, the program will ask to delete them unless their absolute paths are listed in a file in the site folder named `ssg-ignore.txt`, each file path on its own line.
