# zk-ssg

This is a static site generator (SSG) for [zettelkastens](https://blog.viktomas.com/posts/slip-box/), which means it converts markdown-based zettelkastens into fully functional HTML and CSS files that can be immediately published as a website. Most of the files in the site folder get overwritten each time this program runs. This program **_never_** makes any changes to the files in the zettelkasten; it only copies the relevant files to the site folder and works with those copies.

[Here's a site that was built with this program](https://wheelercj.github.io/notes/)

[Comparisons to other methods for publishing a zettelkasten](https://wheelercj.github.io/notes/posts/20210510123255.html)

## Directions
1. Create a new folder that will hold your website's files.
2. In your zettelkasten folder, create `index.md` and `about.md`.
3. In your zettelkasten folder, add the `#published` tag to each markdown file that you want to publish, including `index.md` and `about.md`.
4. In `index.md`, add other tags for the categories of zettels you want links to be listed for. When zk-ssg makes a copy of `index.md`, in that copy, it will automatically replace each of the file's tags (except `#published`) with links to zettels with that same tag. Any headers, empty lines, etc. you added to the file around the tags will be kept, so you will probably want to spread the tags out.
5. In `generate_site.py`, near the top of the file are some variables you will want to customize. Their defaults are what I use for my site:
```python
zettelkasten_path = 'C:/Users/chris/Documents/zettelkasten'
site_path = 'C:/Users/chris/Documents/site'
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
* Each of the zettels that are to be published contain the tag `#published`.
* All the zettels that are to be published are in the same folder (the "zettelkasten folder").
* There are zettels named `index.md` and `about.md` (that contain `#published`) in the zettelkasten folder.
* There are not files named `alphabetical-index.md` and/or `chronological-index.md` (that contain `#published`) in the zettelkasten folder.
* The name of each zettel file (except index.md and about.md) is the zettel's 14-digit ID followed by `.md`, e.g. `20201221140928.md`.
* The zettelkasten-style internal links are delimited by double square brackets and are composed of a numerical 14-digit zettel ID, e.g. `[[20201221140928]] note title usually goes here`.
* Each time the program runs, many of the files in the site folder will be overwritten or deleted (details below).

## What gets overwritten or deleted?
### Short answer
* **_Nothing_** in the zettelkasten folder is changed in any way.
* Site files with the same name as zettelkasten files get overwritten.
* All markdown files in the site folder's posts folder that do not get overwritten get deleted.
* Specific markdown files in the site folder (outside the posts folder) will get overwritten.
* The program will ask to delete HTML files that were not overwritten.

### Detailed answer
When the site files are being generated, all currently existing markdown and HTML files in the site folder that happen to have the same name as any markdown files in the zettelkasten folder that contain the `#published` tag will be overwritten. The program will not overwrite `style.css` and will create it only if it does not already exist. Any markdown files in the site folder's posts folder that do not get overwritten will be deleted. Specific markdown files in the site folder (outside the posts folder) will get overwritten: `index.md`, `about.md`, `alphabetical-index.md`, and `chronological-index.md`. If there are HTML files in the site folder that do not get overwritten, the program will ask to delete them unless their absolute paths are listed in a file in the site folder named `ssg-ignore.txt`, each file path on its own line.
