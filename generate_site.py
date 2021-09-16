# external imports
import os
import re
import shutil
from mistune import markdown as HTMLConverter  # https://github.com/lepture/mistune
import datetime
from typing import List

# internal imports
from convert_links import convert_links_from_zk_to_md


def main(site_path: str,
         zettelkasten_path: str,
         site_title: str,
         copyright_text: str,
         hide_tags: bool):
    this_dir, _ = os.path.split(__file__)
    if site_path == zettelkasten_path or site_path == this_dir:
        raise ValueError

    site_posts_path = site_path
    # TODO: more changes to the code needed to have some of the files at 
    # a different location.
    # site_posts_path = site_path + '/posts'

    print('Finding zettels that contain `#published`.')
    zettel_paths = get_zettels_to_publish(zettelkasten_path)
    print(f'Found {len(zettel_paths)} zettels that contain `#published`.')
    find_unlinked_zettels(zettel_paths)
    
    print('Deleting all markdown files currently in the site folder.')
    delete_site_md_files(site_posts_path)

    print(f'Copying the zettels to {site_posts_path}')
    new_zettel_paths = copy_zettels_to_site_folder(zettel_paths,
                                                   site_posts_path)

    print('Searching for any attachments that are linked to in the zettels.')
    n = copy_attachments(zettel_paths, site_posts_path)
    print(f'Found {n} attachments and copied them to {site_posts_path}')

    reformat_zettels(new_zettel_paths, hide_tags)
    new_html_paths = regenerate_html_files(new_zettel_paths, site_posts_path)

    fix_image_links(new_html_paths)
    n = convert_attachment_links(new_html_paths)
    print(f'Converted {n} attachment links from the md to the html format.')

    # TODO: create a posts folder. Only index.html and about.html should
    # be in the root folder.
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

    print('Inserting the site header, footer, etc. into each html file.')
    append_html('index.html',
        '<br><br><br><br><br><br><br><p style="text-align: ' \
        f'center">{copyright_text}</p>')
    wrap_template_html(new_html_paths, site_title)

    print('Checking for style.css.')
    check_style(site_path)

    print('\nWebsite generation complete.\n')
    print('Generated HTML files:')
    for path in new_html_paths:
        print(f'  {path}')

    print(f'{len(new_html_paths)} HTML files generated.')


def reformat_zettels(new_zettel_paths: List[str], hide_tags: bool) -> None:
    """Convert any file links to absolute markdown-style HTML links
    
    Also, remove all tags from the files if hide_tags is True.
    """
    make_file_paths_absolute(new_zettel_paths)
    if (hide_tags):
        remove_all_tags(new_zettel_paths)
    convert_links_from_zk_to_md(new_zettel_paths)
    redirect_links_from_md_to_html(new_zettel_paths)


def regenerate_html_files(new_zettel_paths: List[str],
                          site_posts_path: str) -> List[str]:
    """Creates new and deletes old HTML files
    
    May overwrite some HTML files. Old HTML files that were listed in 
    ssg-ignore.txt are saved and not changed at all.
    """
    old_html_paths = get_file_paths(site_posts_path, '.html')
    print('Creating html files from the md files.')
    new_html_paths = create_html_files(new_zettel_paths)
    all_html_paths = get_file_paths(site_posts_path, '.html')

    print('Deleting any HTML files that were not just generated and were not' \
        ' listed in ssg-ignore.txt.')
    delete_old_html_files(old_html_paths, all_html_paths, site_posts_path)

    return new_html_paths


def convert_attachment_links(all_html_paths: List[str]) -> int:
    """Converts any attachment links from the md to the html format
    
    Returns the number of links converted.
    """
    md_link_pattern = r'\[(.+)]\((.+)\)'
    n = replace_pattern(md_link_pattern,
                        r'<a href="\2">\1</a>',
                        all_html_paths)
    return n


