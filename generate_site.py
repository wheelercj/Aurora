# External imports.
import os
import re
import shutil
import gh_md_to_html
import datetime

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

    # Get a list of any HTML files that already exist, to compare later.
    old_html_paths = get_file_paths(site_posts_path, '.html')

    print('Creating html files from the md files.')
    for zettel_path in new_zettel_paths:
        gh_md_to_html.main(zettel_path, destination=site_path)

    all_html_paths = get_file_paths(site_posts_path, '.html')

    # Fix the images. gh_md_to_html doesn't seem to convert the image links correctly.
    # `.png" src="/images/` must be changed to
    # `.png" src="images/`
    incorrect_link_pattern = r'\.png\" src=\".+images/'
    n = replace_pattern(incorrect_link_pattern, '.png" src="images/', all_html_paths)
    print(f'Fixed the src path of {n} image links.')

    # Convert any attachment links from the md to the html format (gh_md_to_html doesn't do this).
    md_link_pattern = r'\[(.+)]\((.+)\)'
    n = replace_pattern(md_link_pattern, r'<a href="\2">\1</a>', all_html_paths)
    print(f'Converted {n} attachment links from the md to the html format.')

    # TODO: create a posts folder. Only index.html and about.html should be in the root folder.
    # Move index.html and about.html to the root folder.
    # root_html_names = [ 'index.html', 'about.html' ]
    # root_html_paths = []
    # for file_name in root_html_names:
    #     for path in all_html_paths:
    #         if path.endswith(file_name):
    #             new_html_path = os.path.join(site_path, file_name)
    #             os.rename(path, new_html_path)
    #             root_html_paths += new_html_path
    #             all_html_paths.remove(path)
    #             print(f'Moved {file_name} to the root folder.')

    print('Removing some unwanted CSS that was added by gh_md_to_html.')
    remove_css(all_html_paths)
    n = replace_pattern(re.escape('<div class="highlight '), '<div class="', all_html_paths)

    print('Inserting the site header, footer, etc. into each html file.')
    append_html('index.html', f'<br><br><br><br><br><br><br><p style="text-align: center">{copyright_text}</p>')
    new_html_paths = get_new_html_paths(zettel_paths, site_posts_path)
    insert_template_html(new_html_paths, website_title)

    # TODO: if I can't use the gh_md_to_html option to not add extra CSS, try overwriting their CSS instead of editing every HTML file like with remove_css except the one line with a style tag.
    # print('Overwriting github-css.css')
    # overwrite_github_css_file(site_path)

    print('Checking for style.css.')
    check_style(site_path)

    print('Deleting any HTML files that were not just generated and were not listed in custom-HTML-file-names.txt.')
    delete_old_html_files(old_html_paths, all_html_paths, site_path)

    print('\nWebsite generation complete.\n')


def append_html(file_name, html):
    with open(file_name, 'a', encoding='utf8') as file:
        file.write(html)


def insert_template_html(all_html_paths, website_title, folder_name=''):
    this_dir, _ = os.path.split(__file__)
    os.chdir(this_dir)
    for path in all_html_paths:
        with open(path, 'r+', encoding='utf8') as file:
            contents = file.read()
            file.truncate(0)
            contents = get_header_html(folder_name, website_title) + contents + get_footer_html()
            file.write(contents)


def get_header_html(folder, website_title):
    with open('header.html', 'r', encoding='utf8') as file:
        header_html = file.read()
    header_html = header_html.replace('{folder}', folder)
    header_html = header_html.replace('{website_title}', website_title)

    return header_html


def get_footer_html(footer=''):
    time_now = str(datetime.datetime.now())
    with open('footer.html', 'r', encoding='utf8') as file:
        footer_html = file.read()
    footer_html = footer_html.replace('{footer}', footer)
    footer_html = footer_html.replace('{time_now}', time_now)

    return footer_html


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

        # Temporarily remove any code blocks from contents.
        code_block_pattern = r'(`{1,3}(.|\n)*?`{1,3})'
        code_blocks = re.findall(code_block_pattern, contents)
        contents = re.sub(code_block_pattern, '␝', contents)

        # Replace the pattern.
        new_contents, n_replaced = compiled_pattern.subn(replacement_string, contents)
        total_replaced += n_replaced

        # Put back the code blocks.
        for code_block in code_blocks:
            new_contents = re.sub(r'␝', code_block[0], new_contents, count=1)
        
        # Save changes.
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


def get_new_html_paths(zettel_paths, site_posts_path):
    new_html_paths = []
    for path in zettel_paths:
        zettel_name = os.path.basename(path)
        html_name = zettel_name[:-2] + 'html'
        html_path = os.path.join(site_posts_path, html_name)
        new_html_paths.append(html_path)

    return new_html_paths


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


def remove_css(all_html_paths):
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

    for path in all_html_paths:
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
        print('  style.css already exists. The file will not be changed.')
    else:
        print('  style.css was not found. Providing a new copy.')
        shutil.copy('C:/Users/chris/Documents/programming/generate site/style.css', site_path)


def delete_old_html_files(old_html_paths, all_html_paths, site_path):
    '''Delete any HTML files that are not being regenerated and not marked to be saved.
    
    old_html_paths is the list of paths before the #published zettels were converted to HTML.
    all_html_paths is the list of paths after. Files can be marked to be saved by putting
    their name on a new line in custom-HTML-file-names.txt
    '''
    file_name = os.path.join(site_path, 'custom-HTML-file-names.txt')
    with open(file_name, 'r') as file:
        custom_html_file_names = file.read().split('\n')

    old_count = 0
    for old_path in old_html_paths:
        if old_path not in all_html_paths:
            if os.path.basename(old_path) not in custom_html_file_names:
                old_count += 1
                print(f'  Ready to delete {old_path}.')
                answer = input('  Confirm (y/n): ').lower()
                if answer == 'y':
                    os.remove(old_path)
                    print(f'    Deleted {old_path}')
                else:
                    raise ValueError
    if not old_count:
        print('  No old HTML files found.')
    else:
        print(f'  Deleted {old_count} files.')
