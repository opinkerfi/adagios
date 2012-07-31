
def resolve_urlname(request):
    """Allows us to see what the matched urlname for this
    request is within the template"""
    from django.core.urlresolvers import resolve
    try:
        res = resolve(request.path)
    	print res.url_name

        if res:
            return {'urlname' : res.url_name}
    except:
        return {}