def fix_image_links(all_html_paths: List[str]) -> None:
    """Fixes any image links that were not converted correctly
    
    `.png" src="/images/` must be changed to `.png" src="images/`.
    """
    incorrect_link_pattern = r'\.png\" src=\".+images/'
    n = replace_pattern(incorrect_link_pattern,
                        '.png" src="images/',
                        all_html_paths)
    print(f'Fixed the src path of {n} image links.')


def create_html_files(new_zettel_paths: List[str]) -> List[str]:
    """Creates HTML files from markdown files into the site folder
    
    Expects the zettels to already be in the site folder.
    """
    new_html_files = []
    for zettel_path in new_zettel_paths:
        new_html_files.append(create_html_file(zettel_path))
    return new_html_files


def create_html_file(zettel_path: str) -> str:
    """Creates one HTML file from a markdown file in the same folder
    
    Overwrites an HTML if it happens to have the same name. Returns the 
    new HTML file's path.
    """
    with open(zettel_path, 'r', encoding='utf8') as file:
        md_text = file.read()
    html_text = HTMLConverter(md_text)
    html_path = create_html_path(zettel_path)
    with open(html_path, 'w', encoding='utf8') as file:
        file.write(html_text)
    return html_path


def create_html_path(zettel_path: str) -> str:
    """Creates an HTML file path from a corresponding md file path."""
    file_path_and_name, _ = os.path.splitext(zettel_path)
    new_html_path = file_path_and_name + '.html'
    return new_html_path


def redirect_links_from_md_to_html(new_zettel_paths: List[str]) -> None:
    """Changes links from pointing to markdown files to HTML files."""
    md_link_pattern = r'(?<=\S)\.md(?=\))'
    n = replace_pattern(md_link_pattern, '.html', new_zettel_paths)
    print(f'Converted {n} internal links from ending with `.md` to ending ' \
        'with `.html`.')


def make_file_paths_absolute(new_zettel_paths: List[str]) -> None:
    """Converts all relative file paths to absolute file paths."""
    attachment_link_pattern = r'(?<=]\()C:[^\n]*?([^\\/\n]+\.(pdf|png))(?=\))'
    n = replace_pattern(attachment_link_pattern, r'\1', new_zettel_paths)
    print(f'Converted {n} absolute file paths to relative file paths.')


def copy_attachments(zettel_paths: List[str], site_posts_path: str) -> int:
    """Copies files linked to in the zettels into the site folder."""
    attachment_paths = get_attachment_paths(zettel_paths)
    for path in attachment_paths:
        try:
            shutil.copy(path, site_posts_path)
        except shutil.SameFileError:
            _, file_name = os.path.split(path)
            print(f'  Did not copy {file_name} because it is already there.')

    return len(attachment_paths)


def copy_zettels_to_site_folder(zettel_paths: List[str],
                                site_posts_path: str) -> List[str]:
    """Copies zettels to the site folder
    
    Returns the new zettels' paths.
    """
    new_zettel_paths = []
    for zettel_path in zettel_paths:
        new_zettel_paths.append(shutil.copy(zettel_path, site_posts_path))
    return new_zettel_paths


def remove_all_tags(new_zettel_paths: List[str]) -> None:
    """Removes all tags from the zettels.
    
    Prints a message saying how many tags were removed.
    """
    tag_pattern = r'(?<=\s)#[a-zA-Z0-9_-]+'
    n = replace_pattern(tag_pattern, '', new_zettel_paths)
    print(f'Removed {n} tags.')


def append_html(file_name: str, html: str) -> None:
    """Appends a string of HTML into a file."""
    with open(file_name, 'a', encoding='utf8') as file:
        file.write(html)


def wrap_template_html(all_html_paths: List[str],
                         site_title: str,
                         folder_name: str = '') -> None:
    """Wraps each HTML file's contents with a header and footer."""
    this_dir, _ = os.path.split(__file__)
    os.chdir(this_dir)
    for path in all_html_paths:
        with open(path, 'r+', encoding='utf8') as file:
            contents = file.read()
            file.truncate(0)
            contents = get_header_html(folder_name, site_title) \
                + contents \
                + get_footer_html()
            file.write(contents)


