#!/usr/bin/python3

from psychopy import visual, core, microphone
from collections import namedtuple
import sys
import os
import re
import yaml
from cerberus import Validator
import magic
mime = magic.Magic(mime=True)
import pprint
pp = pprint.PrettyPrinter(indent=4)
pprint = pp.pprint

# Data structures
Section = namedtuple('Section', ['name', "number", "path", "interval"])
MsgSource = namedtuple('MsgSource', ['path', 'mimeType', 'mimeSubtype', 'basename', 'interval', 'extension'])
Action = namedtuple('Action', ['msg', 'interval'])

configSchema = {  'sectionDir': {'type': 'string'}
                , 'outputDir': {'type': 'string'}
                , 'windowWidth': {'type': 'integer'}
                , 'windowHeight': {'type': 'integer'}
                , 'sectionTransition': {'type': 'integer'}
                , 'imageTransition': {'type': 'integer'}
}

def validateConfig(config, configSchema):
    validator = Validator()
    if validator.validate(config, configSchema) is False:
        print("\n\nSorry, you made a mistake in the configuration file.\nHope this will help:")
        print(validator.errors)
        exit(1)

def loadConfig(configPath):
    with open(configPath, 'r') as stream:
        try:
            return yaml.load(stream)
        except yaml.YAMLError as exc:
            print(exc)


def createOutputDir(outputDir, experimentName, num):
    experimentNameEnum = experimentName + "_" + str(num)
    experimentDirPath = os.path.join(outputDir, experimentNameEnum)
    try:
        os.mkdir(outputDir)
    except OSError as excp:
        # errno 17 --> file exists
        if excp.errno == 17:
            pass
        else:
            print(excp)
            exit(1)
    try:
        os.mkdir(experimentDirPath)
    except OSError as excp:
        if excp.errno == 17:
            num += 1
            experimentDirPath = createOutputDir(outputDir, experimentName, num)
        else:
            print(excp)
            exit(1)
    return experimentDirPath


def validateSectionDirName(sectionDirName):
    """Throw error if name doesn't match regexp pattern"""
    match =re.match(r"[0-9]{1,}[_][a-z0-9_-]{1,}[_][0-9]{1,}", sectionDirName)
    if match is None:
        raise ValueError("Section directory name doesn't conform the usage schema.")


def destructureSecionDirName(sectionDir):
    numberEnd = sectionDir.find("_")
    intervalStart = sectionDir.rfind("_")

    name = sectionDir[numberEnd + 1:intervalStart]
    number = sectionDir[:numberEnd]
    interval = sectionDir[intervalStart + 1:]

    return (name, number, interval)


def readSections(sectionDirPath):
    sectionDirNames = sorted(list(os.listdir(sectionDirPath)))
    sections = []
    for sectionDirName in sectionDirNames:
        validateSectionDirName(sectionDirName)
        name, number, interval = destructureSecionDirName(sectionDirName)
        path = os.path.join(sectionDirPath, sectionDirName)
        sections.append(Section(name, number, path, interval))
    return sections


def deduceMsgSourceData(section, msgSourceFileName):
    basename = msgSourceFileName[:msgSourceFileName.rfind(".")]
    extension = msgSourceFileName[msgSourceFileName.rfind(".") + 1:].lower()
    intervalStartPos = basename.rfind("_i_");
    interval = None
    if intervalStartPos != -1:
        intervalStr = basename[intervalStartPos + 3:]
        interval = float(intervalStr)
        print("\n\nInteral\n")
        print(interval)
    path = os.path.join(
        section.path,
        msgSourceFileName)
    mimeStr = mime.from_file(path)
    mimeType = mimeStr[:mimeStr.find("/")]
    mimeSubtype = mimeStr[mimeStr.find("/") + 1:]
    return MsgSource(path, mimeType, mimeSubtype, basename, interval, extension)


def validateSections(config, sections):
    """Validate section directory files by their MIME types and extensions"""
    for section in sections:
        for msgSourceFileName in os.listdir(section.path):
            msgSource = deduceMsgSourceData(section, msgSourceFileName)
            if not (msgSource.mimeType == "image"
                    or (msgSource.mimeType == "text" and(msgSource.extension == "yaml" or msgSource.extension == "yml"))):
                print('\nSection: {name} contains an incompatible file: {path}'
                      .format(name=section.name, path=msgSource.path))
                exit(1)


def createAction(msgSource):
    if msgSource.mimeType == "image":
        msg = visual.ImageStim(window, image=msgSource.path)
        if msgSource.interval is not None:
            interval = msgSource.interval
        else:
            interval = config["imageTransition"]
        return(Action(msg, interval))
    elif msgSource.mimeType == "text":
        with open(msgSource.path, 'r') as stream:
            try:
                content = yaml.load(stream)
                try:
                    if "msg" in content:
                        return(
                            Action(
                                visual.TextStim(
                                    window, text=content["msg"]["text"]
                                ),
                                content["msg"]["interval"]
                            )
                        )
                    elif "textList" in content:
                        actionList = []
                        for text in content["textList"]:
                            actionList.append(
                                Action(
                                    visual.TextStim(
                                        window, text=text
                                    ),
                                    content["textListProperties"]["interval"]
                                )
                            )
                        return actionList
                except KeyError as keyExc:
                    print(keyExc)
            except IOError as exc:
                print(exc)


def createActionSequance(config, window, sections):
    actionSequance = []
    for section in sections:
        msgSourceFiles = sorted(os.listdir(section.path))
        for msgSourceFileName in msgSourceFiles:
            msgSource = deduceMsgSourceData(section, msgSourceFileName)
            action = createAction(msgSource)
            if type(action) == list:
                actionSequance.extend(action)
            else:
                actionSequance.append(action)
    return actionSequance


def recordAudio(experimentDirPath):
    recordFile = os.path.join(experimentDirPath, "record")
    microphone.switchOn()
    mic = microphone.AudioCapture()
    mic.setFile(recordFile)


if __name__ == '__main__':
    try:
        config = loadConfig(sys.argv[1])
        experimentName = sys.argv[2]
    except IndexError:
        print("An argument is missing. you should start this app as:\n stein.py config.yml experiment-name")
        exit(1)
    validateConfig(config, configSchema)
    experimentDirPath = createOutputDir(config["outputDir"], experimentName, 1)
    sections = readSections(config["sectionDir"])
    validateSections(config, sections)
    window = visual.Window([config["windowWidth"], config["windowHeight"]])
    actionSequance = createActionSequance(config, window, sections)

    # recordAudio(experimentDirPath);
    for action in actionSequance:
        print(action)
        action.msg.draw()
        window.flip()
        core.wait(action.interval)
    window.close()
    core.quit()
