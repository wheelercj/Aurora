# zk_ssg

This is a static site generator (SSG) for [zettelkastens](https://blog.viktomas.com/posts/slip-box/), which means it converts markdown-based zettelkastens into fully functional HTML and CSS files that can be immediately published as a website. Most of the files in the site folder get overwritten each time this program runs. This program never edits any files in the zettelkasten; it only copies the relevant files to the site folder.

[Comparisons to other methods for publishing a zettelkasten](https://wheelercj.github.io/notes/20210510123255.html)

## Requirements with this SSG (some/all of these are temporary)
* The user must know how to run Python code (not necessarily how to code in Python).
* Each of the zettels that are to be published contain the string `#published`.
* All the zettels that are to be published are in the same folder (the "zettelkasten folder").
* There are either zettels named `index.md` and `about.md` that contain `#published` in the zettelkasten folder, or HTML files named `index.html` and `about.html` in the site folder.
* The zettelkasten-style internal links are delimited by double square brackets and are composed of a numerical 14-digit zettel ID, e.g. `[[20201221140928]] note title usually goes here`.
* The name of each zettel file (except index.md and about.md) is the zettel's 14-digit ID followed by `.md`, e.g. `20201221140928.md`.
* Almost all of the website's files will end up in the same folder (the site folder) when the site is generated, and many of the files that were already there will be overwritten or deleted (details below).
* The site generation process requires an internet connection and has some limits on how many times it can be used by each person each hour. This limit comes from GitHub's REST API.

## What gets overwritten or deleted?
### Short answer
* site files with the same name as zettelkasten files get overwritten
* all markdown files in the site folder that do not get overwritten get deleted
* the program will ask to delete HTML files that were not overwritten

### Detailed answer
When the site files are being generated, all currently existing markdown and HTML files in the site folder that happen to have the same name as any markdown files in the zettelkasten folder that contain the `#published` tag will be overwritten. Also, `github-css.css` will get overwritten on each site generation. The program will not overwrite `style.css` and will create it only if it does not already exist. Any markdown files in the site folder that do not get overwritten will be deleted. If there are HTML files in the site folder that do not get overwritten, the the program will ask to delete them unless their names (not the entire paths) are listed in a file in the site folder named `custom-HTML-file-names.txt`, each file name on its own line.

## Implementation details
This program uses [phseiff's gh-md-to-html module](https://github.com/phseiff/github-flavored-markdown-to-html).