def get_header_html(folder: str, site_title: str) -> str:
    """Retrieves the site's header HTML from header.html."""
    with open('header.html', 'r', encoding='utf8') as file:
        header_html = file.read()
    header_html = header_html.replace('{folder}', folder)
    header_html = header_html.replace('{site_title}', site_title)
        # These strings are not supposed to be f-strings.

    return header_html


def get_footer_html(footer: str = '') -> str:
    """Retrieves the site's footer HTML from footer.html."""
    time_now = str(datetime.datetime.now())
    with open('footer.html', 'r', encoding='utf8') as file:
        footer_html = file.read()
    footer_html = footer_html.replace('{footer}', footer)
    footer_html = footer_html.replace('{time_now}', time_now)

    return footer_html


def replace_pattern(pattern: str,
                    replacement: str,
                    file_paths: List[str],
                    encoding: str = 'utf8') -> int:
    """Replaces a regex pattern with a string in multiple files
    
    Returns the total number of replacements.
    """
    total_replaced = 0
    chosen_pattern = re.compile(pattern)
    triple_code_block_pattern = re.compile(r'(?<=\n)(`{3}(.|\n)*?(?<=\n)`{3})')
    single_code_block_pattern = re.compile(r'(`[^`]+?`)')
    
    for file_path in file_paths:
        with open(file_path, 'r', encoding=encoding) as file:
            try:
                contents = file.read()
            except UnicodeDecodeError as e:
                print(f'UnicodeDecodeError: {e}')
                raise e

        # Temporarily remove any code blocks from contents.
        # TODO: use mistune's ast instead?
        triple_code_blocks = triple_code_block_pattern.findall(contents)
        if len(triple_code_blocks):
            contents = triple_code_block_pattern.sub('␝', contents)

        single_code_blocks = single_code_block_pattern.findall(contents)
        if len(single_code_blocks):
            contents = single_code_block_pattern.sub('␞', contents)

        # Replace the pattern.
        new_contents, n_replaced = chosen_pattern.subn(replacement, contents)
        total_replaced += n_replaced

        # Put back the code blocks.
        for single_code_block in single_code_blocks:
            new_contents = re.sub(r'␞',
                                  single_code_block.replace('\\', r'\\'),
                                  new_contents,
                                  count=1)
        for triple_code_block in triple_code_blocks:
            new_contents = re.sub(r'␝',
                                  triple_code_block[0].replace('\\', r'\\'),
                                  new_contents,
                                  count=1)
        
        # Save changes.
        if n_replaced > 0:
            with open(file_path, 'w', encoding=encoding) as file:
                file.write(new_contents)

    return total_replaced


def get_zettels_to_publish(dir_path: str) -> List[str]:
    """Finds all the zettels that contain '#published'."""
    zettel_paths = get_file_paths(dir_path, '.md')
    zettels_to_publish = []
    published_tag_pattern = re.compile(r'(?<=\s)#published(?=\s)')

    for zettel_path in zettel_paths:
        with open(zettel_path, 'r', encoding='utf8') as zettel:
            try:
                contents = zettel.read()
            except UnicodeDecodeError:
                print(f'UnicodeDecodeError in file {zettel_path}')
                raise

        match = published_tag_pattern.search(contents)
        if match:
            zettels_to_publish.append(zettel_path)

    return zettels_to_publish


def find_unlinked_zettels(zettel_paths: List[str]) -> None:
    """Raises ValueError if any zettel is not linked to in index.md."""
    zettel_ids = remove_alpha_names(get_zettel_names(zettel_paths))
    for path in zettel_paths:
        with open(path, 'r', encoding='utf8') as file:
            contents = file.read()
        for zettel_id in zettel_ids:
            zettel_link = '[[' + zettel_id + ']]'
            if zettel_link in contents:
                zettel_ids.remove(zettel_id)
    if zettel_ids:
        n = len(zettel_ids)
        raise ValueError(f'{n} zettels have not been linked to in ' \
            f'index.md. Their IDs are:\n{"\n".join(zettel_ids)}')


