import PySimpleGUI as PSG
# pylint complains when I get PySimpleGUIQt.InputCombo values via a 
# dictionary, so I switched to PySimpleGUI with which I get no such complaint.
# [PySimpleGUIQt is currently (December 5, 2018) in Alpha.]

import CheckPageLinks

WAYS_TO_RUN_CHECK_LINKS = ["Collect check_links arguments from GUI",
                           "Pass arguments directly to check_links",
                           "Pass wrong number of arguments to generate error"]

layout = [[PSG.Text("Choose how to test check_links:")],
          [PSG.Radio(WAYS_TO_RUN_CHECK_LINKS[0], "radio_group",
                     default=True, key="gui")],
          [PSG.Radio(WAYS_TO_RUN_CHECK_LINKS[1], "radio_group", key="pass")],
          [PSG.Radio(WAYS_TO_RUN_CHECK_LINKS[2], "radio_group", key="error")],
          [PSG.ReadFormButton("Submit")]]

window = PSG.Window("Test CheckPageLinks").Layout(layout)
dummy, value = window.Read()
window.Close()

if dummy is not None:
    if (value["gui"]):  # Collect check_links arguments from GUI
        CheckPageLinks.check_links([])
    elif (value["pass"]):  # Pass appropriate arguments
        DRIVERS = ["Chrome", "Firefox"]

        WEBPAGES = ["http://127.0.0.1:5000/", "http://127.0.0.1:5500/",
                    "https://www.russelljqa.site/"]

        layout = [
            [PSG.Text("WebDriver to use:", size=(20, 1), justification='right'),
             PSG.InputCombo(DRIVERS, size=(25, 1))],
            [PSG.Text("Web page (URL) to check:", size=(20, 1),
                      justification='right'),
             PSG.InputCombo(WEBPAGES, size=(25, 1), readonly=False)],
            [PSG.Text(" ", size=(20, 1), justification='right'),
             PSG.Checkbox("Show only errors", default=True)],
            [PSG.Text(" ", size=(20, 1), justification='right'),
             PSG.ReadFormButton("Submit")]
        ]

        window = PSG.Window("Choose arguments to test check_links with"
                            ).Layout(layout)
        dummy, (web_driver, webpage, only_print_errors) = window.Read()
        window.Close()

        if dummy is not None:  # window closed normally
            BASENAMES = ["lektor-server", "vscode-live-server", "russelljqa"]
            basename = BASENAMES[WEBPAGES.index(webpage)]

            CheckPageLinks.check_links(
                [web_driver, webpage, basename, only_print_errors])
    elif (value["error"]):  # Test using the wrong number of parameters
        CheckPageLinks.check_links(["1"])
