"""Scraper for parsing media data from Instagram links and creating content files for download."""
import re
import json
from zipfile import ZipFile
from io import BytesIO
import requests
from django.core.files.storage import FileSystemStorage
from .errors import AccessDeniedError, PageNotFoundError, PrivateAccountError, UnknownPageTypeError


class DataScraper:
    """Methods for media data from post response."""

    def get_media_data(self, res_text):
        """
        Get shared data from response and find out what page type we have.
        If 'PostPage' type - return dict with media data, else raise correct error.

        _sharedData = {} in response with all content, types:
        {"config":{"csrf_token":.."entry_data":{"PostPage":[{"graphql":{"shortcode_media":{"__typename":"Graph"..
        {"config":{"csrf_token":.."entry_data":{"ProfilePage":[{"logging_page_id":"profilePage_8464881"..
        {"config":{"csrf_token":.."entry_data":{"HttpErrorPage":[{}]},"hostname":"www.instagram.com"..

        :param res_text: response
        :type res_text: <class 'str'>

        :raises PageNotFoundError: if 'HttpErrorPage' in shared data, 404 status code
        :raises PrivateAccountError: if url relate to Private Account
        :raises UnknownPageTypeError: if in shared data not "PostPage", "ProfilePage" or "HttpErrorPage"

        :rtype: <class 'dict'>
        :return: media data from response, e.g. {'__typename': 'GraphSidecar', 'id': '240', 'shortcode': 'CFH', ...,
                                                                            'edge_related_profiles': {'edges': []}}
        """
        shared_data = re.search(r'_sharedData = (\{.+});<\/script>', res_text)
        entry_data = json.loads(shared_data.group(1))['entry_data']

        if 'PostPage' in entry_data:
            return entry_data['PostPage'][0]['graphql']['shortcode_media']
        elif 'HttpErrorPage' in entry_data:
            raise PageNotFoundError('Page not found')
        elif 'ProfilePage' in entry_data:
            raise PrivateAccountError('The post is private')
        else:
            raise UnknownPageTypeError(f'Unknown page type in entry_data: {entry_data}')

    def make_node_urls(self, node_data):
        """
        Create list with content type, display url and download url.

        :param node_data: one node data
        :type node_data: <class 'dict'>

        :rtype: <class 'list'>
        :return: list with type, display url and download url
        """
        node_display = node_data['display_url']
        if node_data['__typename'] == 'GraphVideo':
            return ['video', node_display, node_data['video_url']]

        return ['image', node_display, node_display]

    def parse_media_data(self, media_data, caption):
        """
        Parse media data from response.

        Three types of data:
            'GraphVideo', 'GraphImage' and 'GraphSidecar' that contains inside 'GraphVideo'and 'GraphImage'.
        'GraphVideo' maybe video: ['product_type'] == 'feed' or IGTV video: ['product_type'] == 'igtv'.
        For IGTV title required.

        :param media_data: media data from response
        :type media_data: <class 'dict'>

        :param caption: parse caption from media data or not
        :type caption: <class 'bool'>

        :rtype: <class 'dict'>
        :return: content from media data
        """
        typename = media_data['__typename']
        post_content = {
            'shortcode': media_data['shortcode'],
            'igtv': bool(typename == 'GraphVideo' and media_data['product_type'] == 'igtv')
        }

        if typename == 'GraphSidecar':
            post_content.update({'urls': [self.make_node_urls(elem['node'])
                                          for elem in media_data['edge_sidecar_to_children']['edges']]})
        else:
            post_content.update({'urls': [self.make_node_urls(media_data)]})

        if caption:
            content_text = ''
            if 'title' in media_data and media_data['title']:
                content_text = media_data['title'] + '\n'
            if media_data['edge_media_to_caption']['edges']:
                content_text += media_data['edge_media_to_caption']['edges'][0]['node']['text']
            if content_text:
                post_content.update({'text': content_text})

        return post_content

    def scrape(self, url, caption):
        """
        Main function, make url request, get media data from response and parse it.

        :param url: post url from instagram
        :type url: <class 'str'>

        :param caption: parse caption from media data or not
        :type caption: <class 'bool'>

        :raises AccessDeniedError: if need login to access to media data

        :rtype: <class 'dict'>
        :return: post content, e.g {'shortcode': 'CFdH_JXAGyx', 'igtv': False, 'urls': [['image',
                                'https://frt3-1.cdninstagram.com/v/2459_n.jpg?_nc_ohc=V19eWR&oe=5FCF02E8',
                                'https://frt3-1.cdninstagram.com/v/2459_n.jpg?_nc_ohc=V19eWR&oe=5FCF02E8'],...,[...]],
                                'text': '@KKWFragrance Diamonds', 'quantity': 6}
        """
        res = requests.get(url)

        if 'https://www.instagram.com/accounts/login/' in res.url:
            raise AccessDeniedError('Need login to access')

        media_data = self.get_media_data(res.text)
        return self.parse_media_data(media_data, caption)


class DataLoader:
    """Create files with post content."""

    def make_empty_zip(self):
        """
        Make empty .zip file in buffer.

        :rtype: <class '_io.BytesIO'>
        :return: buffer with empty .zip
        """
        buffer = BytesIO()
        file = ZipFile(buffer, 'w')
        file.close()
        return buffer

    def save_file(self, name, file):
        """
        Save file in django FileSystemStorage.

        :param name: file name
        :type name: <class 'str'>

        :param file: file from buffer
        :type file: <class '_io.BytesIO'>

        :rtype: <class 'str'>
        :return: path to file and file url
        """
        fs = FileSystemStorage()
        filename = fs.save(name, file)
        return fs.path(filename), fs.url(filename)

    def get_content_name(self, content_url):
        """
        Get content name from url in post content.

        :param content_url: file name
        :type content_url: <class 'str'>

        :rtype: <class 'str'>
        :return: path to file and file url
        """
        endpoint = content_url.split('/')[-1]
        return re.match(r'(.+\.(?:jpg|mp4))', endpoint).group(0)

    def make_zip_file(self, post_content):
        """
        Make .zip file with all files and return url for them.

        :param post_content: post content
        :type post_content: <class 'dict'>

        :rtype: <class 'str'>
        :return: url to file
        """
        file_path, file_url = self.save_file(post_content['shortcode'] + '.zip', self.make_empty_zip())
        with ZipFile(file_path, 'w') as zipf:
            if post_content['igtv'] is True:
                zipf.writestr('igtv_link.txt', post_content['urls'][0][2])
            else:
                for url in post_content['urls']:
                    zipf.writestr(self.get_content_name(url[2]), requests.get(url[2]).content)

            if 'text' in post_content:
                zipf.writestr('caption.txt', post_content['text'])
        return file_url
