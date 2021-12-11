#!/usr/bin/env python3
import re
import json
import requests as rq
import mysql.connector
from mysql.connector.utils import NUMERIC_TYPES
from types import NoneType
from time import sleep

# set to run without saving data to the database
commit_to_database = False
# set to run in test mode
test_mode = True
# set to print debug messages
debug = False
ext_debug = False

# default database config
defDataBaseConfig = {"api":"","database":{"host":"","port":3306,"user":"","password":"","database":""},"table":"","dbUnique":"","columns":{"DB":{"api":"API","type":"(bool,int,float,str,json)"}},"delay":2}

# create the dbScrapper class
class dbScrapper():
    # initialize class instance
    def __init__(self, config, delay=False, encode=False):
        # load configuration parameters from json file
        try:
            with open(config, 'r') as file:
                conf = json.loads(file.read())
        except:
            print("Database config not found!")
            with open(config, "w") as file:
                file.write(json.dumps(defDataBaseConfig, indent=4))
            exit()
        # initialize database connection and create a MySQLConnection object
        counter = 0
        while counter < 3:
            try:
                self.db = mysql.connector.connect(
                    host = conf["database"]["host"],
                    port = conf["database"]["port"],
                    user = conf["database"]["user"],
                    password = conf["database"]["password"],
                    database = conf["database"]["database"]
                )
                break
            except:
                print("Error while connecting to database! Trying again...")
                counter += 1
                sleep(5)
        else:
            print("Couldn't connect to database! Terminating program...")
            raise Exception("Couldn't connect to database!")
        # self.db cursor
        self.dbCursor = self.db.cursor(dictionary=True)
        # api url
        self.api = conf["api"]
        # database table name
        self.dbTable = conf["table"]
        # database unique column
        self.uniqueId = conf["dbUnique"]
        # (database) : (api) dictionary
        self.dbCols = conf["columns"]
        # keys only from self.dbCols
        self.dbKeys = list(self.dbCols.keys())
        # cycle delay
        if delay:
            print(f"* dbScrapper initialized with custom delay of {delay}")
            self.delay = delay
        else:
            self.delay = conf["delay"]
        # select if internally encode data
        self.encodeData = encode
        # (api) : (database) dictionary
        self.apiCols = {}
        for k in self.dbKeys:
            self.apiCols[self.dbCols[k]["api"]] = {"db":k, "type":self.dbCols[k]["type"]}
        # keys only from self.apiCols
        self.apiKeys = list(conf["columns"].keys())
        # columns in database table
        self.dbCursor.execute(f"DESCRIBE `{conf['table']}`")
        self.tableCols = []
        for c in list(self.dbCursor.fetchall()):
            self.tableCols.append(c["Field"])
        print("New dbScrapper object created!")
        return

    # fetch data info from self.api
    # returns 'data' (json formatted data) if it found a result, and False if it did not found anything
    def dataGet(self, fetch):
        # debug
        if test_mode and debug: print("dataGet()")

        data = rq.get(f"{self.api}/{fetch}")
        sleep(self.delay)
        if data.status_code in [200, 201]:
            print(f"Entry with Id:{fetch} found!")
            data = data.json()
            if type(data) is dict:
                for key in data.keys():
                    data[key] = "null" if data[key] == None else data[key]
                    if key in self.apiKeys and data[key] != "null":
                        match self.apiCols[key]["type"]:
                            case "bool":
                                data[key] = int(data[key])
                            case "int":
                                data[key] = int(data[key])
                            case "float":
                                data[key] = float(data[key])
                            case "str":
                                data[key] = str(data[key].replace("\\u00a0", " ").replace("\"", "\\\"").replace("'", "\\'"))
                            case "json":
                                data[key] = json.loads(json.dumps(data[key]).replace("\\u00a0", " "))

                # debug
                if test_mode:
                    with open("dataGet.json", "w") as f:
                        f.write(json.dumps(data, indent=4))

                # debug
                if test_mode and debug and ext_debug: print(data)

                # debug
                if test_mode and debug: print("dataGet() > Returning")
                return data
            else:
                print("Data is not a dictionary!")
                raise Exception("Data is not a dictionary!")
        elif data.status_code == 404:
            print(f"Entry with Id:{fetch} not found!")
        elif data.status_code in [400, 401, 403, 405, 409]:
            print("Invalid request!")
        elif data.status_code in [500, 503]:
            print("Service not available right now!")

            # debug
            if test_mode and debug: print("dataGet() > Returning")
            return None
        else:
            print("Unknown status code: " + data.status_code)
        
        # debug
        if test_mode and debug: print("dataGet() > Returning")
        return False
    
    # check if data (dictionary parsed from API request) is already in the database table (self.dbTable) and if data values are the same (shows each column)
    # returns result (data exists on database or not), different (data in database is different than the one being checked), query(returns the database query)
    def dataExists(self, data):
        # debug
        if test_mode and debug: print("dataExists()")

        print("Checking data existance within the database...")
        self.dbCursor.execute(f"SELECT * FROM `{self.dbTable}` WHERE `{self.uniqueId}`={data[self.dbCols[self.uniqueId]['api']]}", )
        query = self.dbCursor.fetchall()
        # return False if there is no result
        if not query:
            # debug
            if test_mode and debug: print("dataExists() > Returning")
            return False

        row = query[0]

        # debug
        if test_mode and debug and ext_debug: print(row)

        for key in row.keys():
            convert = self.apiCols[self.dbCols[key]["api"]]["type"]
            row[key] = "null" if row[key] == None else row[key]
            if row[key] != "null":
                match convert:
                    case "bool":
                        row[key] = int(row[key])
                    case "int":
                        row[key] = int(row[key])
                    case "float":
                        row[key] = float(row[key])
                    case "str":
                        row[key] = str(row[key].replace("\\u00a0", " ").replace("\"", "\\\"").replace("'", "\\'"))
                    case "json":
                        row[key] = json.loads(row[key])

        # debug
        if test_mode:
            with open("dataExists.json", "w") as f:
                f.write(json.dumps(row, indent=4))
        
        row = json.loads(json.dumps(row))

        result = False
        different = False
        # compares data from database and parsed
        print(f"\t├─Same '{self.uniqueId}' found in database!")

        for key,value in row.items():
            if key in data.keys():
                api_key = self.dbCols[key]["api"]
                data[api_key] = "null" if data[api_key] == None else data[api_key]
                if value == data[api_key]:
                    result = True
                    col_check = True
                else:
                    different = True
                    col_check = False
                print(f"\t│\t├─Same {key}: {col_check}")
                if test_mode and debug: print(f"\t│\t│\t└─ {type(value)} : {type(data[api_key])}")

                # debug
                if test_mode and debug and ext_debug: print(value, "|", data[api_key])

        print(f"\t└─Data exists in database:\n\t\t├─result:{result}\n\t\t└─different:{different}")
        
        # debug
        if test_mode and debug: print("dataExists() > Returning")
        return [result,different,row]
    
    # insert or update an anime entry in the database and finally check if it is found int he database
    # prints id, mal_id and title if the entry was added and found in the database
    def dataInsert(self, data):
        # debug
        if test_mode and debug: print("dataInsert()")

        dataKeys = list(data.keys())
        check = self.dataExists(data)
        if not check:
            print("Entry not found in the database! Creating it...")
            dbEntry = f"INSERT INTO `{self.dbTable}` VALUES ("
            for c in self.tableCols:
                k = self.dbCols[c]["api"]
                if k in dataKeys and k != None:
                    if data[k] == "null":
                        col_entry = data[k]
                    else:
                        match self.dbCols[c]["type"]:
                            case "bool":
                                col_entry = data[k]
                            case "int":
                                col_entry = data[k]
                            case "float":
                                col_entry = data[k]
                            case "str":
                                col_entry = "\"%s\"" % data[k]
                            case "json":
                                col_entry = "\"%s\"" % json.dumps(data[k]).replace("\\", "\\\\").replace("\"", "\\\"")
                    dbEntry += str(col_entry)
                else:
                    dbEntry += "null"
                if c != self.apiKeys[-1]: dbEntry += ","
                
                # debug
                if test_mode and debug: dbEntry += "\n\t"

            dbEntry += ");"

            # debug
            if test_mode and debug and ext_debug: print(dbEntry)

            self.dbCursor.execute(dbEntry)
            print("\t├─Checking data added succesfully... ")
        elif check[0] and check[1]:
            print("Entry was found with different values! Updating it...")
            dbUpdate = f"UPDATE `{self.dbTable}` SET "
            for c in self.tableCols:
                k = self.dbCols[c]["api"]
                if k in dataKeys and k != None:
                    if data[k] == "null":
                        col_entry = data[k]
                    else:
                        match self.dbCols[c]["type"]:
                            case "bool":
                                col_entry = data[k]
                            case "int":
                                col_entry = data[k]
                            case "float":
                                col_entry = data[k]
                            case "str":
                                col_entry = "\"%s\"" % data[k]
                            case "json":
                                col_entry = "\"%s\"" % json.dumps(data[k]).replace("\\", "\\\\").replace("\"", "\\\"")
                    dbUpdate += f"`{c}`={str(col_entry)}"
                    if c != self.apiKeys[-1]: dbUpdate += ", "

                # debug
                if test_mode and debug: dbUpdate += "\n\t"

            dbUpdate += f" WHERE {self.uniqueId}={data[self.dbCols[self.uniqueId]['api']]};"
            
            # debug
            if test_mode and debug and ext_debug: print(dbUpdate)

            self.dbCursor.execute(dbUpdate)
            print("\t├─Checking data was updated succesfully... ")
        else:
            print("Entry was found in the database with no changes!")

            # debug
            if test_mode and debug: print("dataInsert() > Returning")
            return True
        
        # commit database changes if not on test mode
        if commit_to_database and not test_mode: self.db.commit()

        entry = self.dataExists(data)
        if not entry:
            print("Entry was not found in the database! Check the system.")

            # debug
            if test_mode and debug: exit()

            raise Exception("Entry was not found in the database! Check the system.")
        elif entry[0] and not entry[1]:
            print(f"Entry was found in the database!\n\t└─{self.uniqueId}: {entry[2][self.uniqueId]}\n")
            
            # debug
            if test_mode and debug: print("dataInsert() > Returning")
            return True
        elif entry[0] and entry[1]:
            print("Entry was found with different values! Check the system.")

            # debug
            if test_mode and debug: exit()

            raise Exception("Entry was found with different values! Check the system.")
        
        # debug
        if test_mode and debug: print("dataInsert() > Returning")
        return False
    
    # close the connection with the database
    def closeConnection(self):
        # debug
        if test_mode and debug: print("closeConnection()")

        self.db.close()

        # debug
        if test_mode and debug: print("closeConnection() > Returning")
        return

# run the next set of commands to execute it properly
#scrapper = dbScrapper(configFile)
#data = scrapper.dataGet(1)
#scrapper.dataInsert(data)
#scrapper.closeConnection()