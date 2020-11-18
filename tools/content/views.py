import logging
from django.shortcuts import render
from requests.exceptions import RequestException
from content.scraper.errors import ScraperError, PageNotFoundError, PrivateAccountError
from content.scraper.scraper import DataScraper, DataLoader
from .forms import PostForm


logger = logging.getLogger('content.views')


def parse_content(request):
    post_content = None
    error = None

    if request.method == 'POST':
        form = PostForm(request.POST)

        if form.is_valid():
            cd = form.cleaned_data
            try:
                post_content = DataScraper().scrape(cd['url'], cd['caption'])

                if len(post_content['urls']) > 1 or 'text' in post_content:
                    post_content.update({'zipfile_url': DataLoader().make_zip_file(post_content)})

                logger.info(f'SUCCESS! Form data: {cd}. Content: {post_content}.')
            except PageNotFoundError:
                error = 'The page you are looking for does not exist.'
                logger.exception(f'Shown error: {error} Form data: {cd}.')
            except PrivateAccountError:
                error = 'The link relate to Private Account.'
                logger.exception(f'Shown error: {error} Form data: {cd}.')
            except (RequestException, ScraperError):
                error = 'Temporary error, please try again later.'
                logger.exception(f'Shown error: {error} Form data: {cd}.')
    else:
        form = PostForm()

    return render(request, 'content/post/detail.html', {'form': form,
                                                        'post_content': post_content,
                                                        'errors': error})
