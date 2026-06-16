# Structure
# "Automation" <<-- Main View
#    "Setup" <<-- Sub View
#               <<-- Sub Sub View ()

Data = {
    "Automation": {
        "Setup": {
            "Type": "Automation",
            "Options": ["Enable", "Disable", "Change Timing"],
        },
        "Checkin": {
            "Type": "Automation",
            "Options": ["Enable", "Disable", "Change Timing"],
        },
        "PickBan": {
            "Type": "Automation",
            "Options": ["Enable", "Disable", "Change Timing"],
        },
    },
    "Channels": {
        "Announcement": {
            "Type": "Channel",
            "Options": ["Change Channel"],
        },
        "Rules": {
            "Type": "Channel",
            "Options": ["Change Channel"],
        },
        "Format": {
            "Type": "Channel",
            "Options": ["Change Channel"],
        },
        "Log": {
            "Type": "Channel",
            "Options": ["Change Channel"],
        }
    },
    "Messages": {
        "Announcement": {
            "Type": "Message",
            "Options": ["Change Message"],
        },
        "Checkin": {
            "Type": "Message",
            "Options": ["Change Message"],
        },
        "Rules": {
            "Type": "Message",
            "Options": ["Change Message"],
        },
        "Format": {
            "Type": "Message",
            "Options": ["Change Message"],
        },
        "PickBan": {
            "Type": "Message",
            "Options": ["Change Message"],
        },
        "Registration": {
            "Type": "Message",
            "Options": ["Change Message"],
        },
        "Reserve": {
            "Type": "Message",
            "Options": ["Change Message"],
        }
    },
    "Presets": {
        "Preset 1": {
            "Type": "Preset",
            "Options": ["Create Preset", "Edit Preset", "Delete Preset"],
        },
        "Preset 2": {
            "Type": "Preset",
            "Options": ["Create Preset", "Edit Preset", "Delete Preset"],
        },
        "Preset 3": {
            "Type": "Preset",
            "Options": ["Create Preset", "Edit Preset", "Delete Preset"],
        },
        "Preset 4": {
            "Type": "Preset",
            "Options": ["Create Preset", "Edit Preset", "Delete Preset"],
        },
        "Preset 5": {
            "Type": "Preset",
            "Options": ["Create Preset", "Edit Preset", "Delete Preset"],
        }
    },
    "Scrims": {
        "Caster": {
            "Type": "Role",
            "Options": ["Enable", "Disable", "Change Role"],
        }
    }
}
