# Aurora

A static site generator for [zettelkastens](https://blog.viktomas.com/posts/slip-box/).

Create ready-to-publish HTML files from your markdown files by typing `#published` into them and clicking once! [Here's a site that was built with this app](https://wheelercj.github.io/notes/).

## Features

* After setup (instructions below), you can add more pages to your site by simply adding the `#published` tag to your markdown files and running this app again.
* All internal links are converted to HTML regardless of whether they are markdown-style links or zettelkasten-style links.
* If you have zettelkasten-style links with titles mixed into the rest of the page, they will still be converted correctly. For example, if you have a markdown file named `20201221140928.md` and titled `Positive Health`, and one of your other pages contains the text `also see [[20201221140928]] Positive Health for more details`, that will become `also see [Positive Health](20201221140928.md) for more details` (and then that will be converted to HTML). This app can figure out the correct format even though there is no indication of where the title ends.
* The settings menu makes the site's title, colors, and other important options easy to customize. Also, the CSS and the HTML that wraps each page's content can optionally be customized directly. When you generate the site the first time, `style.css`, `header.html`, and `footer.html` will be created and then reused in the future.
* Three index pages listing all the other pages are automatically populated: categorical, alphabetical, and chronological indexes.
* Any broken zettelkasten-style links will be detected.
* Any zettelkasten-style links with outdated titles will be detected.
* Any file attachments in the #published pages will be automatically copied to the site folder.
* This app **_never_** makes any changes to the files in the zettelkasten; it only copies the relevant files to the site folder and works with those copies.
* This app is 100% compatible with [Zettlr](https://www.zettlr.com/)'s default settings for internal links and file names, and is compatible with many other markdown editors as well.

Feature requests, contributions, etc. are welcome!

## Setup

1. Create a new folder that will hold your website's files (the "site folder").
2. In your zettelkasten folder, create `index.md` and `about.md`. `index.md` will later become your site's homepage, and has special options explained in the next steps. You can write whatever you would like in `about.md`.
3. In your zettelkasten folder, add the `#published` tag to each markdown file that you want to publish, including `index.md` and `about.md`. Only files with this tag will be copied to the site folder.
4. In `index.md`, add other tags for the categories of zettels you want links to be listed for. When Aurora makes a copy of `index.md`, in that copy, it will automatically replace each of the tags (except `#published`) with links to zettels that also have that same tag. Any headers, empty lines, etc. you added to the file around the tags will be kept, so you will probably want to spread the tags out. [Here's](https://gist.github.com/wheelercj/f5a974277f2d6096471a88a2c27562f0) an example of how you can write `index.md`.
5. Run the app with one of the commands listed below. Now you're ready to send your new HTML files to your site's host! If you don't have one yet, [GitHub Pages](https://pages.github.com/) is worth considering.

You can run the app with a terminal command:

* on Mac or Linux: `python3 gui.py` (or `python3 cli.py`)
* on Windows: `py gui.py` (or `py cli.py`)

Use `gui.py` to run the app with a graphical user interface, or `cli.py` to run it with a command-line interface. The CLI also has a few options; use the `--help` option to see a list of them. If you will use this app often, you might want to [create a custom terminal command](https://wheelercj.github.io/notes/pages/20220320181252.html).

## What gets overwritten or deleted?

### Short answer

* **_Nothing_** in the zettelkasten folder is changed in any way.
* Site files with the same name as zettelkasten files get overwritten.
* All markdown files in the site folder's pages folder that do not get overwritten get deleted.
* The app will ask to delete HTML files that were not overwritten.
* Some markdown files in the site folder (outside the pages folder) may be overwritten, depending on their names.

### Detailed answer

When the site files are being generated, all currently existing markdown and HTML files in the site folder that happen to have the same name as any markdown files in the zettelkasten folder that contain the `#published` tag will be overwritten. The app will not overwrite `style.css` (except for user settings changes), `header.html`, and `footer.html`, and will create them only if they do not already exist. Any markdown files in the site folder's pages folder that do not get overwritten will be deleted. Specific markdown files in the site folder (outside the pages folder) will get overwritten: `index.md`, `about.md`, `alphabetical-index.md`, and `chronological-index.md`. If there are HTML files in the site folder that do not get overwritten, the app will ask to delete them unless their absolute paths are listed in a file in the site folder named `ssg-ignore.txt`, each file path on its own line.
