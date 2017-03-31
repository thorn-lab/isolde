# vim: set expandtab shiftwidth=4 softtabstop=4:

from chimerax.core.toolshed import BundleAPI
from . import geometry


class _MyAPI(BundleAPI):

    @staticmethod
    def get_class(class_name):
        # 'get_class' is called by session code to get class from bundle that
        # was saved in a session
        if class_name == 'MolProbity_ToolUI':
            from . import tool
            return tool.MolProbity_ToolUI
        return None

    @staticmethod
    def start_tool(session, tool_name):
        # 'start_tool' is called to start an instance of the tool
        from .tool import MolProbity_ToolUI
        from chimerax.core import tools
        return tools.get_singleton(session, MolProbity_ToolUI, 'MolProbity', create=True)


    @staticmethod
    def register_command(command_name):
        # 'register_command' is lazily called when the command is referenced
        from chimerax.core.commands import register
        # if command_name == 'fps':
        #     register(command_name + " start", fps.fps_start_desc, fps.fps_start)
        #     register(command_name + " stop", fps.fps_stop_desc, fps.fps_stop)
        # elif command_name == 'isolde':
        #     from . import cmd
        #     cmd.register_isolde()

bundle_api = _MyAPI()