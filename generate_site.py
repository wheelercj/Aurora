# External imports.
import os
import re
import shutil
import gh_md_to_html

# Internal imports.
from convert_links import zk_to_md


def main(site_path, zettelkasten_path, website_title, copyright_text, hide_tags):
    if site_path == zettelkasten_path:
        raise ValueError

    site_posts_path = site_path
    # More changes to the code needed to have some of the files at a different location.
    # site_posts_path = site_path + '/posts'

    print('Finding zettels that contain `#published`.')
    zettel_paths = get_zettels_to_publish(zettelkasten_path)
    print(f'Found {len(zettel_paths)} zettels that contain `#published`.')
    
    # Copy zettels to the site folder.
    print(f'Copying the zettels to {site_posts_path}')
    for zettel_path in zettel_paths:
        shutil.copy(zettel_path, site_posts_path)

    # Copy other linked files.
    print('Searching for any attachments that are linked to in the zettels.')
    attachment_paths = get_attachment_paths(zettel_paths)
    print(f'Found {len(attachment_paths)} attachments. Copying to {site_posts_path}')
    for path in attachment_paths:
        shutil.copy(path, site_posts_path)

    # Get the new zettel paths.
    new_zettel_paths = get_zettels_to_publish(site_posts_path)

    attachment_link_pattern = r'(?<=]\()C:[^\n]*?([^\\/\n]+\.(pdf|png))(?=\))'
    n = replace_pattern(attachment_link_pattern, r'\1', new_zettel_paths)
    print(f'Converted {n} absolute file paths to relative file paths.')

    if (hide_tags):
        # Remove all tags.
        tag_pattern = r'#[^#\s\)]+(?=[\n\s])'
        n = replace_pattern(tag_pattern, '', new_zettel_paths)
        print(f'Removed {n} tags.')

    print(f'Converting internal links from the zk to the md format.')
    n = zk_to_md(new_zettel_paths)
    print(f'Converted {n} internal links from the zk to the md format.')

    md_link_pattern = r'(?<=\S)\.md(?=\))'
    n = replace_pattern(md_link_pattern, '.html', new_zettel_paths)
    print(f'Converted {n} internal links from ending with `.md` to ending with `.html`.')

    print('Creating html files from the md files.')
    for zettel_path in new_zettel_paths:
        gh_md_to_html.main(zettel_path, destination=site_path)

    # Get all the new html files.
    html_paths = get_file_paths(site_posts_path, '.html')

    # Fix the images. gh_md_to_html doesn't seem to convert the image links correctly.
    # `.png" src="/images/` must be changed to
    # `.png" src="images/`
    incorrect_link_pattern = r'\.png\" src=\"/images/'
    n = replace_pattern(incorrect_link_pattern, '.png" src="images/', html_paths)
    print(f'Fixed the src path of {n} image links.')

    # Convert any attachment links from the md to the html format (gh_md_to_html doesn't do this).
    md_link_pattern = r'\[(.+)]\((.+)\)'
    n = replace_pattern(md_link_pattern, r'<a href="\2">\1</a>', html_paths)
    print(f'Converted {n} attachment links from the md to the html format.')

    # Move index.html and about.html to the parent folder.
    # parent_html_names = [ 'index.html', 'about.html' ]
    # parent_html_paths = []
    # for parent_name in parent_html_names:
    #     for path in html_paths:
    #         if path.endswith(parent_name):
    #             new_html_path = os.path.join(site_path, parent_name)
    #             os.rename(path, new_html_path)
    #             parent_html_paths += new_html_path
    #             html_paths.remove(path)
    #             print(f'Moved {parent_name} to the parent folder.')

    print('Removing some unwanted CSS that was added by gh_md_to_html.')
    remove_css(html_paths)
    n = replace_pattern(re.escape('<div class="highlight '), '<div class="', html_paths)

    print('Inserting the site header, footer, etc. into each html file.')
    append_html('index.html', f'<br><br><br><br><br><br><br><p style="text-align: center">{copyright_text}</p>')
    insert_template_html(html_paths, website_title)

    # TODO: if I can't use the gh_md_to_html option to not add extra CSS, try overwriting their CSS instead of editing every HTML file like with remove_css except the one line with a style tag.
    # print('Overwriting github-css.css')
    # overwrite_github_css_file(site_path)

    print('Checking for style.css.')
    check_style(site_path)

    print('\nWebsite generation complete.\n')


def append_html(file_name, html):
    with open(file_name, 'a', encoding='utf8') as file:
        file.write(html)


def insert_template_html(html_paths, website_title, folder_name=''):
    for path in html_paths:
        with open(path, 'r', encoding='utf8') as file:
            contents = file.read()
        contents = get_header_html(folder_name, website_title) + contents + get_footer_html()
        with open(path, 'w', encoding='utf8') as file:
            file.write(contents)


