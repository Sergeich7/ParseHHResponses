
import configparser

cnf = configparser.ConfigParser()

"""
config.cnf["Login"]["usernsme"]
config.cnf["Login"]["password"]
config.cnf["Result"]["save_to"]
config.cnf["Result"]["SPREADSHEET_ID"]
config.cnf["Chrome"]["hide_chrome"]
config.cnf["Chrome"]["min_wait"]
config.cnf["Debug"]["debuging"]
config.cnf["Debug"]["first_num_resps"]



print(cnf["Login"]["usernsme"])
print(cnf["Login"]["password"])
print(cnf["Result"]["save_to"])
print(cnf["Result"]["SPREADSHEET_ID"])
print(cnf["Chrome"]["hide_chrome"])
print(cnf["Chrome"]["min_wait"])
print(cnf["Debug"]["debuging"])
print(cnf["Debug"]["first_num_resps"])
"""