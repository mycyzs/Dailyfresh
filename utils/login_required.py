from django.contrib.auth.decorators import login_required
from django.views.generic import View


class LoginReqiuredMixin(object):


    @classmethod
    def as_view(cls, **initkwargs):
        vw_fun = super().as_view(**initkwargs)
        vw_fun = login_required(vw_fun)
        return vw_fun