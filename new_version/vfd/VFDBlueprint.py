from sanic.response import json
from sanic import BadRequest, Blueprint
from sanic.log import logger
from sanic_ext import validate, openapi
import yaml
from dataclasses import asdict
from RequestTypes import SetVFDStateParams
from .VFDController import VFDController, VFD, VFDState

VFDBlueprint = Blueprint("vfd", url_prefix="/vfd")

@VFDBlueprint.get("/")
@openapi.definition(
    summary="List all VFDs configured on the system",
    tag="VFD Control",
    response={"application/json": [VFD]}
)
async def get_vfd_list(request):
    controller: VFDController = request.app.ctx.vfdController
    return json(controller.getVFDSArr())

@VFDBlueprint.get("/<vfd_id>")
@openapi.definition(
    summary="Get state of single VFD",
    tag="VFD Control",
    response={
        "application/json": VFDState
    },
)
async def get_vfd_state(request, vfd_id: str):
    controller: VFDController = request.app.ctx.vfdController
    if not controller.hasVFD(vfd_id):
        raise BadRequest(f"VFD {vfd_id} does not exist!")

    vfdState = controller.getStateDict(vfd_id)

    return json(vfdState)

@VFDBlueprint.post("/<vfd_id>")
@openapi.definition(
    summary="Set state of single VFD",
    tag="VFD Control",
    body={
        "application/json": SetVFDStateParams.model_json_schema()
    },
)
@validate(json=SetVFDStateParams)
async def set_vfd_state(request, vfd_id: str, body: SetVFDStateParams):
    controller: VFDController = request.app.ctx.vfdController

    if not controller.hasVFD(vfd_id):
        raise BadRequest(f"VFD {vfd_id} does not exist!")
    
    if "frequency" in body:
        request.app.add_task(controller.setFrequency(vfd_id, body.frequency))

    if "drive_mode" in body:
        request.app.add_task(controller.setDriveMode(vfd_id, body.drive_mode))

    return json()

@VFDBlueprint.listener('after_server_start')
def open_serial_port(app):
    with open("config.yaml") as cfgFile:
        cfg = yaml.load(cfgFile, Loader=yaml.FullLoader)
        app.ctx.vfdController = VFDController(cfg["modbus_path"])
        for modbus_device in cfg["modbus_devices"]:
            if modbus_device["type"] == "VFD":
                app.ctx.vfdController.registerVFD(modbus_device["slave_id"], modbus_device["display_name"], modbus_device["name"], model=modbus_device["model"])
                app.add_task(app.ctx.vfdController.vfdStateUpdateLoop(modbus_device["name"]))
        app.add_task(app.ctx.vfdController.initializeModbus)