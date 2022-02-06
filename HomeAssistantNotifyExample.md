## Home Assistant notification example

Using this plugin I've configured Home Assistant to send me notifications whenever the 3D Printer requires attention, or some error has occured.

The following snippet shows an example automation that notifies on configured GCode events similar to my configuration. Here 2 _topics_ are defined in the Octoprint configuration: `action_required` and `error`. In the message field the payload _event_ contains additional information about what actually occured. For instance 'Paused for Filament Change'.

```yaml
id: octoprint_print_gcode_event
alias: Octoprint Print GCode Event Notification
description: ''
mode: single
trigger:
- platform: mqtt
  topic: "octoPrint/event/gcode_event_error"
  id: "ERROR"
- platform: mqtt
  topic: "octoPrint/event/gcode_event_action_required"
  id: "Action Required"
condition: 
# Discard line number and checksum errors
- "{{ not 'Error:No Line Number with checksum' in trigger.payload_json.gcode  }}"
- "{{ not 'Error:Line Number is not Last Line Number' in trigger.payload_json.gcode  }}"
- "{{ not 'Error:No checksum with line' in trigger.payload_json.gcode  }}"
- "{{ not 'Error:checksum mismatch' in trigger.payload_json.gcode  }}"
# Discard old events (30+ sec)
- "{{ (as_timestamp(now())|int) - (trigger.payload_json._timestamp|int) < 30 }}"
action:
- service: script.notify_me
  data:
    title: "Octoprint {{ trigger.id }}!"
    message: "'{{ trigger.payload_json.event }}' with GCode '{{ trigger.payload_json.gcode }}'"
    data:
      channel: "Octoprint {{ trigger.id }}"
      importance: high
      priority: high
      ttl: 0
      color: '#f7b202'
      notification_icon: mdi:printer-3d-nozzle
```

This works well with the settings shown below:

![CustomGcodeEvents_Settings](extras/screenshots/CustomGcodeEvents_settings.PNG)