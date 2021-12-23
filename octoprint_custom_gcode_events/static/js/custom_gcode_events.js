/*
 * View model for OctoPrint-Custom_gcode_events
 *
 * Author: RoboMagus
 * License: AGPLv3
 */
$(function() {
    function Custom_gcode_eventsViewModel(parameters) {
        var self = this;

		var PLUGIN_ID = "custom_gcode_events";

        self.settings = parameters[0];
        
        self.received_gcode_hooks = ko.observableArray();
        self.sent_gcode_hooks     = ko.observableArray();

        self.onSettingsBeforeSave = function() {
            // ko.utils.arrayForEach(self.settings.settings.plugins.LightControls.light_controls(), function (item, index) {
            // });
        };

        
        self.addRcvdEvent = function() {
            self.settings.settings.plugins.custom_gcode_events.received_gcode_hooks.push({
                gcode: ko.observable(''),
                event: ko.observable(''),
                exactMatch: ko.observable('true') });
            self.received_gcode_hooks(self.settings.settings.plugins.custom_gcode_events.received_gcode_hooks());
        };

        self.removeRcvdEvent = function(profile) {
            self.settings.settings.plugins.custom_gcode_events.received_gcode_hooks.remove(profile);
            self.received_gcode_hooks(self.settings.settings.plugins.custom_gcode_events.received_gcode_hooks());
        };

        self.addSntEvent = function() {
            self.settings.settings.plugins.custom_gcode_events.sent_gcode_hooks.push({
                gcode: ko.observable(''),
                event: ko.observable(''),
                exactMatch: ko.observable('true') });
            self.sent_gcode_hooks(self.settings.settings.plugins.custom_gcode_events.sent_gcode_hooks());
        };

        self.removeSntEvent = function(profile) {
            self.settings.settings.plugins.custom_gcode_events.sent_gcode_hooks.remove(profile);
            self.sent_gcode_hooks(self.settings.settings.plugins.custom_gcode_events.sent_gcode_hooks());
        };
    }

    /* view model class, parameters for constructor, container to bind to
     * Please see http://docs.octoprint.org/en/master/plugins/viewmodels.html#registering-custom-viewmodels for more details
     * and a full list of the available options.
     */
    OCTOPRINT_VIEWMODELS.push({
        construct: Custom_gcode_eventsViewModel,
        // ViewModels your plugin depends on, e.g. loginStateViewModel, settingsViewModel, ...
        dependencies: [ "settingsViewModel" ],
        // Elements to bind to, e.g. #settings_plugin_custom_gcode_events, #tab_plugin_custom_gcode_events, ...
        elements: [ "#settings_plugin_custom_gcode_events" ]
    });
});
