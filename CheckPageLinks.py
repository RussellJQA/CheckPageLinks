import sys
import time
import json

import PySimpleGUIQt as PSG
import requests
from selenium import webdriver

VALID_STATUS_CODES = [100, 101, 102, 103, 122, 200, 201, 202, 203, 204, 205,
                      206, 207, 208, 226, 300, 301, 302, 303, 304, 305, 306, 307, 308, 400, 401,
                      402, 403, 404, 405, 406, 407, 408, 409, 410, 411, 412, 413, 414, 415, 416,
                      417, 418, 421, 422, 423, 424, 425, 426, 428, 429, 431, 444, 449, 450, 451,
                      499, 500, 501, 502, 503, 504, 505, 506, 507, 509, 510, 511]
# List of valid numeric status codes dervied from the codes included in:
#   https://github.com/requests/requests/blob/master/requests/status_codes.py


def collect_check_links_arguments_from_gui():
    """ Uses PySimpleGUI interface to collect parameters for check_links()

    Returns:
        web_driver -- which WebDriver to use: "Chrome" or "Firefox"
        webpage -- the Web page (URL) containing links to be checked
        basename -- the basename for the results file
        only_print_errors -- only print links which fail checking (boolean)
    """

    DRIVERS = ["Chrome", "Firefox"]  # List of WebDrivers to choose from
    WEBPAGES = ["http://127.0.0.1:5000/", "http://127.0.0.1:5500/",
                "https://www.russelljqa.site/"]
    # List of Web pages (URLs) to choose from
    BASENAMES = ["lektor-server", "vscode-live-server", "russelljqa"]
    # Corresponding (to webpages) list of basenames to choose from

    layout = [
        [PSG.Text("WebDriver to use:", size=(20, 1), justification='right'),
            PSG.InputCombo(DRIVERS, size=(25, 1))],
        [PSG.Text("Web page (URL) to check:", size=(20, 1),
                  justification='right'),
            PSG.InputCombo(WEBPAGES, size=(25, 1), readonly=False, 
                tooltip="Editable")],
        [PSG.Text("Basename for results file:", size=(20, 1),
                  justification='right'),
            PSG.InputCombo(BASENAMES, size=(25, 1), readonly=False,
                tooltip="Editable")],
        [PSG.Text(" ", size=(20, 1), justification='right'),
            PSG.Checkbox("Show only errors", default=True)],
        [PSG.Text(" ", size=(20, 1), justification='right'),
            PSG.ReadFormButton("Submit")]
    ]

    window = PSG.Window("Check Page Links").Layout(layout)
    dummy, (web_driver, webpage, basename, only_print_errors) = \
        window.Read()
    window.Close()

    if dummy is None:  # window closed abnormally
        return None
    else:
        return (web_driver, webpage, basename, only_print_errors)


def formatted_status(status_code):
    """ If status code is a valid numeric code, append a common name to it

    Arguments:
        status_code -- status code returned from requests

    Returns:
        status -- string version of that code, with (if it's a valid numeric 
            status code) its first common name (from requests) appended
    """

    status = str(status_code)
    if status_code in VALID_STATUS_CODES:

        str_code = requests.status_codes._codes[status_code][0]
        # Convert the valid numeric code to its first common name, as in:
        #   404 to ('not_found', '-o-') to "not_found" code to tuple of
        #   429 to ('too_many_requests', 'too_many') to "too_many_requests"

        status += (' (' + str_code.replace('_', ' ').title() + ')')

    return status


def check_link(href, link_text):
    """ User requests library to check the link for errors

    Arguments:
        href -- href (URL) of the link to be checked
        link_text -- link text of the link to be checked

    Returns:
        status -- formatted version of status returned by requests
        error_found -- whether 1 or more errors were found
        redirection_info -- For redirected URLs, contains info on redirection
    """

    error_found = False
    redirection_info = ""

    try:
        response = requests.get(href)
        status = response.status_code
        error_found = (status != 200)
        if response.history:
            # Handle redirections (codes 301, 302, etc.)
            redirection_info = ("\n" + " "*4 + "Text: \"" + link_text +
                                "\" was redirected from:")
            for resp in response.history:
                if resp.status_code != 200:
                    error_found = True
                redirection_info += ("\n" + " "*8 +
                                     formatted_status(resp.status_code) + " \"" + resp.url + "\" to:")
            redirection_info += ("\n" + " "*8 +
                                 formatted_status(status) + " \"" +
                                 response.url + "\"\n")
    except Exception as e:
        status = "\n" + str(e) + "\n"
        error_found = True

    return (status, error_found, redirection_info)


def check_links(args):
    """Check the links on the specified Web page, and report the results

    Arguments passed via sys.argv[1:] (if len(args)):
        args[0] -- which WebDriver to use: "Chrome" or "Firefox"
        args[1] -- the Web page containing links to be checked
        args[2] -- the basename for the results file
        args[3] -- only print links which fail checking (boolean)
    """

    if len(args) == 0:
        # No arguments were passed via sys.argv[1:]
        new_args = collect_check_links_arguments_from_gui()
        if new_args is None:
            msg = "Argument collecting dialog was cancelled"
            PSG.PopupCancel("", msg)
            raise SystemExit("\n" + msg)
        else:
            (web_driver, webpage, basename, only_print_errors) = new_args
    elif len(args) == 4: # 4 arguments were passed via sys.argv[1:]
        (web_driver, webpage, basename, only_print_errors) = \
            (args[0], args[1], args[2], args[3])
        # So, use them
    else:
        msg = "An incorrect number of arguments was specified." + \
            "\nPlease specify exactly 4 parameters or none."
        PSG.PopupError("", msg)
        raise SystemExit("\nCancelling:\n" + msg)           

    driver = None
    if web_driver == "Chrome":
        driver = webdriver.Chrome()
    elif web_driver == "Firefox":
        driver = webdriver.Firefox()

    print("\nWebDriver to use: {}".format(web_driver))
    print("Web page (URL) to check: \"{}\"".format(webpage))
    print("Basename for the results file: \"{}\"".format(basename))
    print("Show errors only: {}\n".format(only_print_errors))

    if driver:

        driver.get(webpage)

        link_elements = driver.find_elements_by_tag_name('a')
        time.sleep(1)

        bad_links = 0
        link_statuses = []

        for count, link_element in enumerate(link_elements, start=1):
            href = link_element.get_attribute('href')
            link_text = link_element.text
            (status, error_found, redirection_info) = check_link(href,
                                                                 link_text)
            bad_links += (1 if error_found else 0)

            link_status = "Link: " + str(count) + ","
            if len(redirection_info):
                link_status += redirection_info
            else:
                link_status += " Text: \"{}\", URL: \"{}\", status: {}".format(
                    link_text, href, status)
            link_statuses.append(link_status)
            if error_found or (not only_print_errors):
                print(link_status)

        with open((basename + ".json"), 'w') as json_file:
            json.dump(link_statuses, json_file)

        print("\n{} bad links found".format(bad_links if bad_links else "No"))

        driver.quit()

if __name__ == "__main__":
    check_links(sys.argv[1:])
    sys.exit(0)
