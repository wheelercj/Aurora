# zk-ssg

This is a static site generator (SSG) for [zettelkastens](https://blog.viktomas.com/posts/slip-box/), which means it converts markdown-based zettelkastens into fully functional HTML and CSS files that can be immediately published as a website. Most of the files in the site folder get overwritten each time this program runs. This program **_never_** makes any changes to the files in the zettelkasten; it only copies the relevant files to the site folder and works with those copies.

[Here's a site that was built with this program](https://wheelercj.github.io/notes/)

[Comparisons to other methods for publishing a zettelkasten](https://wheelercj.github.io/notes/20210510123255.html)

## Directions
1. Create a new folder that will hold your website's files.
2. In your zettelkasten folder, add the `#published` tag to each markdown file that you want to publish.
3. In your zettelkasten folder, create `index.md`.
4. In `index.md`, add the `#published` tag and other tags for the categories of zettels you want links to be listed for. When zk-ssg makes a copy of `index.md`, in that copy, it will automatically replace each of the file's tags (except `#published`) with links to zettels with that same tag. Any headers, empty lines, etc. around the tags you added to the file will be kept, so you will probably want to spread the tags out.
5. In `generate_site.py`, near the top of the file are some variables you will want to customize. Their defaults are what I use for my site:
```python
zettelkasten_path = 'C:/Users/chris/Documents/zettelkasten'
site_path = 'C:/Users/chris/Documents/blog'
site_title = "Chris' notes"
copyright_text = '© 2021 Chris Wheeler'
hide_tags = True   # If true, tags will be removed from the copied 
    # zettels when generating the site.
hide_chrono_index_dates = True  # If true, file creation dates will
    # not be shown in the chronological index.
```
6. You might also want to customize `style.css`, such as to change the site's colors.
7. Run this program.
8. Send your new HTML files to your website's hosting provider. If you don't have one yet, [GitHub Pages](https://pages.github.com/) is worth considering.

## Limitations
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
* NOTHING in the zettelkasten folder is changed in any way
* site files with the same name as zettelkasten files get overwritten
* all markdown files in the site folder that do not get overwritten get deleted
* the program will ask to delete HTML files that were not overwritten

### Detailed answer
When the site files are being generated, all currently existing markdown and HTML files in the site folder that happen to have the same name as any markdown files in the zettelkasten folder that contain the `#published` tag will be overwritten. The program will not overwrite `style.css` and will create it only if it does not already exist. Any markdown files in the site folder that do not get overwritten will be deleted. If there are HTML files in the site folder that do not get overwritten, the program will ask to delete them unless their absolute paths are listed in a file in the site folder named `ssg-ignore.txt`, each file path on its own line.
