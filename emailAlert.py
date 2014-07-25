"""
SecTool

Send the output from the plugins in an email alert to the user
who triggered the job.

23/07/2014
"""

# https://docs.python.org/2/library/email-examples.html

import json
from email.mime.text import MIMEText
from subprocess import Popen, PIPE

###############################################################################
# Members
###############################################################################

SENDMAIL = "/usr/sbin/sendmail"
FROM_ADDRESS = "noreply@digital.cabinet-office.gov.uk"

###############################################################################
# Class
###############################################################################


class Email:
    def __init__(self, pluginName = "Wapiti", jsonOutputFileName = "wapitiOutput.json", usersEmailAddress = "peter.mcnerny@digital.cabinet-office.gov.uk", targetUrl = "http://localhost:3000"):
        self.pluginName = pluginName
        self.jsonOutputFileName = jsonOutputFileName
        self.usersEmailAddress = usersEmailAddress
        self.targetUrl = targetUrl

    ###############################################################################
    # Functions
    ###############################################################################

    def parseWapitiOutput(self, json_data):
        # infos, vulnerabilities, classifications, anomalies

        # output is what will be displayed in the email
        title = "Summary"
        output = "{0}\n{1}\n\n**Category**\t\t\t\t**Number of Vulnerabilities Found**\n".format(title, '='*len(title))

        data = json.loads(json_data)

        noOfVulns = 0  # total number of vulnerabilities wapiti found

        # SUMMARY: the first part of the output is a summary of the number of
        # vulnerabilities found for each category of vulnerability
        dictOfVulns = {}

        # maintain count of vulns and append the parsed vuln data to the output
        for k, v in data['vulnerabilities'].items():
            noOfVulns += len(v)

            if len(v) != 0:
                if v not in dictOfVulns.items():
                    dictOfVulns[k] = len(v)

            # TODO: nicely format output for email (console will look bad)
            # set an appropriate number of tabs for tidy output
            tabs = "\t\t\t\t"
            if len(k) > 15:
                tabs = "\t\t\t"
            if "Backup" in k:
                tabs = "\t\t\t\t"
            if "Cross" in k:
                tabs = "\t\t\t"
            if "Potentially" in k:
                tabs = "\t\t"

            output += "\n* {0}{1}{2}\n".format(k, tabs, len(v))

        # ANOMALIES & VULNERABILITIES: the next part of the output describes
        # an identified attack, its location, the HTTP request and the cURL
        # command line command used to find the vuln
        title = "Detailed Vulnerability Information"
        output += "\n\n{0}\n".format(title)
        output += '='*len(title)

        for vuln in dictOfVulns:
            output += "\n\n{0}\n{1}".format(vuln, '-'*len(vuln))
            output += "\n**Description**\n\t"

            for k, v in data['classifications'].items():
                if k == vuln:
                    output += "{0}\n\n\n".format(v['desc'])

                    for key, val in data['vulnerabilities'].items():
                        if key == vuln:
                            counter = 1
                            for listItem in val:
                                if vuln == "Internal Server Error":
                                    output += "**[{0} of {1}] Vulnerability found in {2}**\n\n".format(
                                        counter, dictOfVulns[vuln], listItem['path'])
                                else:
                                    output += "**[{0} of {1}] Anomaly found in {2}**\n\n".format(
                                        counter, dictOfVulns[vuln], listItem['path'])

                                output += "**Description**\n\t{0}\n".format(listItem['info'])
                                output += "\n**HTTP Request**\n\t{0}\n".format(listItem['http_request'])
                                output += "**cURL command line**\n\t{0}\n\n".format(listItem['curl_command'])
                                counter += 1

                    output += "**Solutions**\n\t{0}".format(v['sol'])
                    output += "\n\n**References**\n\t"
                    for element in v['ref'].items():
                        output += "{0}\n\t".format(element)

        #print(output)  # TODO: DEBUG - remove

        return output, noOfVulns

    def getOutputFromJsonObject(self, json_data):
        #json_data = open(self.jsonOutputFileName).read()
        json_data = open(self.jsonOutputFileName, 'r+').read()


        # handling of output needs to be specific to each plugin
        parsedData = None
        if self.pluginName.lower() == "wapiti":
            parsedData = self.parseWapitiOutput(json_data)

        return parsedData[0], parsedData[1]  # output, numOfErrors

    def createEmail(self):
        # create the contents of the email
        output = self.getOutputFromJsonObject(self)

        message = MIMEText(output[0])

        # how many issues the tool has found
        numOfErrors = output[1]
        issues = "Issues Found"
        if numOfErrors == 1:
            issues = "Issue Found"

        # add addressing to the email
        message['Subject'] = "SecTool Results: {0} {1} [{2}]".format(
            numOfErrors, issues, self.pluginName)
        message['from'] = FROM_ADDRESS
        message['to'] = self.usersEmailAddress  # email address of user who ran the tool
        return message

    def sendEmail(self, message):
        p = Popen([SENDMAIL, "-t"], stdin=PIPE)
        p.communicate(bytes(message.as_string(), 'utf-8'))
        if p.returncode != 0:
            raise Exception("Oops")
    def triggerEmailAlert(self):
        emailMessage = self.createEmail()
        self.sendEmail(emailMessage)


###############################################################################
# Testing
###############################################################################
if __name__ == '__main__':
    e = Email()
    msg = e.createEmail()
    e.sendEmail(msg)




