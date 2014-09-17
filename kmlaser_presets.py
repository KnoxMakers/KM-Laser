_pcolors = {
    "#ff0000": "cut",
    "#00ffff": "engrave-light",
    "#0000ff": "engrave-heavy",
}

_presets = {
    "3mm-wood": {
        "engrave-light": [10000,400,0.13],
        "engrave-heavy": [10000,400,0.14],
        "cut": [10000,400,0.4],
    },
    "6mm-wood": {
        "engrave-light": [10000,400,0.13],
        "engrave-heavy": [10000,400,0.14],
        "cut": [10000,400,0.6],    
    },
    "3mm-acrylic": {
        "engrave-light": [10000,1000,0.164],
        "engrave-heavy": [10000,400,0.152],
        "cut": [10000,400,0.4],            
    },
    "6mm-acrylic": {
        "engrave-light": [10000,1500,0.2],
        "engrave-heavy": [10000,1000,0.2],
        "cut": [10000,200,0.6],            
    },
    "paper": {
        "engrave-light": [1, 10000, 0.2], # Perforated
        "engrave-heavy": [10000,1500,0.128],
        "cut": [10000, 500, 0.165]
    },
    "cardboard": {
        "engrave-light": [10000,400,0.13],
        "engrave-heavy": [10000,1000,0.14],
        "cut": [10000,1000,0.5]
    }
}