def get_header_html(folder, website_title):
    return f'''
        <!DOCTYPE html>

        <html lang="en">
            <head>
                <meta charset="UTF-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <title>{website_title}</title>
                <link rel="stylesheet" type="text/css" href="{folder}style.css" media="screen"/>
                <!-- bootstrap -->
                <link rel="stylesheet" href="https://stackpath.bootstrapcdn.com/bootstrap/4.5.2/css/bootstrap.min.css" integrity="sha384-JcKb8q3iqJ61gNV9KGb8thSsNjpSL0n8PARn9HuZOnIxN0hoP+VmmDGMN5t9UJ0Z" crossorigin="anonymous">
                <!-- bootstrap -->
            </head>
            
            <body>
                <header>
                    <div class="header-contents">
                        <nav>
                            <a href="{folder}index.html" class="title" style="float: left">{website_title}</a>
                            <a href="{folder}about.html" style="float: right">About</a>
                            <p style="float: right">&emsp;&emsp;</p>
                            <a href="{folder}index.html" style="float: right">Home</a>
                            <div style="clear: both"></div>
                        </nav>
                    </div>
                </header>

                <div class="content">'''


def get_footer_html(footer=''):
    return f'''
                </div>

                <footer>
                    {footer}
                </footer>

                <!-- bootstrap -->
                <script src="https://code.jquery.com/jquery-3.5.1.slim.min.js" integrity="sha384-DfXdz2htPH0lsSSs5nCTpuj/zy4C+OGpamoFVy38MVBnE+IbbVYUew+OrCXaRkfj" crossorigin="anonymous"></script>
                <script src="https://cdn.jsdelivr.net/npm/popper.js@1.16.1/dist/umd/popper.min.js" integrity="sha384-9/reFTGAW83EW2RDu2S0VKaIzap3H66lZH81PoYlFhbGU+6BZp6G7niu735Sk7lN" crossorigin="anonymous"></script>
                <script src="https://stackpath.bootstrapcdn.com/bootstrap/4.5.2/js/bootstrap.min.js" integrity="sha384-B4gt1jrGC7Jh4AgTPSdUtOBvfO8shuf57BaghqFfPlYxofvL8/KUEfYiJOMMV+rV" crossorigin="anonymous"></script>
                <!-- bootstrap -->
            </body>
        </html>
    '''


# Returns the total number of replacements.
def replace_pattern(pattern, replacement_string, file_paths, encoding='utf8'):
    total_replaced = 0
    compiled_pattern = re.compile(pattern)
    
    for file_path in file_paths:
        with open(file_path, 'r', encoding=encoding) as file:
            try:
                contents = file.read()
            except UnicodeDecodeError as e:
                print(f'UnicodeDecodeError: {e}')
                raise e

        # Remove any code blocks from contents.
        contents = re.sub(r'`{1,3}(.|\n)*?`{1,3}', '', contents)

        new_contents, n_replaced = compiled_pattern.subn(replacement_string, contents)
        total_replaced += n_replaced
        if n_replaced > 0:
            with open(file_path, 'w', encoding=encoding) as file:
                file.write(new_contents)

    return total_replaced


def get_zettels_to_publish(dir_path):
    zettel_paths = get_file_paths(dir_path, '.md')
    zettels_to_publish = []

    for zettel_path in zettel_paths:
        with open(zettel_path, 'r', encoding='utf8') as zettel:
            try:
                contents = zettel.read()
            except UnicodeDecodeError as e:
                print(f'UnicodeDecodeError in file {zettel_path}')
                raise e
        if '#published' in contents:
            zettels_to_publish.append(zettel_path)

    return zettels_to_publish


def get_file_paths(dir_path, file_extension):
    os.chdir(dir_path)
    dir_list = os.listdir()
    file_paths = []

    for file_name in dir_list:
        if file_name.endswith(file_extension):
            file_name = os.path.abspath(file_name)
            file_paths.append(file_name)

    return file_paths


def get_attachment_paths(zettel_paths):
    attachment_paths = []
    new_attachment_groups = []

    for zettel_path in zettel_paths:
        with open(zettel_path, 'r', encoding='utf8') as zettel:
            contents = zettel.read()
        new_attachment_groups = re.findall(r'(?<=]\()(.+\S\.(pdf|png))(?=\))', contents)
        for group in new_attachment_groups:
            if not group[0].startswith('http'):
                attachment_paths.append(group[0])

    return attachment_paths


def remove_css(html_paths):
    # gh_md_to_html inserts some extra CSS that I don't want.
    # Remove it by deleting some HTML divs and an article.
    strings_to_delete = [
        '<div class="js-gist-file-update-container js-task-list-container file-box">',
        '<div class="Box-body readme blob js-code-block-container p-5 p-xl-6" id="file-docker-image-pull-md-readme" style="margin-left: 40px; margin-right: 40px; margin-top: 20px; margin-bottom: 20px">',
        '<div class="gist-data">',
        '<div class="gist-file">',
        '<article class="markdown-body entry-content container-lg" itemprop="text">',
        '</article>\n</div>\n</div>\n</div>\n</div>',
    ]

    for path in html_paths:
        with open(path, 'r', encoding='utf8') as file:
            contents = file.read()
        for string in strings_to_delete:
            contents = contents.replace(string, '')
        with open(path, 'w', encoding='utf8') as file:
            file.write(contents)


def overwrite_github_css_file(site_path):
    destination = os.path.join(site_path, 'github-markdown-css')
    shutil.copy('C:/Users/chris/Documents/programming/generate site/github-css.css', destination)


def check_style(site_path):
    style_file = os.path.join(site_path, 'style.css')
    if os.path.isfile(style_file):
        print('    style.css already exists. The file will not be changed.')
    else:
        print('    style.css was not found. Providing a new copy.')
        shutil.copy('C:/Users/chris/Documents/programming/generate site/style.css', site_path)
