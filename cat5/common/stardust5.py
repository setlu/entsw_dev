
from apollo.scripts.entsw.libs.diags.stardust import Stardust


class StardustC9500(Stardust):
    def __init__(self, **kwargs):
        super(StardustC9500, self).__init__(**kwargs)
        return