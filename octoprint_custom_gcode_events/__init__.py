# coding=utf-8
from __future__ import absolute_import

import octoprint.plugin
import logging
import traceback

from octoprint.events import eventManager, Events


## NOTES:
# - Can fire custom events as strings. No need to register beforehand.
# - Restrict to lower-case, trim whitespace and convert '-' and ' ' to '_' when saving settings.
# - Prepend with Gcode_event_*

# Distinction between contains ('in') and == during GCode handling..


class Custom_gcode_eventsPlugin(octoprint.plugin.SettingsPlugin,
                                octoprint.plugin.AssetPlugin,
                                octoprint.plugin.TemplatePlugin,
                                octoprint.plugin.StartupPlugin ):

    ##~~ SettingsPlugin mixin

    def get_settings_defaults(self):
        return dict(
            received_gcode_hooks=[{'gcode': '', 'event': '', 'exactMatch': True}],
            sent_gcode_hooks=[{'gcode': '', 'event': '', 'exactMatch': True}]
        )

    def on_settings_initialized(self):
        self.received_gcode_hooks = self._settings.get(["received_gcode_hooks"])
        self.sent_gcode_hooks = self._settings.get(["sent_gcode_hooks"])
        self._logger.info("received_gcode_hooks settings initialized: '{}'".format(self.received_gcode_hooks))
        self._logger.info("sent_gcode_hooks settings initialized: '{}'".format(self.sent_gcode_hooks))
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
        self._logger.info("    sent_gcode_hooks settings saved: '{}'".format(self._settings.get(["sent_gcode_hooks"])))
        self.received_gcode_hooks = self._settings.get(["received_gcode_hooks"])
        self.sent_gcode_hooks = self._settings.get(["sent_gcode_hooks"])


    ##~~ StartupPlugin mixin
 
    def on_after_startup(self):
        self._logger.info("CustomGcodeEvents Startup()")
        eventManager().fire("custom_fire_at_startup")
        self.triggered = False
    
    ##~~ octoprint.comm.protocol.gcode.received Plugin Hook:
    def recv_callback(self, comm_instance, line, *args, **kwargs):
        if ( not line or self.received_gcode_hooks == None or len(self.received_gcode_hooks) == 0 ):
            return line
        # Do processing...
        try:
            for entry in self.received_gcode_hooks:
                if entry["exactMatch"] and line == entry["gcode"]:
                    self._logger.info("Received exact match for '{}'. Firing event 'gcode_event_{}'".format(entry["gcode"], entry["event"]))
                    eventManager().fire('gcode_event_' + entry["event"])
                elif entry["gcode"] in line:
                    self._logger.info("Received 'contains' match for '{}'. Firing event 'gcode_event_{}'".format(entry["gcode"], entry["event"]))
                    eventManager().fire('gcode_event_' + entry["event"])
        except:
            exc_type, exc_value, exc_tb = sys.exc_info()
            self._logger.error("exception in recv_callback(): {}, {}".format(exc_type, exc_value))
            self._logger.error("TraceBack: {}".format(traceback.extract_tb(exc_tb)))

        return line

    ##~~ octoprint.comm.protocol.gcode.sending Plugin Hook:
    # https://docs.octoprint.org/en/master/plugins/hooks.html#octoprint-comm-protocol-gcode-phase
    def sent_callback(self, comm_instance, phase, cmd, cmd_type, gcode, subcode=None, tags=None, *args, **kwargs):
        if ( not gcode or self.sent_gcode_hooks == None or len(self.sent_gcode_hooks) == 0 ):
            return None
        # Do processing...
        try:
            for entry in self.sent_gcode_hooks:
                if entry["exactMatch"] and gcode == entry["gcode"]:
                    self._logger.info("Sent exact match for '{}'. Firing event 'gcode_event_{}'".format(entry["gcode"], entry["event"]))
                    eventManager().fire('gcode_event_' + entry["event"])
                elif entry["gcode"] in gcode:
                    self._logger.info("Sent 'contains' match for '{}'. Firing event 'gcode_event_{}'".format(entry["gcode"], entry["event"]))
                    eventManager().fire('gcode_event_' + entry["event"])
        except:
            exc_type, exc_value, exc_tb = sys.exc_info()
            self._logger.error("exception in sent_callback(): {}, {}".format(exc_type, exc_value))
            self._logger.error("TraceBack: {}".format(traceback.extract_tb(exc_tb)))

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
                "displayName": "Custom GCode Events",
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

__plugin_name__ = "Custom GCode Events"

__plugin_pythoncompat__ = ">=3,<4" # only python 3

def __plugin_load__():
    global __plugin_implementation__
    __plugin_implementation__ = Custom_gcode_eventsPlugin()

    global __plugin_hooks__
    __plugin_hooks__ = {
        "octoprint.plugin.softwareupdate.check_config": __plugin_implementation__.get_update_information,
        "octoprint.comm.protocol.gcode.received": __plugin_implementation__.recv_callback,
        "octoprint.comm.protocol.gcode.sent": __plugin_implementation__.sent_callback
    }
