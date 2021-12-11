#!/usr/bin/env python3
from dbScrapperV5 import dbScrapper
from datetime import date
from os import mkdir
import json
import argparse
import logging

# create config folder
try:
    mkdir("config/")
except:
    pass

# create logs folder
try:
    mkdir("logs/")
except:
    pass

# configure logging
logging.basicConfig(filename=f"logs/CharacterScrapper({date.today()}).log", \
    format="%(asctime)s (%(levelname)s): %(message)s", \
        datefmt='%d/%m/%Y (%a) %H:%M:%S >> ', level=logging.DEBUG)

# define console parameters to be parsed
parser = argparse.ArgumentParser()
parser.add_argument("-s", "--start", help="Specify an Id to start from", type=int)
parser.add_argument("-c", "--cycle", help="Specify a cycle delay", type=float)
args = parser.parse_args()

# files paths
statusFile = "config/character-status.json"
dbConfigFile = "config/scrapper-conf-V5-character.json"

# if parameters parsed then define variables, if not read status file
if args.start:
    finished = False
    lastId = args.start
    logging.info(f"Got lastId = {lastId} from parsed argument!")
    print(f"-> Got lastId = {lastId} from parsed argument!")
else:
    # load status file to check for previus program status
    while True:
        try:
            with open(statusFile, "r") as file:
                logging.info("Status file opened")
                print("Status file opened!")
                status = file.read()
                # if file content is not spaces and its length is grater than 0 then read content
                if not status.isspace() and len(status) > 0:
                    status = json.loads(status)
                    statusKeys = status.keys()
                    # if the needed keys are within the content then continue
                    if "finished" in statusKeys and "lastId" in statusKeys and "maxId" in statusKeys:
                        # if the finished parameter is False then continue
                        if not status["finished"]:
                            finished = status["finished"]
                            lastId = status["lastId"]
                            maxId = status["maxId"]
                            logging.info(f"Finished: {finished}, LastId: {lastId}, Max Id: {maxId}")
                            #print(finished, lastId)
                            break
                # if something fails raise an error
                raise FileNotFoundError
        # if the FileNotFound is raised then create a fresh status file with default parameters
        except FileNotFoundError:
            logging.info("Status file not found or unusable")
            print("Status file not found or unusable!")
            with open(statusFile, "w") as file:
                logging.info("Creating status file")
                print("Creating status file...")
                file.write(json.dumps({"finished":False, "lastId":0, "maxId":50000}, indent=4))

# create a dbScrapper object
logging.debug("Creating dbScrapper object")
characterScrapper = dbScrapper(dbConfigFile, args.cycle)

# if finished is false then continue
if not finished:
    logging.info(f"Scrapping character data from Id: {lastId} to Id: {maxId}")
    print(f"Scrapping character data from Id: {lastId} to Id: {maxId}")
    try:
        # scrap data from lastId to maxId
        for x in range(lastId, maxId):
            # bucle until characterData gets valid data to evaluate
            while True:
                logging.info(f"Getting Id: {x} data")
                characterData = characterScrapper.dataGet(x)
                # if characterData has valid data, insert it into the database and update the status file
                if characterData:
                    logging.debug("Valid data")
                    insertStatus = characterScrapper.dataInsert(characterData)
                    if insertStatus:
                        logging.debug("Data inserted succesfully into database")
                    else:
                        logging.error("Error while inserting data into database!")
                    break
                elif characterData is False:
                    logging.debug("Invalid data")
                    break
            # update status
            with open(statusFile, "w") as status:
                logging.info("Updating status file")
                status.write(json.dumps({"finished":False, "lastId":x, "maxId":maxId}, indent=4))
    except Exception as e:
        error = "An error occurred while running the program!\nError: "+str(e)+"\nTerminating program..."
        logging.error(error)
        print(error)
        exit()
    # when the maxId has been reached, update the finished parameter to True within the status file
    with open(statusFile, "w") as status:
        logging.info("Update status file to finished")
        status.write(json.dumps({"finished":True, "lastId":x, "maxId":maxId}, indent=4))

# close the database connection when everything has finished
logging.info("Closing database connection")
characterScrapper.closeConnection()

# print finished message
logging.info("Scrapping is finished!")
print("Scrapping is finished!")