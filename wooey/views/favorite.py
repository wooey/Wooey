from django.contrib.auth.decorators import login_required
from django.contrib.contenttypes.models import ContentType
from django.http import (
    HttpResponseForbidden,
    HttpResponseNotFound,
    HttpResponseBadRequest,
    JsonResponse,
)
from django.views.decorators.csrf import ensure_csrf_cookie

from ..models import Favorite


@login_required
@ensure_csrf_cookie
def toggle_favorite(request):
    """
    Add/remove an object to the user's favorites. Checks for existance and adds if not, else removes.
    This is the underlying mechanism for adding items to the user 'scrapbook' and favorite scripts.

    :param request:
    :param file_id:
    :return:
    """
    if not request.is_ajax():
        return HttpResponseForbidden()

    try:
        app, model, pk = request.POST['app'], request.POST['model'], int(request.POST['pk'])

    except ValueError:
        return HttpResponseBadRequest()

    try:
        ctype = ContentType.objects.get(app_label=app, model=model)
        obj = ctype.get_object_for_this_type(id=pk)

    except Favorite.DoesNotExist:
        return HttpResponseNotFound()

    try:
        fave = Favorite.objects.get(content_type=ctype, object_id=obj.id, user=request.user)

    except Favorite.DoesNotExist:
        # Does not exist, so create it
        fave = Favorite(content_object=obj, user=request.user)
        fave.save()
        is_favorite = True

    else:
        # Exists, so delete it
        fave.delete()
        is_favorite = False

    # Return the current total number for UI updates
    favorites_count = Favorite.objects.filter(content_type=ctype, user=request.user).count()

    return JsonResponse({
        'app': app,
        'model': model,
        'pk': pk,
        'is_favorite': is_favorite,
        'count': favorites_count,
    })
