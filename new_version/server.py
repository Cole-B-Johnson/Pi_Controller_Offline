from sanic import Sanic
from vfd.VFDBlueprint import VFDBlueprint

app = Sanic("LevitreeBackend")

app.blueprint(VFDBlueprint)