# coding=utf-8
from __future__ import absolute_import

import octoprint.plugin
import logging
from octoprint.events import eventManager, Events

class Custom_gcode_eventsPlugin(octoprint.plugin.SettingsPlugin,
                                octoprint.plugin.AssetPlugin,
                                octoprint.plugin.TemplatePlugin,
                                octoprint.plugin.StartupPlugin ):

    ##~~ SettingsPlugin mixin

    def get_settings_defaults(self):
        return dict(
            received_gcode_hooks=[{'gcode': ''}]
        )

    def on_settings_initialized(self):
        received_gcode_hooks = self._settings.get(["received_gcode_hooks"])
        self._logger.info("received_gcode_hooks settings initialized: '{}'".format(received_gcode_hooks))
#       # On initialization check for incomplete settings!
#       modified=False
#       for idx, ctrl in enumerate(received_gcode_hooks):
#           if not self.checkLightControlEntryKeys(ctrl):
#               lightControls[idx] = self.updateLightControlEntry(ctrl)
#               modified=True
#           self.gpio_startup(lightControls[idx]["pin"], lightControls[idx])
#
#       if modified:
#           self._settings.set(["light_controls"], lightControls)

    def on_settings_save(self, data):
        # Get old settings:

        # Get updated settings
        octoprint.plugin.SettingsPlugin.on_settings_save(self, data)

        # Handle changes (if new != old)
        self._logger.info("received_gcode_hooks settings saved: '{}'".format(self._settings.get(["received_gcode_hooks"])))

    ##~~ StartupPlugin mixin
 
    def on_after_startup(self):
        self.triggered = False
        
    ##~~ octoprint.events.register_custom_events Plugin Hook:
    def register_custom_events(self, *args, **kwargs):
        return ["notify"]
    
    ##~~ octoprint.comm.protocol.gcode.received Plugin Hook:
    def recv_callback(self, comm_instance, line, *args, **kwargs):
        # Found keyword, fire event and block until other text is received
        if "echo:busy: paused for user" in line:
            self._logger.info("Custom GCode Pause received...")
            if not self.triggered:
                self._logger.info("Firing evnt...")
                eventManager().fire(Events.PLUGIN_CUSTOM_GCODE_EVENTS_NOTIFY)
                self.triggered = True
        # Other text, we may fire another event if we encounter "paused for user" again
        else:
            self.triggered = False
            
        return line

    ##~~ octoprint.comm.protocol.gcode.sending Plugin Hook:
    # https://docs.octoprint.org/en/master/plugins/hooks.html#octoprint-comm-protocol-gcode-phase
    def sent_callback(self, comm_instance, phase, cmd, cmd_type, gcode, subcode=None, tags=None, *args, **kwargs):
    #   if ( not gcode or self.active_gcode_send_events == None or len(self.active_gcode_send_events) == 0 ):
    #       return None

		# Do processing...

        return None


    ##~~ AssetPlugin mixin

    def get_assets(self):
        # Define your plugin's asset files to automatically include in the
        # core UI here.
        return {
            "js": ["js/custom_gcode_events.js"],
        }


    ##~~ TemplatePlugin mixin

    def get_template_configs(self):
        return [ 
            dict(type="settings", template="custom_gcode_events_settings.jinja2", custom_bindings=True)
        ]


    ##~~ Softwareupdate hook

    def get_update_information(self):
        # Define the configuration for your plugin to use with the Software Update
        # Plugin here. See https://docs.octoprint.org/en/master/bundledplugins/softwareupdate.html
        # for details.
        return {
            "custom_gcode_events": {
                "displayName": "Custom_gcode_events Plugin",
                "displayVersion": self._plugin_version,

                # version check: github repository
                "type": "github_release",
                "user": "RoboMagus",
                "repo": "OctoPrint-Custom_gcode_events",
                "current": self._plugin_version,

                # update method: pip
                "pip": "https://github.com/RoboMagus/OctoPrint-Custom_gcode_events/archive/{target_version}.zip",
            }
        }

__plugin_name__ = "Custom_gcode_events Plugin"

__plugin_pythoncompat__ = ">=3,<4" # only python 3

def __plugin_load__():
    global __plugin_implementation__
    __plugin_implementation__ = Custom_gcode_eventsPlugin()

    global __plugin_hooks__
    __plugin_hooks__ = {
        "octoprint.plugin.softwareupdate.check_config": __plugin_implementation__.get_update_information,
        "octoprint.comm.protocol.gcode.received": __plugin_implementation__.recv_callback,
        "octoprint.comm.protocol.gcode.sent": __plugin_implementation__.sent_callback,
        "octoprint.events.register_custom_events": __plugin_implementation__.register_custom_events
    }
