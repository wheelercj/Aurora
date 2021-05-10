import generate_site

zettelkasten_path = 'C:/Users/chris/Documents/zettelkasten'
site_path = 'C:/Users/chris/Documents/blog'
website_title = "Chris' notes"
copyright_text = '© 2021 Chris Wheeler'
hide_tags = True  # If true, removes tags from the copied zettels when generating the site.

generate_site.main(site_path, zettelkasten_path, website_title, copyright_text, hide_tags)
