from django.core.paginator import Paginator

QUANTUTY_POST_ON_PAGE = 10


def pagination(request, objects):
    paginator = Paginator(objects, QUANTUTY_POST_ON_PAGE)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return page_obj
