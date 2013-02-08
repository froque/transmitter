## Credit to rakslice from http://stackoverflow.com/a/6064270/1077818

from twisted.python import urlpath
from twisted.web.resource import Resource
from twisted.web.util import redirectTo

class RedirectToScheme(Resource):
    """
    I redirect to the same path at a given URL scheme
    @param newScheme: scheme to redirect to (e.g. https)
    """

    isLeaf = 0

    def __init__(self, newScheme, securePort):
        Resource.__init__(self)
        self.newScheme = newScheme
        self.securePort = securePort

    def render(self, request):
        newURLPath = request.URLPath()

        ## test if the scheme is the same
        if newURLPath.scheme == self.newScheme:
            raise ValueError("Redirect loop: we're trying to redirect to the same URL scheme in the request")
        newURLPath.scheme = self.newScheme

        ## check port and change if needed
        n = newURLPath.netloc.split(':')
        newURL = n[0]
        if len(n) > 1:
            newURLPath.netloc = newURL + ":" +  str(self.securePort)
        return redirectTo(newURLPath, request)

    def getChild(self, name, request):
        return self
