# coding=utf-8
from __future__ import absolute_import

import copy
import traceback
import time
import octoprint.plugin

from octoprint.events import eventManager

## ToDo:
#  - Match types: exact, startswith, contains, regex

def ToIntOrDefault(value, default):
    try:
        v = int(value)
    except ValueError:
        v = default
    return v

class Custom_gcode_eventsPlugin(octoprint.plugin.SettingsPlugin,
                                octoprint.plugin.AssetPlugin,
                                octoprint.plugin.TemplatePlugin,
                                octoprint.plugin.StartupPlugin ):

    defaultEntry = {'gcode': '',
                    'topic': '',
                    'event': '',
                    'exactMatch': False,
                    'reFireThreshold': '',
                    'enabled': True }
                    
    ##~~ SettingsPlugin mixin

    def get_settings_defaults(self):
        return dict(
            received_gcode_hooks=[{'gcode': '', 'topic': '', 'event': '', 'exactMatch': True, 'reFireThreshold': '', 'enabled': True}],
            sent_gcode_hooks=[{'gcode': '', 'topic': '', 'event': '', 'exactMatch': True, 'enabled': True}],
            default_refire_threshold='5'
        )

    def checkEventEntry(self, entry):
            return set(self.defaultEntry.keys()) == set(entry.keys())

    def updateEventEntry(self, entry):
        _entry = copy.deepcopy(self.defaultEntry)
        for key in entry:
            _entry[key]=entry[key]
        self._logger.debug("Updated EventEntry from: {}, to {}".format(entry, _entry))
        return _entry

    def on_settings_initialized(self):
        self.received_gcode_hooks = self._settings.get(["received_gcode_hooks"])
        self.sent_gcode_hooks = self._settings.get(["sent_gcode_hooks"])
        self.default_refire_threshold = ToIntOrDefault(self._settings.get(["default_refire_threshold"]), 5)

        # On initialization check for incomplete settings!
        modified=False
        for idx, evt in enumerate(self.received_gcode_hooks):
            if not self.checkEventEntry(evt):
                self.received_gcode_hooks[idx] = self.updateEventEntry(evt)
                modified=True 

        if modified:
            self._settings.set(["received_gcode_hooks"], self.received_gcode_hooks)

        modified=False
        for idx, evt in enumerate(self.sent_gcode_hooks):
            if not self.checkEventEntry(evt):
                self.sent_gcode_hooks[idx] = self.updateEventEntry(evt)
                modified=True 

        if modified:
            self._settings.set(["sent_gcode_hooks"], self.sent_gcode_hooks)

        self._logger.debug("received_gcode_hooks settings initialized: '{}'".format(self.received_gcode_hooks))
        self._logger.debug("sent_gcode_hooks settings initialized: '{}'".format(self.sent_gcode_hooks))
        
    def on_settings_save(self, data):
        # Get updated settings
        octoprint.plugin.SettingsPlugin.on_settings_save(self, data)

        received_gcode_hooks = self._settings.get(["received_gcode_hooks"])
        for idx, hook in enumerate(received_gcode_hooks):
            received_gcode_hooks[idx]["topic"] = hook["topic"].strip().lower().replace(" ","_").replace("-","_").replace("/","_").replace("$","").replace("#","")
            received_gcode_hooks[idx]["event"] = hook["event"].strip()
            received_gcode_hooks[idx]["reFireThreshold"] = ToIntOrDefault(hook["reFireThreshold"], '')

        sent_gcode_hooks = self._settings.get(["sent_gcode_hooks"])
        for idx, hook in enumerate(sent_gcode_hooks):
            sent_gcode_hooks[idx]["topic"] = hook["topic"].strip().lower().replace(" ","_").replace("-","_").replace("/","_").replace("$","").replace("#","")
            sent_gcode_hooks[idx]["event"] = hook["event"].strip()

        self._settings.set(["received_gcode_hooks"], received_gcode_hooks)
        self._settings.set(["sent_gcode_hooks"]    , sent_gcode_hooks    )

        self.received_gcode_hooks = self._settings.get(["received_gcode_hooks"])
        self.sent_gcode_hooks = self._settings.get(["sent_gcode_hooks"])
        self.default_refire_threshold = ToIntOrDefault(self._settings.get(["default_refire_threshold"]), 5)

        self._logger.debug("received_gcode_hooks settings saved: '{}'".format(self.received_gcode_hooks))
        self._logger.debug("    sent_gcode_hooks settings saved: '{}'".format(self.sent_gcode_hooks    ))


    ##~~ StartupPlugin mixin
 
    def on_after_startup(self):
        self._logger.debug("CustomGcodeEvents Startup()")

    ##~~ octoprint.comm.protocol.gcode.received Plugin Hook:
    def recv_callback(self, comm_instance, line, *args, **kwargs):
        if ( not line or line == "ok" or self.received_gcode_hooks == None or len(self.received_gcode_hooks) == 0 ):
            return line
        # Do processing...
        try:
            for entry in self.received_gcode_hooks:
                if entry["enabled"]:
                    _match = False
                    if entry["exactMatch"] and line == entry["gcode"]:
                        _match = True
                    elif entry["gcode"] in line:
                        _match = True

                    if _match:
                        _refire_threshold = ToIntOrDefault(entry.get('reFireThreshold', self.default_refire_threshold), self.default_refire_threshold)
                        refire_threshold = int(time.time()) - _refire_threshold
                        if entry.get('timestamp', 0) <= refire_threshold:
                            self._logger.info("Received match for '{}'. Firing event 'gcode_event_{}'".format(entry["gcode"], entry["topic"]))
                            self.fire_event(entry, {"gcode": line})
                        else:
                            self._logger.debug("Prevent firing for event '{}'. Occured within repetition interval ({} s)!!".format(entry["gcode"], _refire_threshold))
                            entry["timestamp"] = int(time.time())

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
                if entry["enabled"]:
                    if (entry["exactMatch"] and gcode == entry["gcode"]) or (entry["gcode"] in gcode):
                        self._logger.info("Sent match for '{}'. Firing event 'gcode_event_{}'".format(entry["gcode"], entry["topic"]))
                        self.fire_event(entry, {"gcode": gcode, "cmd": cmd})
        except:
            exc_type, exc_value, exc_tb = sys.exc_info()
            self._logger.error("exception in sent_callback(): {}, {}".format(exc_type, exc_value))
            self._logger.error("TraceBack: {}".format(traceback.extract_tb(exc_tb)))

        return None

    def fire_event(self, entry, payload):
        if entry["event"]:
            payload["event"] = entry["event"]
        eventManager().fire('gcode_event_' + entry["topic"], payload)
        entry["timestamp"] = int(time.time())

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