def get_zettel_names(zettel_paths: List[str]) -> List[str]:
    """Gets zettel file names from their paths."""
    zettel_names = []
    for path in zettel_paths:
        zettel_id, _ = os.path.splitext(path)
        zettel_names.append(zettel_id)
    return zettel_names


def remove_alpha_names(strings: List[str]) -> List[str]:
    """Removes any strings that contain alpha characters."""
    numeric_strings = []
    for s in strings:
        if s.isnumeric():
            numeric_strings.append(s)
    return numeric_strings


def delete_site_md_files(site_posts_path: str) -> None:
    """Permanently deletes all the markdown files in the site folder."""
    md_paths = get_file_paths(site_posts_path, '.md')
    for path in md_paths:
        os.remove(path)


def get_file_paths(dir_path: str, file_extension: str) -> List[str]:
    """Gets the paths of files in a directory
    
    Only paths of files with the given file extension are included.
    """
    os.chdir(dir_path)
    dir_list = os.listdir()
    file_paths = []

    for file_name in dir_list:
        if file_name.endswith(file_extension):
            file_name = os.path.abspath(file_name)
            file_paths.append(file_name)

    return file_paths


def get_attachment_paths(zettel_paths: List[str]) -> List[str]:
    """Gets the file attachment links in multiple zettels."""
    attachment_paths = []
    new_attachment_groups = []

    attachment_pattern = re.compile(r'(?<=]\()(.+\S\.(pdf|png))(?=\))')
    for zettel_path in zettel_paths:
        with open(zettel_path, 'r', encoding='utf8') as zettel:
            contents = zettel.read()
        new_attachment_groups = attachment_pattern.findall(contents)
        for group in new_attachment_groups:
            if not group[0].startswith('http'):
                attachment_paths.append(group[0])

    return attachment_paths


def check_style(site_path: str) -> None:
    """Copy style.css into the site folder if it's not there already.
    
    If style.css is already there, this function does nothing.
    """
    site_style_path = os.path.join(site_path, 'style.css')
    if os.path.isfile(site_style_path):
        print('  style.css already exists. The file will not be changed.')
    else:
        print('  style.css was not found. Providing a new copy.')
        this_dir, _ = os.path.split(__file__)
        this_style_path = os.path.join(this_dir, 'style.css')
        shutil.copy(this_style_path, site_path)


def delete_old_html_files(old_html_paths: List[str],
                          all_html_paths: List[str],
                          site_path: str) -> None:
    '''Delete HTML files that are not being generated or saved

    old_html_paths is the paths to HTML files present before the
    #published zettels were converted to HTML. all_html_paths is the
    ones present after. A file can be marked to be saved by putting its
    absolute path on a new line in ssg-ignore.txt.
    '''
    file_name = os.path.join(site_path, 'ssg-ignore.txt')
    with open(file_name, 'r', encoding='utf8') as file:
        ignored_html_paths = file.read().split('\n')

    # Make sure all the slashes in all the paths are the same.
    for path in ignored_html_paths:
        path = path.replace('/', '\\')

    old_count = 0
    for old_path in old_html_paths:
        if old_path not in all_html_paths:
            if old_path not in ignored_html_paths:
                old_count += 1
                print(f'  Ready to delete {old_path}.')
                answer = input('  Confirm (y/n): ').lower()
                if answer == 'y':
                    os.remove(old_path)
                    print('    File deleted.')
                else:
                    print('    File saved.')
    if not old_count:
        print('  No old HTML files found.')
    else:
        print(f'  Deleted {old_count} files.')


if __name__ == '__main__':
    # zettelkasten_path = 'C:/Users/chris/Documents/zettelkasten'
    # site_path = 'C:/Users/chris/Documents/blog'
    # site_title = "Chris' notes"
    # copyright_text = '© 2021 Chris Wheeler'
    # hide_tags = True  # If true, tags will be removed from the copied 
        ## zettels when generating the site.
    
    # main(site_path,
    #      zettelkasten_path,
    #      site_title,
    #      copyright_text,
    #      hide_tags)

    raise ValueError('Edit the comments above this line of code and delete ' \
        'this line of code that raises ValueError to use this program.')
