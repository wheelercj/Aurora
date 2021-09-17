import generate_site

zettelkasten_path = 'C:/Users/chris/Documents/zettelkasten'
site_path = 'C:/Users/chris/Documents/blog'
site_title = "Chris' notes"
copyright_text = '© 2021 Chris Wheeler'
hide_tags = True   # If true, tags will be removed from the copied 
        ## zettels when generating the site.
append_index = True  # If true, a list of all zettels will be
        ## displayed at the end of index.md.

generate_site.main(site_path,
                   zettelkasten_path,
                   site_title,
                   copyright_text,
                   hide_tags,
                   append_index)
